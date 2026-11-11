"""Constants for aprs_weather_station."""

from logging import Logger, getLogger
from typing import Final

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    DEGREE,
    LIGHT_LUX,
    PERCENTAGE,
    EntityCategory,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)

LOGGER: Logger = getLogger(__package__)

DOMAIN = "aprs_weather_station"
ATTRIBUTION = "Data provided by https://www.aprs-is.net/"

CONF_YOUR_CALLSIGN: Final = "your_callsign"
CONF_CALLSIGN: Final = "callsign"

APRSIS_USER_DEFINED_PORT: Final = 14580
APRSIS_FULL_FEED_PORT: Final = 10152

SENSOR_DESCRIPTIONS: Final[tuple[SensorEntityDescription, ...]] = (
    SensorEntityDescription(
        key="timestamp",
        translation_key="last_timestamp",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        has_entity_name=True,
    ),
    SensorEntityDescription(
        key="packet_received",
        translation_key="packet_received",
        icon="mdi:message-check",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        has_entity_name=True,
    ),
    SensorEntityDescription(
        key="is_connected",
        translation_key="is_connected",
        icon="mdi:connection",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        has_entity_name=True,
    ),
    SensorEntityDescription(
        key="wind_speed",
        translation_key="wind_speed",
        icon="mdi:weather-windy",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        has_entity_name=True,
    ),
    SensorEntityDescription(
        key="wind_direction",
        translation_key="wind_direction",
        icon="mdi:compass",
        device_class=SensorDeviceClass.WIND_DIRECTION,
        state_class=SensorStateClass.MEASUREMENT_ANGLE,
        native_unit_of_measurement=DEGREE,
        has_entity_name=True,
    ),
    SensorEntityDescription(
        key="wind_gust",
        translation_key="wind_gust",
        icon="mdi:weather-windy-variant",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        has_entity_name=True,
    ),
    SensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        has_entity_name=True,
    ),
    SensorEntityDescription(
        key="precipitation",
        translation_key="precipitation",
        icon="mdi:weather-rainy",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        has_entity_name=True,
    ),
    SensorEntityDescription(
        key="humidity",
        translation_key="humidity",
        icon="mdi:water-percent",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        has_entity_name=True,
    ),
    SensorEntityDescription(
        key="atmospheric_pressure",
        translation_key="atmospheric_pressure",
        icon="mdi:gauge",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.HPA,
        has_entity_name=True,
    ),
    SensorEntityDescription(
        key="illuminance",
        translation_key="illuminance",
        icon="mdi:brightness-5",
        device_class=SensorDeviceClass.ILLUMINANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=LIGHT_LUX,
        has_entity_name=True,
    ),
)

SENSOR_DESCRIPTIONS_MAP: Final[dict[str, SensorEntityDescription]] = {
    desc.key: desc for desc in SENSOR_DESCRIPTIONS
}

SENSOR_TYPE_TO_MDI_ICONS: Final[dict[str, str]] = {
    desc.key: desc.icon or "" for desc in SENSOR_DESCRIPTIONS if desc.icon
}
SENSOR_TYPE_TO_MDI_ICONS["location"] = "mdi:map-marker"

SENSOR_TYPE_TO_SENSOR_STATE_CLASS: Final[dict[str, SensorStateClass | str | None]] = {
    desc.key: desc.state_class for desc in SENSOR_DESCRIPTIONS
}

SENSOR_TYPE_TO_UNIT_OF_MEASUREMENT: Final[dict[str, str | None]] = {
    desc.key: desc.native_unit_of_measurement for desc in SENSOR_DESCRIPTIONS
}

SENSOR_TYPE_TO_SENSOR_DEVICE_CLASS: Final[dict[str, SensorDeviceClass | None]] = {
    desc.key: desc.device_class for desc in SENSOR_DESCRIPTIONS
}
