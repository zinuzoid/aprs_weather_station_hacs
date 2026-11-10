"""Tests for integration setup and unload."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from custom_components.aprs_weather_station import (
    async_setup_entry,
    async_unload_entry,
)
from custom_components.aprs_weather_station.api import (
    APRSWSApiClientAuthenticationError,
    APRSWSApiClientCommunicationError,
)
from custom_components.aprs_weather_station.const import CONF_YOUR_CALLSIGN, DOMAIN


@pytest.mark.asyncio
async def test_async_setup_entry_raises_config_entry_not_ready() -> None:
    """Test async_setup_entry raises ConfigEntryNotReady on conn failure (Item 18)."""
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(
        side_effect=APRSWSApiClientCommunicationError("APRS-IS server down")
    )

    entry = MagicMock()
    entry.domain = DOMAIN
    entry.data = {CONF_YOUR_CALLSIGN: "N0CALL"}

    with pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(hass, entry)


@pytest.mark.asyncio
async def test_async_setup_entry_raises_config_entry_auth_failed() -> None:
    """Test async_setup_entry raises ConfigEntryAuthFailed on auth failure (Item 18)."""
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(
        side_effect=APRSWSApiClientAuthenticationError("Bad credentials")
    )

    entry = MagicMock()
    entry.domain = DOMAIN
    entry.data = {CONF_YOUR_CALLSIGN: "N0CALL"}

    with pytest.raises(ConfigEntryAuthFailed):
        await async_setup_entry(hass, entry)


@pytest.mark.asyncio
async def test_async_setup_and_unload_entry_success() -> None:
    """Test successful setup and unload flow."""
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(return_value=None)
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    entry = MagicMock()
    entry.domain = DOMAIN
    entry.entry_id = "test_entry"
    entry.data = {CONF_YOUR_CALLSIGN: "N0CALL"}

    with (
        patch("custom_components.aprs_weather_station.async_get_loaded_integration"),
        patch(
            "custom_components.aprs_weather_station.coordinator.APRSWSDataUpdateCoordinator.async_config_entry_first_refresh",
            new_callable=AsyncMock,
        ),
    ):
        result = await async_setup_entry(hass, entry)
        assert result is True
        assert entry.runtime_data is not None

        unload_result = await async_unload_entry(hass, entry)
        assert unload_result is True
