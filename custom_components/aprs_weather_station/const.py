"""Constants for aprs_weather_station."""

from logging import Logger, getLogger
from typing import Final

LOGGER: Logger = getLogger(__package__)

DOMAIN = "aprs_weather_station"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"

CONF_YOUR_CALLSIGN: Final = "your_callsign"
CONF_CALLSIGN: Final = "callsign"
