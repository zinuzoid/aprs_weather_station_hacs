"""Sensor platform for aprs_weather_station."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import callback

from .const import (
    CONF_CALLSIGN,
    LOGGER,
    SENSOR_TYPE_TO_ENTITY_CATEGORY,
    SENSOR_TYPE_TO_MDI_ICONS,
    SENSOR_TYPE_TO_SENSOR_DEVICE_CLASS,
    SENSOR_TYPE_TO_SENSOR_STATE_CLASS,
    SENSOR_TYPE_TO_UNIT_OF_MEASUREMENT,
)
from .entity import APRSWSEntity

if TYPE_CHECKING:
    from datetime import datetime
    from types import MappingProxyType

    from homeassistant.config_entries import ConfigSubentry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
    from homeassistant.helpers.typing import StateType

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
            filter(lambda s: s.key not in known_sensors, coordinator.data)
        )
        LOGGER.debug(
            "_check_device %s %s %s", entry.subentries, known_sensors, new_sensors
        )
        for sensor in list(new_sensors):
            subentry = _find_subentry(entry.subentries, sensor.callsign)
            if not subentry:
                LOGGER.error("Cannot find subentry %s", sensor.callsign)
                continue
            async_add_entities(
                [
                    APRSWSSensor(
                        data=sensor,
                        coordinator=coordinator,
                    )
                ],
                config_subentry_id=subentry.subentry_id,
            )
            known_sensors.add(sensor.key)
            LOGGER.debug("Added sensor %s", sensor)

    entry.async_on_unload(coordinator.async_add_listener(_check_device))


class APRSWSSensor(APRSWSEntity, SensorEntity):
    """APRS Weather Station Sensor class."""

    def __init__(
        self,
        data: APRSWSSensorData,
        coordinator: APRSWSDataUpdateCoordinator,
        entity_description: SensorEntityDescription | None = None,
    ) -> None:
        """Initialize the sensor class."""
        if entity_description is None:
            entity_description = SensorEntityDescription(
                key=data.key,
                translation_key=data.type,
                has_entity_name=True,
                device_class=SENSOR_TYPE_TO_SENSOR_DEVICE_CLASS[data.type],
                icon=SENSOR_TYPE_TO_MDI_ICONS[data.type],
                state_class=SENSOR_TYPE_TO_SENSOR_STATE_CLASS[data.type],
                native_unit_of_measurement=SENSOR_TYPE_TO_UNIT_OF_MEASUREMENT[
                    data.type
                ],
                entity_category=SENSOR_TYPE_TO_ENTITY_CATEGORY[data.type],
            )

        super().__init__(coordinator, entity_description)
        self.entity_description = entity_description
        self.data = data
        if self.device_info:
            self.device_info.update(name=data.callsign)

    @property
    def native_value(self) -> StateType | datetime:
        """Return the native value of the sensor."""
        return self.data.value

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        sensor_data = next(
            (
                data
                for data in self.coordinator.data
                if data.key == self.entity_description.key
            ),
            None,
        )
        if not sensor_data:
            return

        LOGGER.debug(
            "update sensor_data for %s with value %s",
            sensor_data.key,
            sensor_data.value,
        )
        self.data = sensor_data
        self.async_write_ha_state()
