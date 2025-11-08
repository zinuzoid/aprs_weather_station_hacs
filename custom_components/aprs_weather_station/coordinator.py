"""DataUpdateCoordinator for integration_blueprint."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.aprs_weather_station.const import LOGGER

from .api import (
    APRSWSApiClientAuthenticationError,
    APRSWSApiClientError,
)

if TYPE_CHECKING:
    from .data import APRSWSConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class APRSWSDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: APRSWSConfigEntry

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        LOGGER.debug("_async_update_data")
        try:
            return {}
        except APRSWSApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except APRSWSApiClientError as exception:
            raise UpdateFailed(exception) from exception
