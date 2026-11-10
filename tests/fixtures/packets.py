"""APRS packet fixtures for testing."""

from typing import Any

FAKE_DATA1: dict[str, Any] = {
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

FAKE_DATA2: dict[str, Any] = {
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
