"""Tests for the aprs_weather_station diagnostics platform."""

from unittest.mock import MagicMock

import pytest

from custom_components.aprs_weather_station.const import (
    CONF_CALLSIGN,
    CONF_YOUR_CALLSIGN,
    DOMAIN,
)
from custom_components.aprs_weather_station.data import APRSWSSensorData
from custom_components.aprs_weather_station.diagnostics import (
    async_get_config_entry_diagnostics,
)


@pytest.mark.asyncio
async def test_async_get_config_entry_diagnostics() -> None:
    """Test retrieving config entry diagnostics (Item 32)."""
    hass = MagicMock()

    mock_subentry = MagicMock()
    mock_subentry.subentry_id = "sub_1"
    mock_subentry.data = {CONF_CALLSIGN: "W3ADO-1"}

    mock_client = MagicMock()
    mock_client.is_connected.return_value = True
    mock_client.is_listening.return_value = True
    mock_client.budlist = ["W3ADO-1"]

    mock_coordinator = MagicMock()
    temp_sensor = APRSWSSensorData(
        timestamp=1700000000,
        callsign="W3ADO-1",
        type="temperature",
        value=21.5,
    )
    mock_coordinator.data = {"W3ADO-1_temperature": temp_sensor}

    mock_entry = MagicMock()
    mock_entry.entry_id = "entry_123"
    mock_entry.domain = DOMAIN
    mock_entry.title = "N0CALL"
    mock_entry.data = {CONF_YOUR_CALLSIGN: "N0CALL"}
    mock_entry.subentries = {"sub_1": mock_subentry}
    mock_entry.runtime_data.client = mock_client
    mock_entry.runtime_data.coordinator = mock_coordinator

    diagnostics = await async_get_config_entry_diagnostics(hass, mock_entry)

    assert diagnostics["entry"]["entry_id"] == "entry_123"
    assert diagnostics["entry"]["title"] == "N0CALL"
    assert len(diagnostics["entry"]["subentries"]) == 1
    assert diagnostics["entry"]["subentries"][0]["callsign"] == "W3ADO-1"

    assert diagnostics["connection"]["is_connected"] is True
    assert diagnostics["connection"]["is_listening"] is True
    assert diagnostics["connection"]["budlist"] == ["W3ADO-1"]

    assert diagnostics["coordinator"]["sensor_count"] == 1
    assert "W3ADO-1_temperature" in diagnostics["coordinator"]["sensors"]
    assert diagnostics["coordinator"]["sensors"]["W3ADO-1_temperature"]["value"] == 21.5
