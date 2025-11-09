"""DataUpdateCoordinator for integration_blueprint."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .aprs_parser import APRSPacketParser
from .const import CONF_CALLSIGN, LOGGER
from .data import APRSWSSensorData

if TYPE_CHECKING:
    from .data import APRSWSConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class APRSWSDataUpdateCoordinator(DataUpdateCoordinator[list[APRSWSSensorData]]):
    """Class to manage fetching data from the API."""

    config_entry: APRSWSConfigEntry

    def aprs_callback(self, packet: dict[str, Any]) -> None:
        """Execute on non-loop thread. Handle APRS packet."""
        LOGGER.debug("Received packet: %s", packet)

        data = APRSPacketParser().parse(packet)

        LOGGER.debug("update data %s", data)
        self.hass.add_job(
            self.async_set_updated_data,
            data,
        )

    async def _async_update_data(self) -> list[APRSWSSensorData]:
        """Update data via library."""
        client = self.config_entry.runtime_data.client
        LOGGER.debug("_async_update_data")
        budlist = [e.data[CONF_CALLSIGN] for e in self.config_entry.subentries.values()]
        if not budlist:
            LOGGER.warning("budlist is None, skip start_listening!")
            return []

        client.budlist = budlist
        client.start_listening(self.aprs_callback)

        return []

    async def async_shutdown(self) -> None:
        """Run shutdown clean up."""
        self.config_entry.runtime_data.client.stop_and_join()
        await super().async_shutdown()
