"""Diagnostics support for aprs_weather_station."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data

from .const import CONF_CALLSIGN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import APRSWSConfigEntry

TO_REDACT: set[str] = set()


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: APRSWSConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator
    client = entry.runtime_data.client

    subentries_info = [
        {
            "subentry_id": subentry.subentry_id,
            "callsign": subentry.data.get(CONF_CALLSIGN),
        }
        for subentry in entry.subentries.values()
    ]

    sensors_info = {
        key: {
            "callsign": sensor.callsign,
            "type": sensor.type,
            "value": sensor.value,
            "timestamp": sensor.timestamp,
        }
        for key, sensor in coordinator.data.items()
    }

    return {
        "entry": {
            "entry_id": entry.entry_id,
            "domain": entry.domain,
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "subentries": subentries_info,
        },
        "connection": {
            "is_connected": client.is_connected(),
            "is_listening": client.is_listening(),
            "budlist": client.budlist,
        },
        "coordinator": {
            "sensor_count": len(coordinator.data),
            "sensors": sensors_info,
        },
    }
