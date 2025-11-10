"""DataUpdateCoordinator for integration_blueprint."""

from __future__ import annotations

from time import time
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
        LOGGER.debug("_async_update_data")
        client = self.config_entry.runtime_data.client
        data = [
            APRSWSSensorData(
                timestamp=int(time()),
                callsign="SELF",
                type="is_connected",
                value=client.is_connected(),
            )
        ]

        budlist = [e.data[CONF_CALLSIGN] for e in self.config_entry.subentries.values()]
        if not budlist:
            LOGGER.warning("budlist is None, skip start_listening!")
            return data

        if budlist != client.budlist:
            client.budlist = budlist
            client.start_listening(self.aprs_callback)

        return data

    async def async_shutdown(self) -> None:
        """Run shutdown clean up."""
        self.config_entry.runtime_data.client.stop_and_join()
        await super().async_shutdown()
