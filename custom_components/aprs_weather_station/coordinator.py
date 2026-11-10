"""DataUpdateCoordinator for integration_blueprint."""

from __future__ import annotations

from datetime import timedelta
from time import time
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .aprs_parser import APRSPacketParser
from .const import CONF_CALLSIGN, DOMAIN, LOGGER
from .data import APRSWSSensorData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import APRSWSConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class APRSWSDataUpdateCoordinator(DataUpdateCoordinator[list[APRSWSSensorData]]):
    """Class to manage fetching data from the API."""

    config_entry: APRSWSConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: APRSWSConfigEntry,
    ) -> None:
        """Initialize coordinator."""
        self._sensors_by_key: dict[str, APRSWSSensorData] = {}
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=1),
            config_entry=entry,
        )

    def _create_is_connected_data(self, *, is_connected: bool) -> APRSWSSensorData:
        return APRSWSSensorData(
            timestamp=int(time()),
            callsign="APRS-IS",
            type="is_connected",
            value=is_connected,
        )

    def aprs_status_callback(self, connected: bool) -> None:  # noqa: FBT001
        """Execute on non-loop thread. Handle connection status change."""
        LOGGER.debug("APRS connection status changed: %s", connected)
        self.hass.add_job(self._async_handle_status_update, connected)

    def _async_handle_status_update(self, connected: bool) -> None:  # noqa: FBT001
        """Handle connection status update on event loop."""
        conn_sensor = self._create_is_connected_data(is_connected=connected)
        self._sensors_by_key[conn_sensor.key] = conn_sensor
        self.async_set_updated_data(list(self._sensors_by_key.values()))

    def aprs_callback(self, packet: dict[str, Any]) -> None:
        """Execute on non-loop thread. Handle APRS packet."""
        LOGGER.debug("Received packet: %s", packet)

        data = APRSPacketParser().parse(packet)

        LOGGER.debug("update data %s", data)
        self.hass.add_job(self._async_handle_packet_data, data)

    def _async_handle_packet_data(self, data: list[APRSWSSensorData]) -> None:
        """Handle packet data on event loop."""
        conn_sensor = self._create_is_connected_data(is_connected=True)
        self._sensors_by_key[conn_sensor.key] = conn_sensor
        for item in data:
            self._sensors_by_key[item.key] = item
        self.async_set_updated_data(list(self._sensors_by_key.values()))

    async def _async_update_data(self) -> list[APRSWSSensorData]:
        """Update data via library."""
        LOGGER.debug("_async_update_data")
        client = self.config_entry.runtime_data.client
        is_conn = bool(client.is_connected())
        conn_sensor = self._create_is_connected_data(is_connected=is_conn)
        self._sensors_by_key[conn_sensor.key] = conn_sensor

        budlist = [
            e.data[CONF_CALLSIGN].upper() for e in self.config_entry.subentries.values()
        ]
        if not budlist:
            LOGGER.warning("budlist is None, skip start_listening!")
            return list(self._sensors_by_key.values())

        should_start = (budlist != client.budlist) or not client.is_listening()
        if should_start:
            client.budlist = budlist
            await self.hass.async_add_executor_job(
                client.start_listening,
                self.aprs_callback,
                self.aprs_status_callback,
            )

        return list(self._sensors_by_key.values())

    async def async_shutdown(self) -> None:
        """Run shutdown clean up."""
        await self.hass.async_add_executor_job(
            self.config_entry.runtime_data.client.stop_and_join
        )
        await super().async_shutdown()
