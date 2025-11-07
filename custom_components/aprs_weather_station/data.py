"""Custom types for aprs_weather_station."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import APRSWSApiClient
    from .coordinator import APRSWSDataUpdateCoordinator


type APRSWSConfigEntry = ConfigEntry[APRSWSData]


@dataclass
class APRSWSData:
    """Data for the APRS Weather Station."""

    client: APRSWSApiClient
    coordinator: APRSWSDataUpdateCoordinator
    integration: Integration
