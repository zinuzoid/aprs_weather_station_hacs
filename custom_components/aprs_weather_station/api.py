"""Sample API Client."""

from __future__ import annotations

import aprslib

from .const import LOGGER


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
        port: int,
        budlist: str,
    ) -> None:
        """APRSWS API Client."""
        self._callsign = callsign
        self._port = port
        self._budlist = budlist

    def _gen_filter_from_budlist(self) -> str:
        replace = self._budlist.strip().replace(",", "/")
        return f"b/{replace}"

    def test_connection(self) -> None:
        """Test connection to APRS-IS server."""
        ais_filter = self._gen_filter_from_budlist()
        LOGGER.info(
            "Test connection with: callsign=%s port=%d budlist=%s",
            self._callsign,
            self._port,
            ais_filter,
        )
        try:
            ais = aprslib.IS(self._callsign, port=self._port)
            ais.set_filter(ais_filter)
            ais.connect(retry=5)
            ais.close()
        except Exception as ex:
            msg = f"Something wrong! - {ex}"
            raise APRSWSApiClientCommunicationError(msg) from ex
