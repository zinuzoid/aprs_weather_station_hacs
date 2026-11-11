"""APRS packet parser for extracting sensor data."""

from datetime import UTC, datetime
from typing import Any, Final

from .const import LOGGER
from .data import APRSWSSensorData

WEATHER_FIELD_TO_SENSOR_TYPE: Final[dict[str, str]] = {
    "wind_speed": "wind_speed",
    "wind_gust": "wind_gust",
    "temperature": "temperature",
    "rain_1h": "precipitation",
    "humidity": "humidity",
    "pressure": "atmospheric_pressure",
    "luminosity": "illuminance",
}


def parse_aprs_packet(packet: dict[str, Any]) -> list[APRSWSSensorData]:
    """Parse an APRS packet and extract sensor data."""
    timestamp = packet.get("timestamp")
    callsign = packet.get("from")

    if not timestamp or not callsign:
        LOGGER.error("Packet doesn't include timestamp nor from! Skipping...")
        return []

    sensor_data: list[APRSWSSensorData] = [
        APRSWSSensorData(
            timestamp=timestamp,
            callsign=callsign,
            type="timestamp",
            value=datetime.fromtimestamp(timestamp, tz=UTC),
        ),
        APRSWSSensorData(
            timestamp=timestamp,
            callsign=callsign,
            type="packet_received",
            value=1,
        ),
    ]

    # Add location sensor if latitude and longitude are available
    if "latitude" in packet and "longitude" in packet:
        try:
            lat = float(packet["latitude"])
            lon = float(packet["longitude"])
            sensor_data.append(
                APRSWSSensorData(
                    timestamp=timestamp,
                    callsign=callsign,
                    type="location",
                    value=(lat, lon),
                )
            )
        except (ValueError, TypeError) as err:
            LOGGER.debug("Could not parse coordinates: %s", err)

    # Parse weather data if available
    weather = packet.get("weather")
    if weather and isinstance(weather, dict):
        for field, sensor_type in WEATHER_FIELD_TO_SENSOR_TYPE.items():
            if field in weather:
                sensor_data.append(
                    APRSWSSensorData(
                        timestamp=timestamp,
                        callsign=callsign,
                        type=sensor_type,
                        value=weather[field],
                    )
                )

        if "course" in packet:
            sensor_data.append(
                APRSWSSensorData(
                    timestamp=timestamp,
                    callsign=callsign,
                    type="wind_direction",
                    value=packet["course"],
                )
            )

    return sensor_data


class APRSPacketParser:
    """Parser for APRS packets to extract sensor data."""

    @staticmethod
    def parse(packet: dict[str, Any]) -> list[APRSWSSensorData]:
        """Parse an APRS packet and extract sensor data."""
        return parse_aprs_packet(packet)
