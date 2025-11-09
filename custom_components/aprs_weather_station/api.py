"""Sample API Client."""

from __future__ import annotations

from typing import TYPE_CHECKING

import aprslib

from .aprs_listener import APRSListener
from .const import APRSIS_FULL_FEED_PORT, APRSIS_USER_DEFINED_PORT, LOGGER

if TYPE_CHECKING:
    from collections.abc import Callable


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
        except Exception as ex:
            msg = f"Something wrong! - {ex}"
            raise APRSWSApiClientCommunicationError(msg) from ex

    def start_listening(self, callback: Callable[[dict[str, str]]]) -> None:
        """Start listening to APRS packet."""
        LOGGER.debug(
            "start_listening with budlist: %s", self._gen_filter_from_budlist()
        )

        self.stop_and_join()

        self._aprs_listener = APRSListener(
            callsign=self._callsign,
            budlist_filter=self._gen_filter_from_budlist(),
            callback=callback,
        )
        self._aprs_listener.start()

    def stop_and_join(self) -> None:
        """Stop and join thread."""
        LOGGER.debug("stop_and_join()")
        if self._aprs_listener:
            self._aprs_listener.stop()
            self._aprs_listener.join()
        LOGGER.debug("stop_and_join() done")
