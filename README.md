# APRS Weather Station Listener

A Python library for listening to and parsing APRS (Automatic Packet Reporting System) weather station data, with built-in Home Assistant integration support.

## What is APRS?

APRS is an amateur radio-based system for real-time digital communications of information. This project specifically focuses on receiving and parsing weather station data from the APRS-IS (APRS Internet Service) network.

## Features

- **Real-time APRS packet reception** via APRS-IS network
- **Weather data parsing** from APRS packets into structured sensor data
- **Home Assistant integration** with proper device classes, state classes, and entity categories
- **10 sensor types supported** for comprehensive weather monitoring

## Supported Sensor Types

| Sensor Type | Data Source | Unit | Description |
|-------------|-------------|------|-------------|
| **timestamp** | `packet["timestamp"]` | datetime | Timestamp when the packet was received |
| **message_received** | counter | - | Message reception indicator (value: 1) |
| **wind_speed** | `packet["speed"]` | m/s | Current wind speed |
| **wind_direction** | `packet["course"]` | ° | Wind direction in degrees |
| **wind_gust** | `weather["wind_gust"]` | m/s | Wind gust speed |
| **temperature** | `weather["temperature"]` | °C | Ambient temperature |
| **precipitation** | `weather["rain_1h"]` | mm/h | Rainfall in last hour |
| **humidity** | `weather["humidity"]` | % | Relative humidity |
| **atmospheric_pressure** | `weather["pressure"]` | hPa | Barometric pressure |
| **illuminance** | `weather["luminosity"]` | lx | Light level/brightness |
