"""APRSListener thread."""

import threading
import time
from collections.abc import Callable
from typing import Any

import aprslib
import aprslib.exceptions

from .const import LOGGER

FAKE_DATA1 = {
    "raw": "G4ZMG>APRS,TCPIP*,qAC,T2SYDNEY:@100100z5205.65N/00219.62W_202/008g013t054r001p021P001h98b10038L000.WFL",  # noqa: E501
    "from": "G4ZMG",
    "to": "APRS",
    "path": ["TCPIP*", "qAC", "T2SYDNEY"],
    "via": "T2SYDNEY",
    "messagecapable": True,
    "raw_timestamp": "100100z",
    "timestamp": 1762736400,
    "format": "uncompressed",
    "posambiguity": 0,
    "symbol": "_",
    "symbol_table": "/",
    "latitude": 52.094166666666666,
    "longitude": -2.327,
    "course": 202,
    "speed": 14.816,
    "comment": ".WFL",
    "weather": {
        "wind_gust": 5.81152,
        "temperature": 12.222222222222221,
        "rain_1h": 0.254,
        "rain_24h": 5.334,
        "rain_since_midnight": 0.254,
        "humidity": 98,
        "pressure": 1003.8,
        "luminosity": 0,
    },
}

FAKE_DATA2 = {
    "raw": "G8PZT>APXR04,qAO,G6JVY-10:@101119/5224.00N/00215.00W_000/000g000t050r000p000P028h83b0000 Kidderminster, UK {XrPi}",  # noqa: E501
    "from": "G8PZT",
    "to": "APXR04",
    "path": ["qAO", "G6JVY-10"],
    "via": "G6JVY-10",
    "messagecapable": True,
    "raw_timestamp": "101119/",
    "timestamp": 1762773540,
    "format": "uncompressed",
    "posambiguity": 0,
    "symbol": "_",
    "symbol_table": "/",
    "latitude": 52.4,
    "longitude": -2.25,
    "comment": "Kidderminster, UK {XrPi}",
    "weather": {
        "wind_direction": 0,
        "wind_speed": 0.0,
        "wind_gust": 0.0,
        "temperature": 10.0,
        "rain_1h": 0.0,
        "rain_24h": 0.0,
        "rain_since_midnight": 7.112,
        "humidity": 83,
    },
}


class APRSListener(threading.Thread):
    """APRS-IS listener thread that receives packets and routes them to callbacks."""

    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds

    SEND_FAKE_DATA = False

    def __init__(
        self,
        callsign: str,
        budlist_filter: str | None,
        callback: Callable[[dict[str, Any]], None] | None,
    ) -> None:
        """Initialize the APRS listener."""
        super().__init__()
        self._callsign = callsign
        self._budlist_filter = budlist_filter
        self._callback = callback
        self._ais = aprslib.IS(
            self._callsign, port=10152 if budlist_filter is None else 14580
        )

    def __del__(self) -> None:
        """Destructor to ensure connection is closed."""
        self.stop()

    def _consumer_callback(self, packet: dict[str, Any]) -> None:
        """Handle incoming APRS-IS packets."""
        if self._callback:
            self._callback(packet)

    def _connect_with_retry(self) -> None:
        """Connect to APRS-IS with retry logic."""
        for attempt in range(self.MAX_RETRIES):
            try:
                self._ais.connect()
                break  # Connection successful, exit retry loop
            except (aprslib.exceptions.LoginError, ConnectionError) as e:
                if attempt < self.MAX_RETRIES - 1:
                    LOGGER.warning(
                        "Connection attempt %d/%d failed: %s. Retrying in %d seconds.",
                        attempt + 1,
                        self.MAX_RETRIES,
                        e,
                        self.RETRY_DELAY,
                    )
                    time.sleep(self.RETRY_DELAY)
                else:
                    LOGGER.error(
                        "Connection failed after %d attempts: %s", self.MAX_RETRIES, e
                    )
                    raise

    def run(self) -> None:
        """Thread entry point - connects to APRS-IS and starts consuming packets."""
        if self.SEND_FAKE_DATA:
            # Send fake data after 3 seconds for testing
            time.sleep(3)
            self._consumer_callback(FAKE_DATA1)
            self._consumer_callback(FAKE_DATA2)

        try:
            # Proceed with normal connection with retry logic
            self._connect_with_retry()

            if self._budlist_filter:
                self._ais.set_filter(self._budlist_filter)
            self._ais.consumer(self._consumer_callback)
        except (
            OSError,
            ValueError,
            ConnectionError,
            aprslib.exceptions.GenericError,
        ) as e:
            # Connection failed or socket was closed from main thread
            LOGGER.exception(e)
        except Exception as e:  # noqa: BLE001
            # Catch all other exceptions to prevent thread from hanging
            LOGGER.error(
                "Unexpected error in APRS listener thread: %s", e, exc_info=True
            )
        finally:
            self.stop()

    def stop(self) -> None:
        """Signal the listener to stop and close the connection."""
        LOGGER.debug("stop()")
        if self.is_connected():
            self._ais.close()
        LOGGER.debug("stop() done")

    def is_connected(self) -> bool:
        """Check if the APRS-IS connection is active."""
        return self._ais._connected  # noqa: SLF001
