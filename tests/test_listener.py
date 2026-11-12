"""Tests for APRSListener thread and reconnect logic."""

from typing import Any
from unittest.mock import MagicMock

import pytest

from custom_components.aprs_weather_station.api import APRSWSApiClient
from custom_components.aprs_weather_station.aprs_listener import APRSListener
from custom_components.aprs_weather_station.aprs_parser import (
    WEATHER_FIELD_TO_SENSOR_TYPE,
    APRSPacketParser,
    parse_aprs_packet,
)
from custom_components.aprs_weather_station.const import (
    APRSIS_FULL_FEED_PORT,
    APRSIS_USER_DEFINED_PORT,
)
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


def test_parse_aprs_packet_table_driven() -> None:
    """Test parse_aprs_packet function and table-driven weather mapping (Item 20)."""
    packet = {
        "from": "W3ADO-1",
        "timestamp": 1700000000,
        "latitude": 38.9876,
        "longitude": -76.5432,
        "course": 270,
        "weather": {
            "wind_speed": 5.5,
            "wind_gust": 8.2,
            "temperature": 21.5,
            "rain_1h": 1.2,
            "humidity": 65,
            "pressure": 1013.2,
            "luminosity": 450,
        },
    }

    sensors = parse_aprs_packet(packet)
    type_map = {s.type: s.value for s in sensors}

    assert type_map["timestamp"] is not None
    assert type_map["packet_received"] == 1
    assert type_map["location"] == (38.9876, -76.5432)
    assert type_map["wind_direction"] == 270

    for field, sensor_type in WEATHER_FIELD_TO_SENSOR_TYPE.items():
        assert sensor_type in type_map
        assert type_map[sensor_type] == packet["weather"][field]


def test_listener_port_constants_and_custom_host_port() -> None:
    """Test APRSListener uses port constants and supports custom host/port (Item 16)."""
    # Default without budlist filter uses full feed port
    listener_full = APRSListener(
        callsign="N0CALL",
        budlist_filter=None,
        callback=lambda _: None,
    )
    assert listener_full.port == APRSIS_FULL_FEED_PORT
    assert listener_full.host is None

    # Default with budlist filter uses user defined port
    listener_user = APRSListener(
        callsign="N0CALL",
        budlist_filter="b/W3ADO-1",
        callback=lambda _: None,
    )
    assert listener_user.port == APRSIS_USER_DEFINED_PORT
    assert listener_user.host is None

    # Custom host and port
    listener_custom = APRSListener(
        callsign="N0CALL",
        budlist_filter="b/W3ADO-1",
        callback=lambda _: None,
        host="rotate.aprs2.net",
        port=14581,
    )
    assert listener_custom.port == 14581
    assert listener_custom.host == "rotate.aprs2.net"


def test_api_client_passes_custom_host_port(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test APRSWSApiClient forwards host and port (Item 16)."""
    client = APRSWSApiClient(
        callsign="N0CALL",
        budlist=["W3ADO-1"],
        host="custom.aprs.net",
        port=14582,
    )
    assert client.host == "custom.aprs.net"
    assert client.port == 14582

    mock_is_calls: list[dict[str, Any]] = []

    def mock_is(callsign: str, **kwargs: Any) -> MagicMock:
        mock_is_calls.append({"callsign": callsign, **kwargs})
        return MagicMock()

    monkeypatch.setattr("aprslib.IS", mock_is)
    client.test_connection()
    assert len(mock_is_calls) == 1
    assert mock_is_calls[0]["host"] == "custom.aprs.net"
    assert mock_is_calls[0]["port"] == 14582
