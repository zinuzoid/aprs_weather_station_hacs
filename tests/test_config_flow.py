"""Tests for APRS Weather Station config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import aprslib
import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.aprs_weather_station.api import (
    APRSWSApiClient,
    APRSWSApiClientAuthenticationError,
    APRSWSApiClientCommunicationError,
)
from custom_components.aprs_weather_station.config_flow import (
    APRSWSFlowHandler,
    BudlistSubentryFlowHandler,
    _is_valid_callsign,
    _test_connect,
)
from custom_components.aprs_weather_station.const import (
    CONF_CALLSIGN,
    CONF_YOUR_CALLSIGN,
)


def test_callsign_validation() -> None:
    """Test callsign format validation."""
    assert _is_valid_callsign("N0CALL")
    assert _is_valid_callsign("W3ADO-1")
    assert _is_valid_callsign("g4zmg")
    assert _is_valid_callsign("WX_BOS")
    assert not _is_valid_callsign("")
    assert not _is_valid_callsign("CALL SIGN")
    assert not _is_valid_callsign("TOOLONGCALLSIGN12345")
    assert not _is_valid_callsign("INVALID!@#")


@pytest.mark.asyncio
async def test_test_connect_uses_executor() -> None:
    """Test _test_connect runs test_connection via executor (Item 1)."""
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(return_value=None)

    with patch(
        "custom_components.aprs_weather_station.config_flow.APRSWSApiClient"
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        await _test_connect(hass, callsign="N0CALL", budlist=["W3ADO-1"])

        mock_client_cls.assert_called_once_with(callsign="N0CALL", budlist=["W3ADO-1"])
        hass.async_add_executor_job.assert_called_once_with(mock_client.test_connection)


@pytest.mark.asyncio
async def test_flow_user_step_normalizes_callsign() -> None:
    """Test that main config flow strips and uppercases callsign (Item 10)."""
    flow = APRSWSFlowHandler()
    flow.hass = MagicMock()
    flow.hass.async_add_executor_job = AsyncMock(return_value=None)
    flow.async_set_unique_id = AsyncMock(return_value=None)
    flow._abort_if_unique_id_configured = MagicMock()

    result = await flow.async_step_user({CONF_YOUR_CALLSIGN: "  n0call  "})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "N0CALL"
    assert result["data"][CONF_YOUR_CALLSIGN] == "N0CALL"
    flow.async_set_unique_id.assert_called_once_with(unique_id="n0call")


@pytest.mark.asyncio
async def test_flow_user_step_invalid_callsign() -> None:
    """Test that main config flow rejects invalid callsign format."""
    flow = APRSWSFlowHandler()
    flow.hass = MagicMock()

    result = await flow.async_step_user({CONF_YOUR_CALLSIGN: "INVALID CALL!"})

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_callsign"


@pytest.mark.asyncio
async def test_flow_user_step_connection_error() -> None:
    """Test handling connection error in main flow."""
    flow = APRSWSFlowHandler()
    flow.hass = MagicMock()
    flow.hass.async_add_executor_job = AsyncMock(
        side_effect=APRSWSApiClientCommunicationError("Conn failed")
    )

    result = await flow.async_step_user({CONF_YOUR_CALLSIGN: "N0CALL"})

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "connection"


@pytest.mark.asyncio
async def test_flow_user_step_auth_error() -> None:
    """Test handling auth error in main flow (Item 14)."""
    flow = APRSWSFlowHandler()
    flow.hass = MagicMock()
    flow.hass.async_add_executor_job = AsyncMock(
        side_effect=APRSWSApiClientAuthenticationError("Auth failed")
    )

    result = await flow.async_step_user({CONF_YOUR_CALLSIGN: "N0CALL"})

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "auth"


def test_api_client_test_connection_maps_login_error() -> None:
    """Test that APRSWSApiClient.test_connection maps LoginError (Item 14)."""
    client = APRSWSApiClient(callsign="N0CALL", budlist=None)
    with patch("aprslib.IS") as mock_is_cls:
        mock_is = MagicMock()
        mock_is.connect.side_effect = aprslib.exceptions.LoginError("Invalid passcode")
        mock_is_cls.return_value = mock_is

        with pytest.raises(
            APRSWSApiClientAuthenticationError, match="Invalid passcode"
        ):
            client.test_connection()


@pytest.mark.asyncio
async def test_subentry_flow_normalizes_and_checks_duplicates() -> None:
    """Test that subentry flow normalizes callsign and rejects duplicates (Item 10)."""
    flow = BudlistSubentryFlowHandler()
    flow.hass = MagicMock()
    flow.hass.async_add_executor_job = AsyncMock(return_value=None)

    existing_subentry = MagicMock()
    existing_subentry.data = {CONF_CALLSIGN: "W3ADO-1"}

    mock_entry = MagicMock()
    mock_entry.state = config_entries.ConfigEntryState.LOADED
    mock_entry.data = {CONF_YOUR_CALLSIGN: "N0CALL"}
    mock_entry.subentries = {"sub1": existing_subentry}
    flow._get_entry = MagicMock(return_value=mock_entry)
    flow.context = {"source": config_entries.SOURCE_USER}

    # Adding duplicate in different case should abort
    result_dup = await flow.async_step_user({CONF_CALLSIGN: "  w3ado-1  "})
    assert result_dup["type"] is FlowResultType.ABORT
    assert result_dup["reason"] == "already_configured"

    # Adding new callsign in lowercase should normalize to uppercase
    result_new = await flow.async_step_user({CONF_CALLSIGN: "  g4zmg  "})
    assert result_new["type"] is FlowResultType.CREATE_ENTRY
    assert result_new["title"] == "G4ZMG"
    assert result_new["data"][CONF_CALLSIGN] == "G4ZMG"
