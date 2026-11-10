"""Tests for integration setup and unload."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from custom_components.aprs_weather_station import (
    async_setup_entry,
    async_unload_entry,
)
from custom_components.aprs_weather_station.api import (
    APRSWSApiClientAuthenticationError,
    APRSWSApiClientCommunicationError,
)
from custom_components.aprs_weather_station.const import (
    CONF_YOUR_CALLSIGN,
    DOMAIN,
    SENSOR_TYPE_TO_MDI_ICONS,
)


@pytest.mark.asyncio
async def test_async_setup_entry_raises_config_entry_not_ready() -> None:
    """Test async_setup_entry raises ConfigEntryNotReady on conn failure (Item 18)."""
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(
        side_effect=APRSWSApiClientCommunicationError("APRS-IS server down")
    )

    entry = MagicMock()
    entry.domain = DOMAIN
    entry.data = {CONF_YOUR_CALLSIGN: "N0CALL"}

    with pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(hass, entry)


@pytest.mark.asyncio
async def test_async_setup_entry_raises_config_entry_auth_failed() -> None:
    """Test async_setup_entry raises ConfigEntryAuthFailed on auth failure (Item 18)."""
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(
        side_effect=APRSWSApiClientAuthenticationError("Bad credentials")
    )

    entry = MagicMock()
    entry.domain = DOMAIN
    entry.data = {CONF_YOUR_CALLSIGN: "N0CALL"}

    with pytest.raises(ConfigEntryAuthFailed):
        await async_setup_entry(hass, entry)


@pytest.mark.asyncio
async def test_async_setup_and_unload_entry_success() -> None:
    """Test successful setup and unload flow."""
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(return_value=None)
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    entry = MagicMock()
    entry.domain = DOMAIN
    entry.entry_id = "test_entry"
    entry.data = {CONF_YOUR_CALLSIGN: "N0CALL"}

    with (
        patch("custom_components.aprs_weather_station.async_get_loaded_integration"),
        patch(
            "custom_components.aprs_weather_station.coordinator.APRSWSDataUpdateCoordinator.async_config_entry_first_refresh",
            new_callable=AsyncMock,
        ),
    ):
        result = await async_setup_entry(hass, entry)
        assert result is True
        assert entry.runtime_data is not None

        unload_result = await async_unload_entry(hass, entry)
        assert unload_result is True


def test_icons_json_valid_and_complete() -> None:
    """Test icons.json defines icons for all sensor types (Item 24)."""
    icons_path = (
        Path(__file__).parent.parent
        / "custom_components"
        / "aprs_weather_station"
        / "icons.json"
    )
    assert icons_path.exists()
    icons = json.loads(icons_path.read_text())

    for sensor_type, expected_icon in SENSOR_TYPE_TO_MDI_ICONS.items():
        if sensor_type == "location":
            tracker_icons = icons["entity"]["device_tracker"]
            assert tracker_icons["location"]["default"] == expected_icon
        else:
            sensor_icons = icons["entity"]["sensor"]
            assert sensor_icons[sensor_type]["default"] == expected_icon


def test_translations_valid_and_complete() -> None:
    """Test strings.json and translations/en.json define all sensors (Item 27)."""
    base = Path(__file__).parent.parent / "custom_components" / "aprs_weather_station"
    strings_path = base / "strings.json"
    en_path = base / "translations" / "en.json"

    assert strings_path.exists()
    assert en_path.exists()

    strings = json.loads(strings_path.read_text())
    en = json.loads(en_path.read_text())

    for data in (strings, en):
        # Auth error shouldn't mention Username/Password
        assert "Username/Password" not in data["config"]["error"]["auth"]
        assert (
            "Username/Password"
            not in data["config_subentries"]["budlist"]["error"]["auth"]
        )

        # All sensors must have translation names
        for sensor_type in SENSOR_TYPE_TO_MDI_ICONS:
            if sensor_type == "location":
                assert "name" in data["entity"]["device_tracker"]["location"]
            else:
                assert "name" in data["entity"]["sensor"][sensor_type]


def test_quality_scale_yaml_valid() -> None:
    """Test quality_scale.yaml exists and has valid rules (Item 33)."""
    qs_path = (
        Path(__file__).parent.parent
        / "custom_components"
        / "aprs_weather_station"
        / "quality_scale.yaml"
    )
    assert qs_path.exists()
    content = yaml.safe_load(qs_path.read_text())
    assert "rules" in content
    assert content["rules"]["test-before-configure"] == "done"
    assert content["rules"]["test-before-setup"] == "done"
    assert content["rules"]["diagnostics"] == "done"
