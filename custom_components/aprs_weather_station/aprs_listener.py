"""APRSListener thread."""

import contextlib
import socket
import threading
from collections.abc import Callable
from typing import Any

import aprslib
import aprslib.exceptions

from .const import APRSIS_FULL_FEED_PORT, APRSIS_USER_DEFINED_PORT, LOGGER


class APRSListener(threading.Thread):
    """APRS-IS listener thread that receives packets and routes them to callbacks."""

    MIN_RETRY_DELAY = 5  # seconds
    MAX_RETRY_DELAY = 60  # seconds

    def __init__(  # noqa: PLR0913
        self,
        callsign: str,
        budlist_filter: str | None,
        callback: Callable[[dict[str, Any]], None] | None,
        status_callback: Callable[[bool], None] | None = None,
        *,
        host: str | None = None,
        port: int | None = None,
    ) -> None:
        """Initialize the APRS listener."""
        # Daemon thread so a stuck socket never blocks interpreter exit.
        super().__init__(name="APRSListener", daemon=True)
        self._stop_event = threading.Event()
        self._callsign = callsign
        self._budlist_filter = budlist_filter
        self._callback = callback
        self._status_callback = status_callback
        self._port = (
            port
            if port is not None
            else (
                APRSIS_FULL_FEED_PORT
                if budlist_filter is None
                else APRSIS_USER_DEFINED_PORT
            )
        )
        self._host = host
        kwargs: dict[str, Any] = {"port": self._port}
        if self._host is not None:
            kwargs["host"] = self._host
        self._ais = aprslib.IS(self._callsign, **kwargs)

    @property
    def port(self) -> int:
        """Return the port used by listener."""
        return self._port

    @property
    def host(self) -> str | None:
        """Return the host used by listener."""
        return self._host

    def _consumer_callback(self, packet: dict[str, Any]) -> None:
        """Handle incoming APRS-IS packets."""
        if self._callback:
            self._callback(packet)

    def _notify_status(self, *, connected: bool) -> None:
        """Notify status callback of connection state change."""
        if self._status_callback:
            try:
                self._status_callback(connected)
            except Exception as e:  # noqa: BLE001
                LOGGER.error("Error in APRS status callback: %s", e)

    def _connect(self) -> bool:
        """Attempt to connect to APRS-IS. Return True on success."""
        if self._stop_event.is_set():
            return False
        try:
            self._ais.connect()
        except (
            aprslib.exceptions.LoginError,
            aprslib.exceptions.GenericError,
            ConnectionError,
            OSError,
        ) as e:
            LOGGER.warning("Connection to APRS-IS failed: %s", e)
            self._notify_status(connected=False)
            return False

        if self._stop_event.is_set():
            self._ais.close()
            self._notify_status(connected=False)
            return False

        self._notify_status(connected=True)
        return True

    def run(self) -> None:  # noqa: PLR0912
        """Thread entry point - connects to APRS-IS and starts consuming packets."""
        delay = self.MIN_RETRY_DELAY
        try:
            # Main consumer loop with automatic reconnection and backoff
            while not self._stop_event.is_set():
                if not self._connect():
                    if self._stop_event.is_set():
                        break
                    LOGGER.info(
                        "APRS connection failed. Retrying in %d seconds...", delay
                    )
                    if self._stop_event.wait(delay):
                        break
                    delay = min(delay * 2, self.MAX_RETRY_DELAY)
                    continue

                # Reset backoff delay after successful connection
                delay = self.MIN_RETRY_DELAY

                # Set filter if needed
                if self._budlist_filter:
                    self._ais.set_filter(self._budlist_filter)

                try:
                    self._ais.consumer(self._consumer_callback)
                except aprslib.exceptions.ConnectionDrop as e:
                    if self._stop_event.is_set():
                        break
                    LOGGER.warning("Connection dropped: %s. Reconnecting...", e)
                    self._notify_status(connected=False)
                except (
                    OSError,
                    ConnectionError,
                    aprslib.exceptions.GenericError,
                ) as e:
                    if self._stop_event.is_set():
                        break
                    LOGGER.warning("Connection error: %s. Reconnecting...", e)
                    self._notify_status(connected=False)
                finally:
                    if self.is_connected():
                        self._ais.close()
        except Exception as e:  # noqa: BLE001
            # Catch all other exceptions to prevent thread from hanging
            LOGGER.error(
                "Unexpected error in APRS listener thread: %s", e, exc_info=True
            )
        finally:
            self.stop()
            self._notify_status(connected=False)

    def stop(self) -> None:
        """Signal the listener to stop and close the connection."""
        LOGGER.debug("stop()")
        self._stop_event.set()
        sock = getattr(self._ais, "sock", None)
        if sock is not None:
            # shutdown() wakes up a select()/recv() blocked in the listener
            # thread; close() alone does not on Linux.
            with contextlib.suppress(OSError):
                sock.shutdown(socket.SHUT_RDWR)
        # Let the listener thread close its own socket on exit, closing it
        # underneath a running select()/recv() only produces noisy errors.
        if (
            not self.is_alive() or threading.current_thread() is self
        ) and self.is_connected():
            self._ais.close()
        LOGGER.debug("stop() done")

    def is_connected(self) -> bool:
        """Check if the APRS-IS connection is active."""
        return bool(getattr(self._ais, "_connected", False))
