"""Sensor platform for aprs_weather_station."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import callback

from .const import CONF_CALLSIGN, LOGGER
from .entity import APRSWSEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from .coordinator import APRSWSDataUpdateCoordinator
    from .data import APRSWSConfigEntry, APRSWSSensorData


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
            subentry = next(
                (
                    subentry
                    for subentry in entry.subentries.values()
                    if subentry.data[CONF_CALLSIGN] == sensor.callsign
                ),
                None,
            )
            if not subentry:
                LOGGER.error("Cannot find subentry with %s", sensor.callsign)
                continue
            async_add_entities(
                [
                    APRSWSSensor(
                        data=sensor,
                        coordinator=coordinator,
                        entity_description=SensorEntityDescription(
                            key=sensor.key,
                            name=sensor.type,
                            device_class=SensorDeviceClass.WIND_SPEED,
                            icon="mdi:format-quote-close",
                            state_class=SensorStateClass.MEASUREMENT,
                            native_unit_of_measurement="m/s",
                        ),
                    )
                ],
                config_subentry_id=subentry.subentry_id,
            )
            known_sensors.add(sensor.key)
            LOGGER.debug("added sensor %s", sensor)

    entry.async_on_unload(coordinator.async_add_listener(_check_device))


class APRSWSSensor(APRSWSEntity, SensorEntity):
    """APRS Weather Station Sensor class."""

    def __init__(
        self,
        coordinator: APRSWSDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
        data: APRSWSSensorData,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator, entity_description)
        self.entity_description = entity_description
        self.data = data
        if self.device_info:
            self.device_info.update(name=data.callsign)

    @property
    def native_value(self) -> StateType:
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

        self.data = sensor_data
        self.async_write_ha_state()
