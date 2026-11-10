"""Tests for APRS Weather Station sensors and device tracker entities."""

from types import MappingProxyType
from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

from custom_components.aprs_weather_station.const import (
    CONF_CALLSIGN,
    DOMAIN,
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
from custom_components.aprs_weather_station.sensor import (
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
    """Test device_tracker location update does not throw log format error (Item 7)."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "entry_123"
    coordinator.config_entry.domain = DOMAIN

    loc_data = APRSWSSensorData(
        timestamp=1700000000,
        callsign="W3ADO-1",
        type="location",
        value="38.9876,-76.5432",
    )

    tracker = APRSWSLocationSensor(data=loc_data, coordinator=coordinator)
    assert tracker.latitude == pytest.approx(38.9876)
    assert tracker.longitude == pytest.approx(-76.5432)

    # Simulate coordinator update with new coordinates
    new_loc_data = APRSWSSensorData(
        timestamp=1700000060,
        callsign="W3ADO-1",
        type="location",
        value="39.1234,-76.9876",
    )
    coordinator.data = [new_loc_data]
    tracker.async_write_ha_state = MagicMock()

    # This calls LOGGER.debug which had the 3-placeholder 1-arg bug
    tracker._handle_coordinator_update()

    assert tracker.latitude == pytest.approx(39.1234)
    assert tracker.longitude == pytest.approx(-76.9876)
    tracker.async_write_ha_state.assert_called_once()


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
