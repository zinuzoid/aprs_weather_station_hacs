"""APRS packet parser for extracting sensor data."""

from datetime import UTC, datetime
from typing import Any

from .const import LOGGER
from .data import APRSWSSensorData


class APRSPacketParser:
    """Parser for APRS packets to extract sensor data."""

    def parse(self, packet: dict[str, Any]) -> list[APRSWSSensorData]:
        """Parse an APRS packet and extract sensor data."""
        timestamp = packet.get("timestamp")
        callsign = packet.get("from")

        if not timestamp or not callsign:
            LOGGER.error("Packet doesn't include timestamp nor from! Skipping...")
            return []

        sensor_data: list[APRSWSSensorData] = []

        # Add timestamp as a sensor type
        sensor_data.append(
            APRSWSSensorData(
                timestamp=timestamp,
                callsign=callsign,
                type="timestamp",
                value=datetime.fromtimestamp(timestamp, tz=UTC),
            )
        )

        # Add packet received sensor
        sensor_data.append(
            APRSWSSensorData(
                timestamp=timestamp,
                callsign=callsign,
                type="packet_received",
                value=1,
            )
        )

        # Add location sensor if latitude and longitude are available
        if "latitude" in packet and "longitude" in packet:
            sensor_data.append(
                APRSWSSensorData(
                    timestamp=timestamp,
                    callsign=callsign,
                    type="location",
                    value=f"{packet['latitude']},{packet['longitude']}",
                )
            )

        # Parse weather data if available
        weather = packet.get("weather")
        if weather:
            if "wind_speed" in weather:
                sensor_data.append(
                    APRSWSSensorData(
                        timestamp=timestamp,
                        callsign=callsign,
                        type="wind_speed",
                        value=weather["wind_speed"],
                    )
                )

            if "course" in packet:
                # Add wind direction sensor
                sensor_data.append(
                    APRSWSSensorData(
                        timestamp=timestamp,
                        callsign=callsign,
                        type="wind_direction",
                        value=packet["course"],
                    )
                )

            if "wind_gust" in weather:
                sensor_data.append(
                    APRSWSSensorData(
                        timestamp=timestamp,
                        callsign=callsign,
                        type="wind_gust",
                        value=weather["wind_gust"],
                    )
                )

            if "temperature" in weather:
                sensor_data.append(
                    APRSWSSensorData(
                        timestamp=timestamp,
                        callsign=callsign,
                        type="temperature",
                        value=weather["temperature"],
                    )
                )

            if "rain_1h" in weather:
                sensor_data.append(
                    APRSWSSensorData(
                        timestamp=timestamp,
                        callsign=callsign,
                        type="precipitation",
                        value=weather["rain_1h"],
                    )
                )

            if "humidity" in weather:
                sensor_data.append(
                    APRSWSSensorData(
                        timestamp=timestamp,
                        callsign=callsign,
                        type="humidity",
                        value=weather["humidity"],
                    )
                )

            if "pressure" in weather:
                sensor_data.append(
                    APRSWSSensorData(
                        timestamp=timestamp,
                        callsign=callsign,
                        type="atmospheric_pressure",
                        value=weather["pressure"],
                    )
                )

            if "luminosity" in weather:
                sensor_data.append(
                    APRSWSSensorData(
                        timestamp=timestamp,
                        callsign=callsign,
                        type="illuminance",
                        value=weather["luminosity"],
                    )
                )

        return sensor_data
