"""Sensor platform for aprs_weather_station."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import callback

from .const import (
    CONF_CALLSIGN,
    LOGGER,
    SENSOR_TYPE_TO_MDI_ICONS,
    SENSOR_TYPE_TO_SENSOR_DEVICE_CLASS,
    SENSOR_TYPE_TO_SENSOR_STATE_CLASS,
    SENSOR_TYPE_TO_UNIT_OF_MEASUREMENT,
)
from .data import APRSWSSensorData
from .entity import APRSWSEntity

if TYPE_CHECKING:
    from datetime import datetime
    from types import MappingProxyType

    from homeassistant.config_entries import ConfigSubentry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from .coordinator import APRSWSDataUpdateCoordinator
    from .data import APRSWSConfigEntry


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
            "_check_device entry.subentries:%s\nknown_sensors:%s\nnew_sensors:%s",
            entry.subentries,
            known_sensors,
            new_sensors,
        )
        for sensor in list(new_sensors):
            if sensor.type == "is_connected":
                entities = [
                    APRSWSSensor(
                        data=sensor,
                        coordinator=coordinator,
                    )
                ]
                subentry_id = None
            else:
                subentry = _find_subentry(entry.subentries, sensor.callsign)
                if not subentry:
                    LOGGER.error("Cannot find subentry %s", sensor.callsign)
                    continue
                if sensor.type == "packet_received":
                    entities = [
                        APRSWSPacketReceivedSensor(
                            data=sensor,
                            coordinator=coordinator,
                        )
                    ]
                else:
                    entities = [
                        APRSWSSensor(
                            data=sensor,
                            coordinator=coordinator,
                        )
                    ]
                subentry_id = subentry.subentry_id
            async_add_entities(
                entities,
                config_subentry_id=subentry_id,
            )
            known_sensors.add(sensor.key)
            LOGGER.debug("Added sensor %s to %s", sensor, subentry_id)

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
            if data.type == "timestamp":
                entity_description = SensorEntityDescription(
                    key=data.key,
                    translation_key="last_timestamp",
                    has_entity_name=True,
                    device_class=SENSOR_TYPE_TO_SENSOR_DEVICE_CLASS[data.type],
                    icon=SENSOR_TYPE_TO_MDI_ICONS[data.type],
                    state_class=SENSOR_TYPE_TO_SENSOR_STATE_CLASS[data.type],
                    native_unit_of_measurement=SENSOR_TYPE_TO_UNIT_OF_MEASUREMENT[
                        data.type
                    ],
                    entity_category=EntityCategory.DIAGNOSTIC,
                )
            elif data.type == "packet_received":
                entity_description = SensorEntityDescription(
                    key=data.key,
                    translation_key="packet_received",
                    has_entity_name=True,
                    device_class=SENSOR_TYPE_TO_SENSOR_DEVICE_CLASS[data.type],
                    icon=SENSOR_TYPE_TO_MDI_ICONS[data.type],
                    state_class=SENSOR_TYPE_TO_SENSOR_STATE_CLASS[data.type],
                    native_unit_of_measurement=SENSOR_TYPE_TO_UNIT_OF_MEASUREMENT[
                        data.type
                    ],
                    entity_category=EntityCategory.DIAGNOSTIC,
                )
            elif data.type == "is_connected":
                entity_description = SensorEntityDescription(
                    key=data.key,
                    translation_key="is_connected",
                    has_entity_name=True,
                    device_class=SENSOR_TYPE_TO_SENSOR_DEVICE_CLASS[data.type],
                    icon=SENSOR_TYPE_TO_MDI_ICONS[data.type],
                    state_class=SENSOR_TYPE_TO_SENSOR_STATE_CLASS[data.type],
                    native_unit_of_measurement=SENSOR_TYPE_TO_UNIT_OF_MEASUREMENT[
                        data.type
                    ],
                    entity_category=EntityCategory.DIAGNOSTIC,
                )
            else:
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
                )

        super().__init__(coordinator, entity_description, data.callsign)
        self.entity_description = entity_description
        self.data = data
        if self.device_info:
            self.device_info.update(name=data.callsign)

    @property
    def native_value(self) -> StateType | datetime:
        """Return the native value of the sensor."""
        return self.data.value

    @staticmethod
    def _find_sensor_data(
        sensors: list[APRSWSSensorData], key: str
    ) -> APRSWSSensorData | None:
        return next(
            (data for data in sensors if data.key == key),
            None,
        )

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

        LOGGER.debug(
            "update sensor_data for %s with value %s",
            new_data.key,
            new_data.value,
        )
        self.data = new_data
        self.async_write_ha_state()


class APRSWSPacketReceivedSensor(APRSWSSensor):
    """Sensor for packet received with incremental counter."""

    def __init__(
        self,
        data: APRSWSSensorData,
        coordinator: APRSWSDataUpdateCoordinator,
        entity_description: SensorEntityDescription | None = None,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(data, coordinator, entity_description)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        new_data = self._find_sensor_data(
            self.coordinator.data, self.entity_description.key
        )
        if not new_data:
            return

        if self.data.timestamp == new_data.timestamp:
            LOGGER.warning("found duplicated timestamp, ignore data...")
            return

        new_data_copy = APRSWSSensorData.from_other_with_new_value(
            new_data,
            (
                (new_data.value if isinstance(new_data.value, int) else 1)
                + (self.data.value if isinstance(self.data.value, int) else 0)
            ),
        )

        LOGGER.debug(
            "self.data.value=%s new_data.value=%s new_data_copy.value=%s",
            self.data.value,
            new_data.value,
            new_data_copy.value,
        )

        LOGGER.debug(
            "update sensor_data for %s with value %s",
            new_data_copy.key,
            new_data_copy.value,
        )
        self.data = new_data_copy
        self.async_write_ha_state()
