"""Tests for APRS Weather Station coordinator."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.aprs_weather_station.const import DOMAIN
from custom_components.aprs_weather_station.coordinator import (
    APRSWSDataUpdateCoordinator,
)


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
    )
