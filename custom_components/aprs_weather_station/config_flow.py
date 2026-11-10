"""Adds config flow for Blueprint."""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from slugify import slugify

from .api import (
    APRSWSApiClient,
    APRSWSApiClientAuthenticationError,
    APRSWSApiClientCommunicationError,
    APRSWSApiClientError,
)
from .const import (
    CONF_CALLSIGN,
    CONF_YOUR_CALLSIGN,
    DOMAIN,
    LOGGER,
)

CALLSIGN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,15}$")


def _is_valid_callsign(callsign: str) -> bool:
    """Validate APRS callsign format."""
    return bool(CALLSIGN_PATTERN.match(callsign))


class APRSWSFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls,
        config_entry: config_entries.ConfigEntry,  # noqa: ARG003
    ) -> dict[str, type[config_entries.ConfigSubentryFlow]]:
        """Return subentries supported by this integration."""
        return {"budlist": BudlistSubentryFlowHandler}

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            callsign = user_input[CONF_YOUR_CALLSIGN].strip().upper()
            user_input[CONF_YOUR_CALLSIGN] = callsign
            if not _is_valid_callsign(callsign):
                _errors["base"] = "invalid_callsign"
            else:
                try:
                    await _test_connect(self.hass, callsign=callsign)
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
                    await self.async_set_unique_id(unique_id=slugify(callsign))
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=callsign,
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
                },
            ),
            errors=_errors,
            description_placeholders={
                "docs_url": "https://aprs-python.readthedocs.io/en/stable/examples.html#aprs-is"
            },
        )


class BudlistSubentryFlowHandler(config_entries.ConfigSubentryFlow):
    """Budlist Subentry."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.SubentryFlowResult:
        """Subentry user flow."""
        config_entry = self._get_entry()
        if config_entry.state is not config_entries.ConfigEntryState.LOADED:
            return self.async_abort(reason="config_entry_disabled")

        _errors = {}
        if user_input is not None:
            callsign = user_input[CONF_CALLSIGN].strip().upper()
            user_input[CONF_CALLSIGN] = callsign
            existing_callsigns = {
                subentry.data[CONF_CALLSIGN].upper()
                for subentry in config_entry.subentries.values()
            }
            if not _is_valid_callsign(callsign):
                _errors["base"] = "invalid_callsign"
            elif callsign in existing_callsigns:
                return self.async_abort(reason="already_configured")
            else:
                try:
                    await _test_connect(
                        self.hass,
                        callsign=config_entry.data[CONF_YOUR_CALLSIGN],
                        budlist=[callsign],
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
                    return self.async_create_entry(
                        title=callsign,
                        data=user_input,
                        unique_id=callsign,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CALLSIGN,
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )


async def _test_connect(
    hass: HomeAssistant, callsign: str, budlist: list[str] | None = None
) -> None:
    """Test connection."""
    client = APRSWSApiClient(
        callsign=callsign,
        budlist=budlist,
    )
    await hass.async_add_executor_job(client.test_connection)
