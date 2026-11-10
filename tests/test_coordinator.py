"""Tests for APRS Weather Station coordinator."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.aprs_weather_station.const import DOMAIN
from custom_components.aprs_weather_station.coordinator import (
    APRSWSDataUpdateCoordinator,
)
from custom_components.aprs_weather_station.data import APRSWSSensorData


@pytest.mark.asyncio
async def test_coordinator_init_passes_config_entry() -> None:
    """Test coordinator initialization with config_entry (Item 9)."""
    hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry_id"
    mock_entry.domain = DOMAIN

    coordinator = APRSWSDataUpdateCoordinator(hass, mock_entry)

    assert coordinator.config_entry is mock_entry
    assert coordinator.name == DOMAIN


@pytest.mark.asyncio
async def test_coordinator_status_callback_updates_is_connected() -> None:
    """Test real-time connection status callback update (Item 6)."""
    hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry_id"
    mock_entry.domain = DOMAIN

    coordinator = APRSWSDataUpdateCoordinator(hass, mock_entry)
    coordinator.async_set_updated_data = MagicMock()

    # Simulate connection dropping
    coordinator.aprs_status_callback(False)
    # add_job runs _async_handle_status_update
    coordinator._async_handle_status_update(False)

    call_args = coordinator.async_set_updated_data.call_args[0][0]
    conn_sensor = next(s for s in call_args if s.key == "APRS-IS_is_connected")
    assert conn_sensor.value is False

    # Simulate reconnect
    coordinator.aprs_status_callback(True)
    coordinator._async_handle_status_update(True)

    call_args = coordinator.async_set_updated_data.call_args[0][0]
    conn_sensor = next(s for s in call_args if s.key == "APRS-IS_is_connected")
    assert conn_sensor.value is True


@pytest.mark.asyncio
async def test_coordinator_packet_callback_merges_data_and_keeps_connected() -> None:
    """Test packet callback preserves is_connected and merges sensors (Item 6)."""
    hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry_id"
    mock_entry.domain = DOMAIN

    coordinator = APRSWSDataUpdateCoordinator(hass, mock_entry)

    # Initial packet
    weather_sensor = APRSWSSensorData(
        timestamp=1700000000,
        callsign="W3ADO-1",
        type="temperature",
        value=21.5,
    )
    coordinator._async_handle_packet_data([weather_sensor])

    sensor_map = {s.key: s for s in coordinator.data}
    assert "APRS-IS_is_connected" in sensor_map
    assert sensor_map["APRS-IS_is_connected"].value is True
    assert "W3ADO-1_temperature" in sensor_map
    assert sensor_map["W3ADO-1_temperature"].value == 21.5

    # Second packet with another sensor
    humidity_sensor = APRSWSSensorData(
        timestamp=1700000010,
        callsign="W3ADO-1",
        type="humidity",
        value=65,
    )
    coordinator._async_handle_packet_data([humidity_sensor])

    sensor_map = {s.key: s for s in coordinator.data}
    assert sensor_map["APRS-IS_is_connected"].value is True
    assert sensor_map["W3ADO-1_temperature"].value == 21.5
    assert sensor_map["W3ADO-1_humidity"].value == 65


@pytest.mark.asyncio
async def test_coordinator_async_shutdown_uses_executor() -> None:
    """Test async_shutdown invokes stop_and_join in executor (Item 2)."""
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(return_value=None)

    mock_client = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry_id"
    mock_entry.domain = DOMAIN
    mock_entry.runtime_data.client = mock_client

    coordinator = APRSWSDataUpdateCoordinator(hass, mock_entry)

    await coordinator.async_shutdown()

    hass.async_add_executor_job.assert_called_once_with(mock_client.stop_and_join)


@pytest.mark.asyncio
async def test_coordinator_update_data_revives_listener() -> None:
    """Test that _async_update_data revives dead listener (Item 3)."""
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(return_value=None)

    subentry1 = MagicMock()
    subentry1.data = {"callsign": "W3ADO-1"}

    mock_client = MagicMock()
    mock_client.is_connected.return_value = False
    mock_client.is_listening.return_value = False  # Listener died!
    mock_client.budlist = ["W3ADO-1"]

    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry_id"
    mock_entry.domain = DOMAIN
    mock_entry.subentries = {"s1": subentry1}
    mock_entry.runtime_data.client = mock_client

    coordinator = APRSWSDataUpdateCoordinator(hass, mock_entry)

    await coordinator._async_update_data()

    # Verify listener was restarted via executor
    hass.async_add_executor_job.assert_called_once_with(
        mock_client.start_listening,
        coordinator.aprs_callback,
        coordinator.aprs_status_callback,
    )
