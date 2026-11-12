"""Tests for APRS Weather Station sensors and device tracker entities."""

from types import MappingProxyType
from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

from custom_components.aprs_weather_station.aprs_parser import APRSPacketParser
from custom_components.aprs_weather_station.const import (
    CONF_CALLSIGN,
    DOMAIN,
    SENSOR_DESCRIPTIONS,
    SENSOR_DESCRIPTIONS_MAP,
    SENSOR_TYPE_TO_SENSOR_DEVICE_CLASS,
    SENSOR_TYPE_TO_SENSOR_STATE_CLASS,
)
from custom_components.aprs_weather_station.data import APRSWSSensorData
from custom_components.aprs_weather_station.device_tracker import (
    APRSWSLocationSensor,
)
from custom_components.aprs_weather_station.device_tracker import (
    _find_subentry as tracker_find_subentry,
)
from custom_components.aprs_weather_station.entity import (
    find_sensor_data,
    find_subentry,
)
from custom_components.aprs_weather_station.sensor import (
    APRSWSPacketReceivedSensor,
    APRSWSSensor,
)
from custom_components.aprs_weather_station.sensor import (
    _find_subentry as sensor_find_subentry,
)


def test_find_subentry_case_insensitive() -> None:
    """Test _find_subentry matches callsigns case-insensitively (Item 10)."""
    subentry = MagicMock()
    subentry.data = {CONF_CALLSIGN: "W3ADO-1"}
    subentries = MappingProxyType({"s1": subentry})

    # Exact case
    assert sensor_find_subentry(subentries, "W3ADO-1") is subentry
    assert tracker_find_subentry(subentries, "W3ADO-1") is subentry

    # Lowercase
    assert sensor_find_subentry(subentries, "w3ado-1") is subentry
    assert tracker_find_subentry(subentries, "w3ado-1") is subentry

    # Non-matching
    assert sensor_find_subentry(subentries, "N0CALL") is None
    assert tracker_find_subentry(subentries, "N0CALL") is None


def test_find_sensor_data_helper() -> None:
    """Test find_sensor_data shared helper in entity.py (Item 21)."""
    s1 = APRSWSSensorData(
        timestamp=100, callsign="W3ADO-1", type="temperature", value=20
    )
    s2 = APRSWSSensorData(timestamp=100, callsign="W3ADO-1", type="humidity", value=50)

    assert find_sensor_data([s1, s2], "W3ADO-1_temperature") is s1
    assert find_sensor_data([s1, s2], "W3ADO-1_humidity") is s2
    assert find_sensor_data([s1, s2], "W3ADO-1_wind_speed") is None

    subentry = MagicMock()
    subentry.data = {CONF_CALLSIGN: "W3ADO-1"}
    assert find_subentry(MappingProxyType({"s1": subentry}), "w3ado-1") is subentry


def test_is_connected_sensor_unique_id_and_device_info() -> None:
    """Test is_connected unique_id and device_info scoped to entry_id (Item 11)."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "entry_123"
    coordinator.config_entry.domain = DOMAIN
    coordinator.config_entry.title = "N0CALL"

    sensor_data = APRSWSSensorData(
        timestamp=1700000000,
        callsign="APRS-IS",
        type="is_connected",
        value=True,
    )

    sensor = APRSWSSensor(data=sensor_data, coordinator=coordinator)

    # Unique id must be scoped with entry_id to avoid collision across multiple accounts
    assert sensor.unique_id == "entry_123_APRS-IS_is_connected"
    # Device info identifier must be scoped to entry_id
    assert sensor.device_info["identifiers"] == {(DOMAIN, "entry_123")}
    assert "APRS-IS (N0CALL)" in sensor.device_info["name"]
    # ENUM sensor maps boolean to option string
    assert sensor.native_value == "connected"

    sensor_disconnected = APRSWSSensor(
        data=APRSWSSensorData(
            timestamp=1700000000,
            callsign="APRS-IS",
            type="is_connected",
            value=False,
        ),
        coordinator=coordinator,
    )
    assert sensor_disconnected.native_value == "disconnected"


def test_station_sensor_unique_id_and_device_info() -> None:
    """Test station sensor unique_id and device_info scoped to station callsign."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "entry_123"
    coordinator.config_entry.domain = DOMAIN

    sensor_data = APRSWSSensorData(
        timestamp=1700000000,
        callsign="W3ADO-1",
        type="temperature",
        value=22.0,
    )

    sensor = APRSWSSensor(data=sensor_data, coordinator=coordinator)

    assert sensor.unique_id == "W3ADO-1_temperature"
    assert sensor.device_info["identifiers"] == {(DOMAIN, "W3ADO-1")}
    assert sensor.device_info["name"] == "W3ADO-1"


def test_location_sensor_logging_and_update() -> None:
    """Test device_tracker handles tuple coordinates and legacy str (Items 7, 22)."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "entry_123"
    coordinator.config_entry.domain = DOMAIN

    # Initial data with typed tuple (Item 22)
    loc_data = APRSWSSensorData(
        timestamp=1700000000,
        callsign="W3ADO-1",
        type="location",
        value=(38.9876, -76.5432),
    )

    tracker = APRSWSLocationSensor(data=loc_data, coordinator=coordinator)
    assert tracker.latitude == pytest.approx(38.9876)
    assert tracker.longitude == pytest.approx(-76.5432)

    # Coordinator update with new tuple coordinates
    new_loc_data = APRSWSSensorData(
        timestamp=1700000060,
        callsign="W3ADO-1",
        type="location",
        value=(39.1234, -76.9876),
    )
    coordinator.data = {new_loc_data.key: new_loc_data}
    tracker.async_write_ha_state = MagicMock()

    tracker._handle_coordinator_update()

    assert tracker.latitude == pytest.approx(39.1234)
    assert tracker.longitude == pytest.approx(-76.9876)
    tracker.async_write_ha_state.assert_called_once()

    # Legacy string coordinate update
    legacy_data = APRSWSSensorData(
        timestamp=1700000120,
        callsign="W3ADO-1",
        type="location",
        value="40.0,-75.0",
    )
    coordinator.data = {legacy_data.key: legacy_data}
    tracker._handle_coordinator_update()
    assert tracker.latitude == pytest.approx(40.0)
    assert tracker.longitude == pytest.approx(-75.0)


def test_parser_extracts_location_tuple() -> None:
    """Test APRSPacketParser outputs location as (lat, lon) tuple (Item 22)."""
    packet = {
        "from": "W3ADO-1",
        "timestamp": 1700000000,
        "latitude": 38.9876,
        "longitude": -76.5432,
    }
    sensors = APRSPacketParser().parse(packet)
    loc = next(s for s in sensors if s.type == "location")
    assert loc.value == (38.9876, -76.5432)


def test_wind_direction_device_and_state_class() -> None:
    """Test wind_direction sensor uses WIND_DIRECTION and MEASUREMENT_ANGLE."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "entry_123"
    coordinator.config_entry.domain = DOMAIN

    sensor_data = APRSWSSensorData(
        timestamp=1700000000,
        callsign="W3ADO-1",
        type="wind_direction",
        value=180,
    )

    sensor = APRSWSSensor(data=sensor_data, coordinator=coordinator)
    assert sensor.device_class == SensorDeviceClass.WIND_DIRECTION
    assert sensor.state_class == SensorStateClass.MEASUREMENT_ANGLE
    assert (
        SENSOR_TYPE_TO_SENSOR_DEVICE_CLASS["wind_direction"]
        == SensorDeviceClass.WIND_DIRECTION
    )
    assert (
        SENSOR_TYPE_TO_SENSOR_STATE_CLASS["wind_direction"]
        == SensorStateClass.MEASUREMENT_ANGLE
    )


def test_sensor_descriptions_structure() -> None:
    """Test SENSOR_DESCRIPTIONS tuple and SENSOR_DESCRIPTIONS_MAP (Item 19)."""
    assert len(SENSOR_DESCRIPTIONS) >= 11
    assert "temperature" in SENSOR_DESCRIPTIONS_MAP
    assert "wind_speed" in SENSOR_DESCRIPTIONS_MAP
    assert "timestamp" in SENSOR_DESCRIPTIONS_MAP
    assert "is_connected" in SENSOR_DESCRIPTIONS_MAP

    temp_desc = SENSOR_DESCRIPTIONS_MAP["temperature"]
    assert temp_desc.device_class == SensorDeviceClass.TEMPERATURE
    assert temp_desc.state_class == SensorStateClass.MEASUREMENT

    # Item 8: timestamp must have TIMESTAMP device class and NO state class
    ts_desc = SENSOR_DESCRIPTIONS_MAP["timestamp"]
    assert ts_desc.device_class == SensorDeviceClass.TIMESTAMP
    assert ts_desc.state_class is None

    # Item 8: is_connected must have ENUM device class and options defined
    conn_desc = SENSOR_DESCRIPTIONS_MAP["is_connected"]
    assert conn_desc.device_class == SensorDeviceClass.ENUM
    assert conn_desc.options == ["connected", "disconnected"]


def test_sensor_duplicate_timestamp_and_value_ignored() -> None:
    """Test APRSWSSensor ignores duplicates with identical timestamp and value."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "entry_123"
    coordinator.config_entry.domain = DOMAIN

    sensor_data = APRSWSSensorData(
        timestamp=1700000000,
        callsign="W3ADO-1",
        type="temperature",
        value=20.0,
    )
    sensor = APRSWSSensor(data=sensor_data, coordinator=coordinator)
    sensor.async_write_ha_state = MagicMock()

    # Case 1: Identical timestamp and value -> skip update
    dup_data = APRSWSSensorData(
        timestamp=1700000000,
        callsign="W3ADO-1",
        type="temperature",
        value=20.0,
    )
    coordinator.data = {dup_data.key: dup_data}
    sensor._handle_coordinator_update()
    sensor.async_write_ha_state.assert_not_called()

    # Case 2: Same timestamp, different value -> process update
    new_value_data = APRSWSSensorData(
        timestamp=1700000000,
        callsign="W3ADO-1",
        type="temperature",
        value=21.5,
    )
    coordinator.data = {new_value_data.key: new_value_data}
    sensor._handle_coordinator_update()
    sensor.async_write_ha_state.assert_called_once()
    assert sensor.native_value == 21.5

    # Case 3: Different timestamp, same value -> process update
    sensor.async_write_ha_state.reset_mock()
    new_ts_data = APRSWSSensorData(
        timestamp=1700000060,
        callsign="W3ADO-1",
        type="temperature",
        value=21.5,
    )
    coordinator.data = {new_ts_data.key: new_ts_data}
    sensor._handle_coordinator_update()
    sensor.async_write_ha_state.assert_called_once()
    assert sensor.data.timestamp == 1700000060


def test_location_sensor_duplicate_timestamp_and_value_ignored() -> None:
    """Test APRSWSLocationSensor ignores identical timestamp and value duplicates."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "entry_123"
    coordinator.config_entry.domain = DOMAIN

    loc_data = APRSWSSensorData(
        timestamp=1700000000,
        callsign="W3ADO-1",
        type="location",
        value=(38.9876, -76.5432),
    )
    tracker = APRSWSLocationSensor(data=loc_data, coordinator=coordinator)
    tracker.async_write_ha_state = MagicMock()

    # Case 1: Identical timestamp and value -> skip update
    dup_loc = APRSWSSensorData(
        timestamp=1700000000,
        callsign="W3ADO-1",
        type="location",
        value=(38.9876, -76.5432),
    )
    coordinator.data = {dup_loc.key: dup_loc}
    tracker._handle_coordinator_update()
    tracker.async_write_ha_state.assert_not_called()

    # Case 2: Same timestamp, different location value -> process update
    new_loc = APRSWSSensorData(
        timestamp=1700000000,
        callsign="W3ADO-1",
        type="location",
        value=(39.0000, -76.5000),
    )
    coordinator.data = {new_loc.key: new_loc}
    tracker._handle_coordinator_update()
    tracker.async_write_ha_state.assert_called_once()
    assert tracker.latitude == pytest.approx(39.0000)
    assert tracker.longitude == pytest.approx(-76.5000)


def test_packet_received_sensor_duplicate_handling() -> None:
    """Test packet received sensor skips duplicate refresh and increments on new."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "entry_123"
    coordinator.config_entry.domain = DOMAIN

    packet_data = APRSWSSensorData(
        timestamp=1700000000,
        callsign="W3ADO-1",
        type="packet_received",
        value=1,
    )
    sensor = APRSWSPacketReceivedSensor(data=packet_data, coordinator=coordinator)
    sensor.async_write_ha_state = MagicMock()
    assert sensor.native_value == 1

    # Coordinator refresh with the SAME object and timestamp -> skip
    coordinator.data = {packet_data.key: packet_data}
    sensor._handle_coordinator_update()
    sensor.async_write_ha_state.assert_not_called()
    assert sensor.native_value == 1

    # New packet arrives within same minute (different object, same ts) -> increment
    new_packet = APRSWSSensorData(
        timestamp=1700000000,
        callsign="W3ADO-1",
        type="packet_received",
        value=1,
    )
    coordinator.data = {new_packet.key: new_packet}
    sensor._handle_coordinator_update()
    sensor.async_write_ha_state.assert_called_once()
    assert sensor.native_value == 2

    # Refresh with that same new_packet object -> skip
    sensor.async_write_ha_state.reset_mock()
    sensor._handle_coordinator_update()
    sensor.async_write_ha_state.assert_not_called()
    assert sensor.native_value == 2
