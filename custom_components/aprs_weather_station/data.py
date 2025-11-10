"""Custom types for aprs_weather_station."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import APRSWSApiClient
    from .coordinator import APRSWSDataUpdateCoordinator


type APRSWSConfigEntry = ConfigEntry[APRSWSRuntimeData]


@dataclass
class APRSWSRuntimeData:
    """Data for the APRS Weather Station."""

    client: APRSWSApiClient
    coordinator: APRSWSDataUpdateCoordinator
    integration: Integration


@dataclass(frozen=True)
class APRSWSSensorData:
    """Base class for sensor data."""

    timestamp: int
    callsign: str
    type: str

    value: str | int | float | datetime | None

    @classmethod
    def from_other_with_new_value(
        cls, other: APRSWSSensorData, value: str | float | datetime | None
    ) -> APRSWSSensorData:
        """Create copy with new value."""
        return APRSWSSensorData(
            timestamp=other.timestamp,
            callsign=other.callsign,
            type=other.type,
            value=value,
        )

    @property
    def key(self) -> str:
        """Unique key for sensor."""
        return f"{self.callsign}_{self.type}"
