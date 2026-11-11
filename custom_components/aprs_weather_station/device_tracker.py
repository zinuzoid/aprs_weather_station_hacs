"""Device tracker platform for aprs_weather_station."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.device_tracker.config_entry import (
    TrackerEntity,
    TrackerEntityDescription,
)
from homeassistant.core import callback

from .const import (
    LOGGER,
    SENSOR_TYPE_TO_MDI_ICONS,
)
from .entity import APRSWSEntity, find_subentry

# Backward-compatible alias
_find_subentry = find_subentry

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

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
        sensor_items = (
            coordinator.data.values()
            if isinstance(coordinator.data, dict)
            else (coordinator.data or [])
        )
        new_sensors = [
            s
            for s in sensor_items
            if s.key not in known_sensors and s.type == "location"
        ]
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
            self.device_info["name"] = data.callsign

    def _set_location_data(
        self, value: tuple[float, float] | str | float | datetime | None
    ) -> bool:
        if isinstance(value, tuple):
            try:
                lat, lon = value
                self._attr_latitude = float(lat)
                self._attr_longitude = float(lon)
            except (ValueError, TypeError):
                LOGGER.error("Failed to parse location tuple: %s", value)
                return False
            else:
                return True
        if isinstance(value, str):
            try:
                lat_str, lon_str = value.split(",")
                self._attr_latitude = float(lat_str)
                self._attr_longitude = float(lon_str)
            except (ValueError, AttributeError):
                LOGGER.error("Failed to parse location string: %s", value)
                return False
            else:
                return True
        LOGGER.error("Value is not a valid location: %s", value)
        return False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        new_data = self._find_sensor_data(
            self.coordinator.data, self.entity_description.key
        )
        if not new_data:
            return

        if (
            self.data
            and self.data.timestamp == new_data.timestamp
            and self.data.value == new_data.value
        ):
            LOGGER.debug(
                "Duplicate location for %s (timestamp=%s, value=%s), skipping",
                new_data.key,
                new_data.timestamp,
                new_data.value,
            )
            return

        if not self._set_location_data(new_data.value):
            return

        LOGGER.debug(
            "update sensor_data for %s with value %s",
            new_data.key,
            new_data.value,
        )
        self.data = new_data
        self.async_write_ha_state()
