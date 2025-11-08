"""
Custom integration to integrate aprs_weather_station with Home Assistant.

For more details about this integration, please refer to
https://github.com/zinuzoid/aprs_weather_station_hacs
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import CONF_PORT, Platform
from homeassistant.loader import async_get_loaded_integration

from .api import APRSWSApiClient
from .const import CONF_YOUR_CALLSIGN, DOMAIN, LOGGER
from .coordinator import APRSWSDataUpdateCoordinator
from .data import APRSWSData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import APRSWSConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: APRSWSConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    coordinator = APRSWSDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(hours=1),
    )
    entry.runtime_data = APRSWSData(
        client=APRSWSApiClient(
            callsign=entry.data[CONF_YOUR_CALLSIGN],
            port=14580,
            budlist=None,
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: APRSWSConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: APRSWSConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
