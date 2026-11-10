"""Tests for APRSListener thread and reconnect logic."""

from unittest.mock import MagicMock

from custom_components.aprs_weather_station.api import APRSWSApiClient
from custom_components.aprs_weather_station.aprs_listener import APRSListener


def test_listener_stop_unblocks_and_closes() -> None:
    """Test stop closes connection and sets stop event (Item 2)."""
    listener = APRSListener(
        callsign="N0CALL",
        budlist_filter=None,
        callback=lambda _: None,
    )
    mock_ais = MagicMock()
    mock_sock = MagicMock()
    mock_ais.sock = mock_sock
    mock_ais._connected = True
    listener._ais = mock_ais

    listener.stop()

    assert listener._stop_event.is_set()
    mock_sock.shutdown.assert_called_once()
    mock_ais.close.assert_called_once()
    assert listener.is_connected() is True


def test_api_client_is_listening_and_is_connected() -> None:
    """Test APRSWSApiClient is_listening and is_connected helpers (Items 3, 6)."""
    client = APRSWSApiClient(callsign="N0CALL", budlist=["W3ADO-1"])
    assert client.is_listening() is False
    assert client.is_connected() is False

    mock_listener = MagicMock()
    mock_listener.is_alive.return_value = True
    mock_listener.is_connected.return_value = True
    client._aprs_listener = mock_listener

    assert client.is_listening() is True
    assert client.is_connected() is True

    mock_listener.is_alive.return_value = False
    assert client.is_listening() is False
