"""Tests for APRS Weather Station config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.data_entry_flow import FlowResultType

from custom_components.aprs_weather_station.api import (
    APRSWSApiClientCommunicationError,
)
from custom_components.aprs_weather_station.config_flow import (
    APRSWSFlowHandler,
    _test_connect,
)
from custom_components.aprs_weather_station.const import CONF_YOUR_CALLSIGN


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
