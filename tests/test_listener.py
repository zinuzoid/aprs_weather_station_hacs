"""Tests for APRSListener thread and reconnect logic."""

from unittest.mock import MagicMock

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
