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
        port: int | None,
        budlist: list[str] | None,
    ) -> None:
        """APRSWS API Client."""
        self._callsign = callsign
        self._port = port
        self.budlist = budlist

    def _gen_filter_from_budlist(self) -> str | None:
        if not self.budlist:
            return None
        replace = "/".join(self.budlist)
        return f"b/{replace}"

    def test_connection(self) -> None:
        """Test connection to APRS-IS server."""
        ais_filter = self._gen_filter_from_budlist()
        LOGGER.info(
            "Test connection with: callsign=%s port=%s budlist=%s",
            self._callsign,
            self._port,
            ais_filter,
        )
        try:
            if self._port is not None:
                ais = aprslib.IS(self._callsign, port=self._port)
            else:
                ais = aprslib.IS(self._callsign)
            if ais_filter is not None:
                ais.set_filter(ais_filter)
            ais.connect(retry=5)
            ais.close()
        except Exception as ex:
            msg = f"Something wrong! - {ex}"
            raise APRSWSApiClientCommunicationError(msg) from ex
