"""Tests for APRSListener thread and reconnect logic."""

from unittest.mock import MagicMock

from custom_components.aprs_weather_station.api import APRSWSApiClient
from custom_components.aprs_weather_station.aprs_listener import APRSListener
from custom_components.aprs_weather_station.aprs_parser import APRSPacketParser
from tests.fixtures.packets import FAKE_DATA1, FAKE_DATA2


def test_listener_status_callback_called_on_connect_and_disconnect() -> None:
    """Test APRSListener notifies status_callback on connect/disconnect."""
    status_calls: list[bool] = []

    listener = APRSListener(
        callsign="N0CALL",
        budlist_filter="b/W3ADO-1",
        callback=lambda _: None,
        status_callback=status_calls.append,
    )

    mock_ais = MagicMock()
    listener._ais = mock_ais

    # Test _connect success
    assert listener._connect() is True
    assert status_calls[-1] is True

    # Test _connect failure
    mock_ais.connect.side_effect = ConnectionError("Network down")
    assert listener._connect() is False
    assert status_calls[-1] is False


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


def test_fixtures_packets_parse() -> None:
    """Test packet fixtures moved to tests/fixtures/ parse properly (Item 26)."""
    parser = APRSPacketParser()

    sensors1 = parser.parse(FAKE_DATA1)
    types1 = {s.type for s in sensors1}
    assert "temperature" in types1
    assert "location" in types1
    assert "humidity" in types1

    sensors2 = parser.parse(FAKE_DATA2)
    types2 = {s.type for s in sensors2}
    assert "temperature" in types2
    assert "location" in types2
