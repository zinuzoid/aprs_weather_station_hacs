"""Device tracker platform for aprs_weather_station."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.device_tracker.config_entry import (
    TrackerEntity,
    TrackerEntityDescription,
)
from homeassistant.core import callback

from .const import (
    CONF_CALLSIGN,
    LOGGER,
    SENSOR_TYPE_TO_MDI_ICONS,
)
from .entity import APRSWSEntity

if TYPE_CHECKING:
    from datetime import datetime
    from types import MappingProxyType

    from homeassistant.config_entries import ConfigSubentry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

    from .coordinator import APRSWSDataUpdateCoordinator
    from .data import APRSWSConfigEntry, APRSWSSensorData


def _find_subentry(
    subentries: MappingProxyType[str, ConfigSubentry], callsign: str
) -> ConfigSubentry | None:
    return next(
        (
            subentry
            for subentry in subentries.values()
            if subentry.data[CONF_CALLSIGN] == callsign
        ),
        None,
    )


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: APRSWSConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data.coordinator

    known_sensors: set[str] = set()

    def _check_device() -> None:
        new_sensors = list(
            filter(
                lambda s: s.key not in known_sensors and s.type == "location",
                coordinator.data,
            )
        )
        LOGGER.debug(
            "_check_device entry.subentries:%s\nknown_sensors:%s\nnew_sensors:%s",
            entry.subentries,
            known_sensors,
            new_sensors,
        )
        for sensor in list(new_sensors):
            subentry = _find_subentry(entry.subentries, sensor.callsign)
            if not subentry:
                LOGGER.error("Cannot find subentry %s", sensor.callsign)
                continue
            async_add_entities(
                [
                    APRSWSLocationSensor(
                        data=sensor,
                        coordinator=coordinator,
                    ),
                ],
                config_subentry_id=subentry.subentry_id,
            )
            known_sensors.add(sensor.key)
            LOGGER.debug("Added sensor %s to %s", sensor, subentry.subentry_id)

    entry.async_on_unload(coordinator.async_add_listener(_check_device))


class APRSWSLocationSensor(APRSWSEntity, TrackerEntity):
    """APRS Weather Station Sensor class."""

    def __init__(
        self,
        data: APRSWSSensorData,
        coordinator: APRSWSDataUpdateCoordinator,
        entity_description: TrackerEntityDescription | None = None,
    ) -> None:
        """Initialize the sensor class."""
        if entity_description is None:
            entity_description = TrackerEntityDescription(
                key=data.key,
                translation_key=data.type,
                has_entity_name=True,
                icon=SENSOR_TYPE_TO_MDI_ICONS[data.type],
            )

        super().__init__(coordinator, entity_description, data.callsign)
        self.entity_description = entity_description
        self._set_location_data(data.value)
        self.data = data
        if self.device_info:
            self.device_info.update(name=data.callsign)

    @staticmethod
    def _find_sensor_data(
        sensors: list[APRSWSSensorData], key: str
    ) -> APRSWSSensorData | None:
        return next(
            (data for data in sensors if data.key == key),
            None,
        )

    def _set_location_data(self, value: str | float | datetime | None) -> bool:
        if not isinstance(value, str):
            LOGGER.error("value is not str, %s", value)
            return False
        lat, lon = value.split(",")

        lat = float(lat)
        lon = float(lon)

        self._attr_latitude = lat
        self._attr_longitude = lon

        return True

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        new_data = self._find_sensor_data(
            self.coordinator.data, self.entity_description.key
        )
        if not new_data:
            return

        if self.data and self.data.timestamp == new_data.timestamp:
            LOGGER.warning("found duplicated timestamp, ignore data...")
            return

        if not self._set_location_data(new_data.value):
            return

        LOGGER.debug(
            "update sensor_data for %s with value %s %s",
            new_data.key,
        )
        self.data = new_data
        self.async_write_ha_state()
