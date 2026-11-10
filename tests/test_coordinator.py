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
