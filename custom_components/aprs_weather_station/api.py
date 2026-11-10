"""Sample API Client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import aprslib

from .aprs_listener import APRSListener
from .const import APRSIS_FULL_FEED_PORT, APRSIS_USER_DEFINED_PORT, LOGGER

if TYPE_CHECKING:
    from collections.abc import Callable

STOP_JOIN_TIMEOUT = 10  # seconds


class APRSWSApiClientError(Exception):
    """Exception to indicate a general API error."""


class APRSWSApiClientCommunicationError(
    APRSWSApiClientError,
):
    """Exception to indicate a communication error."""


class APRSWSApiClientAuthenticationError(
    APRSWSApiClientError,
):
    """Exception to indicate an authentication error."""


class APRSWSApiClient:
    """APRSWS API Client."""

    def __init__(
        self,
        callsign: str,
        budlist: list[str] | None,
    ) -> None:
        """APRSWS API Client."""
        self._callsign = callsign
        self.budlist = budlist
        self._aprs_listener: APRSListener | None = None

    def _gen_filter_from_budlist(self) -> str | None:
        if not self.budlist:
            return None
        replace = "/".join(self.budlist)
        return f"b/{replace}"

    def test_connection(self) -> None:
        """Test connection to APRS-IS server."""
        ais_filter = self._gen_filter_from_budlist()
        port = APRSIS_USER_DEFINED_PORT if self.budlist else APRSIS_FULL_FEED_PORT
        LOGGER.info(
            "Test connection with: callsign=%s port=%s budlist=%s",
            self._callsign,
            port,
            ais_filter,
        )
        try:
            ais = aprslib.IS(self._callsign, port=port)
            if ais_filter is not None:
                ais.set_filter(ais_filter)
            ais.connect()
            ais.close()
        except aprslib.exceptions.LoginError as ex:
            msg = f"Authentication failed: {ex}"
            raise APRSWSApiClientAuthenticationError(msg) from ex
        except Exception as ex:
            msg = f"Something wrong! - {ex}"
            raise APRSWSApiClientCommunicationError(msg) from ex

    def start_listening(
        self,
        callback: Callable[[dict[str, Any]], None],
        status_callback: Callable[[bool], None] | None = None,
    ) -> None:
        """Start listening to APRS packet."""
        LOGGER.debug(
            "start_listening with budlist: %s", self._gen_filter_from_budlist()
        )

        self.stop_and_join()

        self._aprs_listener = APRSListener(
            callsign=self._callsign,
            budlist_filter=self._gen_filter_from_budlist(),
            callback=callback,
            status_callback=status_callback,
        )
        self._aprs_listener.start()

    def is_listening(self) -> bool:
        """Return if aprs listener thread is active."""
        return self._aprs_listener is not None and self._aprs_listener.is_alive()

    def is_connected(self) -> bool:
        """Return if aprs client is connected."""
        return bool(self._aprs_listener and self._aprs_listener.is_connected())

    def stop_and_join(self) -> None:
        """Stop and join thread."""
        LOGGER.debug("stop_and_join()")
        if self._aprs_listener:
            self._aprs_listener.stop()
            self._aprs_listener.join(timeout=STOP_JOIN_TIMEOUT)
            if self._aprs_listener.is_alive():
                LOGGER.warning("APRS listener thread did not stop in time")
            self._aprs_listener = None
        LOGGER.debug("stop_and_join() done")
