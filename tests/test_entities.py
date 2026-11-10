"""Tests for APRS Weather Station sensors and device tracker entities."""

from types import MappingProxyType
from unittest.mock import MagicMock

import pytest

from custom_components.aprs_weather_station.const import CONF_CALLSIGN, DOMAIN
from custom_components.aprs_weather_station.data import APRSWSSensorData
from custom_components.aprs_weather_station.device_tracker import (
    APRSWSLocationSensor,
)
from custom_components.aprs_weather_station.device_tracker import (
    _find_subentry as tracker_find_subentry,
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
