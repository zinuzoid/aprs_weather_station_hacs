"""Tests for APRS Weather Station coordinator."""

from unittest.mock import MagicMock

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
