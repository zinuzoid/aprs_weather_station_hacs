"""APRS packet parser for extracting sensor data."""

from typing import Any

from .data import APRSWSSensorData


class APRSPacketParser:
    """Parser for APRS packets to extract sensor data."""

    def parse(self, packet: dict[str, Any]) -> list[APRSWSSensorData]:
        """Parse an APRS packet and extract sensor data."""
        sensor_data: list[APRSWSSensorData] = []
        timestamp = packet.get("timestamp", 0)
        callsign = packet.get("from", "")

        # Parse weather data if available
        weather = packet.get("weather")
        if weather:
            if "wind_gust" in weather:
                sensor_data.append(
                    APRSWSSensorData(
                        timestamp=timestamp,
                        callsign=callsign,
                        type="wind_speed",
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
