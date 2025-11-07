"""Adds config flow for Blueprint."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PORT
from homeassistant.helpers import selector
from slugify import slugify

from .api import (
    APRSWSApiClient,
    APRSWSApiClientAuthenticationError,
    APRSWSApiClientCommunicationError,
    APRSWSApiClientError,
)
from .const import CONF_BUDLIST_FILTER, CONF_YOUR_CALLSIGN, DOMAIN, LOGGER


class APRSWSFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            user_input[CONF_PORT] = int(user_input[CONF_PORT])
            try:
                await self._test_connect(
                    callsign=user_input[CONF_YOUR_CALLSIGN],
                    port=user_input[CONF_PORT],
                    budlist=user_input[CONF_BUDLIST_FILTER],
                )
            except APRSWSApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except APRSWSApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except APRSWSApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    unique_id=slugify(
                        user_input[CONF_YOUR_CALLSIGN]
                        + str(user_input[CONF_PORT])
                        + user_input[CONF_BUDLIST_FILTER]
                    )
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_BUDLIST_FILTER],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_YOUR_CALLSIGN,
                        default=(user_input or {}).get(CONF_YOUR_CALLSIGN, "N0CALL"),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(
                        CONF_PORT, default=(user_input or {}).get(CONF_PORT, 14580)
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX, min=1, max=65535
                        )
                    ),
                    vol.Required(CONF_BUDLIST_FILTER): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                    ),
                },
            ),
            errors=_errors,
        )

    async def _test_connect(self, callsign: str, port: int, budlist: str) -> None:
        """Test connection."""
        client = APRSWSApiClient(
            callsign=callsign,
            port=port,
            budlist=budlist,
        )
        client.test_connection()
