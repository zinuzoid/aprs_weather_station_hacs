"""APRSListener thread."""

import threading
import time
from collections.abc import Callable
from typing import Any

import aprslib
import aprslib.exceptions

from .const import LOGGER

FAKE_DATA = {
    "raw": "G4ZMG>APRS,TCPIP*,qAC,T2SPAIN:@090150z5205.65N/00219.62W_175/003g008t048r000p001P000h94b10139L000.WFL",
    "from": "G4ZMG",
    "to": "APRS",
    "path": ["TCPIP*", "qAC", "T2SPAIN"],
    "via": "T2SPAIN",
    "messagecapable": True,
    "raw_timestamp": "090150z",
    "timestamp": 1762653000,
    "format": "uncompressed",
    "posambiguity": 0,
    "symbol": "_",
    "symbol_table": "/",
    "latitude": 52.094166666666666,
    "longitude": -2.327,
    "course": 175,
    "speed": 5.556,
    "comment": ".WFL",
    "weather": {
        "wind_gust": 3.57632,
        "temperature": 8.88888888888889,
        "rain_1h": 0.0,
        "rain_24h": 0.254,
        "rain_since_midnight": 0.0,
        "humidity": 94,
        "pressure": 1013.9,
        "luminosity": 0,
    },
}


class APRSListener(threading.Thread):
    """A threaded APRS-IS listener that receives packets and routes them to callbacks."""

    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds

    SEND_FAKE_DATA = True

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
            self._consumer_callback(FAKE_DATA)

        try:
            # Proceed with normal connection with retry logic
            self._connect_with_retry()

            if self._budlist_filter:
                self._ais.set_filter(self._budlist_filter)
            self._ais.consumer(self._consumer_callback)
        except ValueError as e:
            # Socket was closed (file descriptor is -1), this is expected when stopping
            LOGGER.warning("Consumer stopped: %s", e)
        except (OSError, ConnectionError, aprslib.exceptions.GenericError) as e:
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
