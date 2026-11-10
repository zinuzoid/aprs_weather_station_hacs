"""Constants for aprs_weather_station."""

from logging import Logger, getLogger
from typing import Final

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    DEGREE,
    LIGHT_LUX,
    PERCENTAGE,
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

SENSOR_TYPE_TO_MDI_ICONS: Final[dict[str, str]] = {
    "timestamp": "mdi:clock-outline",
    "packet_received": "mdi:message-check",
    "wind_speed": "mdi:weather-windy",
    "wind_direction": "mdi:compass",
    "wind_gust": "mdi:weather-windy-variant",
    "temperature": "mdi:thermometer",
    "precipitation": "mdi:weather-rainy",
    "humidity": "mdi:water-percent",
    "atmospheric_pressure": "mdi:gauge",
    "illuminance": "mdi:brightness-5",
    "location": "mdi:map-marker",
    "is_connected": "mdi:connection",
}

SENSOR_TYPE_TO_SENSOR_STATE_CLASS: Final[dict[str, SensorStateClass | None]] = {
    "timestamp": SensorStateClass.TOTAL_INCREASING,
    "packet_received": SensorStateClass.TOTAL_INCREASING,
    "wind_speed": SensorStateClass.MEASUREMENT,
    "wind_direction": SensorStateClass.MEASUREMENT_ANGLE,
    "wind_gust": SensorStateClass.MEASUREMENT,
    "temperature": SensorStateClass.MEASUREMENT,
    "precipitation": SensorStateClass.MEASUREMENT,
    "humidity": SensorStateClass.MEASUREMENT,
    "atmospheric_pressure": SensorStateClass.MEASUREMENT,
    "illuminance": SensorStateClass.MEASUREMENT,
    "is_connected": None,
}

SENSOR_TYPE_TO_UNIT_OF_MEASUREMENT: Final[dict[str, str | None]] = {
    "timestamp": None,
    "packet_received": None,
    "wind_speed": UnitOfSpeed.METERS_PER_SECOND,
    "wind_direction": DEGREE,
    "wind_gust": UnitOfSpeed.METERS_PER_SECOND,
    "temperature": UnitOfTemperature.CELSIUS,
    "precipitation": UnitOfPrecipitationDepth.MILLIMETERS,
    "humidity": PERCENTAGE,
    "atmospheric_pressure": UnitOfPressure.HPA,
    "illuminance": LIGHT_LUX,
    "is_connected": None,
}

SENSOR_TYPE_TO_SENSOR_DEVICE_CLASS: Final[dict[str, SensorDeviceClass | None]] = {
    "timestamp": SensorDeviceClass.TIMESTAMP,
    "packet_received": None,
    "wind_speed": SensorDeviceClass.WIND_SPEED,
    "wind_direction": SensorDeviceClass.WIND_DIRECTION,
    "wind_gust": SensorDeviceClass.WIND_SPEED,
    "temperature": SensorDeviceClass.TEMPERATURE,
    "precipitation": SensorDeviceClass.PRECIPITATION,
    "humidity": SensorDeviceClass.HUMIDITY,
    "atmospheric_pressure": SensorDeviceClass.ATMOSPHERIC_PRESSURE,
    "illuminance": SensorDeviceClass.ILLUMINANCE,
    "is_connected": SensorDeviceClass.ENUM,
}
