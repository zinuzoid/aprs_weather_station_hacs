"""Base entity for aprs_weather_station."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, CONF_CALLSIGN
from .coordinator import APRSWSDataUpdateCoordinator

if TYPE_CHECKING:
    from types import MappingProxyType

    from homeassistant.config_entries import ConfigSubentry
    from homeassistant.helpers.entity import EntityDescription

    from .data import APRSWSSensorData


def find_subentry(
    subentries: MappingProxyType[str, ConfigSubentry], callsign: str
) -> ConfigSubentry | None:
    """Find a subentry matching the callsign case-insensitively."""
    callsign_upper = callsign.upper()
    return next(
        (
            subentry
            for subentry in subentries.values()
            if subentry.data[CONF_CALLSIGN].upper() == callsign_upper
        ),
        None,
    )


def find_sensor_data(
    sensors: dict[str, APRSWSSensorData] | list[APRSWSSensorData] | None, key: str
) -> APRSWSSensorData | None:
    """Find sensor data by its unique key."""
    if not sensors:
        return None
    if isinstance(sensors, dict):
        return sensors.get(key)
    return next(
        (data for data in sensors if data.key == key),
        None,
    )


class APRSWSEntity(CoordinatorEntity[APRSWSDataUpdateCoordinator]):
    """APRSWSEntity class."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: APRSWSDataUpdateCoordinator,
        entity_description: EntityDescription,
        device_id: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = entity_description.key
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    device_id,
                ),
            },
        )

    @staticmethod
    def _find_sensor_data(
        sensors: dict[str, APRSWSSensorData] | list[APRSWSSensorData] | None, key: str
    ) -> APRSWSSensorData | None:
        return find_sensor_data(sensors, key)
