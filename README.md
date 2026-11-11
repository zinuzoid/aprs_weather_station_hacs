# APRS Weather Station for Home Assistant

[![Tests](https://github.com/zinuzoid/aprs_weather_station_hacs/actions/workflows/tests.yml/badge.svg)](https://github.com/zinuzoid/aprs_weather_station_hacs/actions/workflows/tests.yml)
[![Lint](https://github.com/zinuzoid/aprs_weather_station_hacs/actions/workflows/lint.yml/badge.svg)](https://github.com/zinuzoid/aprs_weather_station_hacs/actions/workflows/lint.yml)
[![Validate](https://github.com/zinuzoid/aprs_weather_station_hacs/actions/workflows/validate.yml/badge.svg)](https://github.com/zinuzoid/aprs_weather_station_hacs/actions/workflows/validate.yml)
[![HACS Default](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Home Assistant custom integration for receiving and monitoring real-time weather reports and station locations from the amateur radio **APRS-IS** (Automatic Packet Reporting System Internet Service) network.

---

## What is APRS?

**APRS** (Automatic Packet Reporting System) is an amateur radio-based digital communications system widely used for transmitting real-time tactical information, including GPS coordinates and weather station telemetry. Weather stations worldwide—ranging from Citizen Weather Observer Program (CWOP) stations to personal ham radio weather stations and mobile trackers—transmit weather data packets over RF and the APRS-IS network.

This integration connects directly to the APRS-IS network, filtering for only the stations you choose, and pushes weather observations into Home Assistant as soon as they are received.

---

## Features

- **Real-Time Push Updates (`cloud_push`)**: Connects directly to APRS-IS servers; observations update the moment a station transmits a packet.
- **Multi-Station Support (Subentries)**: Monitor one or many weather stations under a single APRS-IS connection.
- **Non-Blocking Architecture**: All socket connections and worker threads run asynchronously via executors, keeping Home Assistant's event loop fast and responsive.
- **Automatic Reconnection**: Built-in exponential backoff automatically reconnects if the APRS-IS server drops.
- **Automatic Entity Discovery**: Sensors and device trackers are created automatically when the first packet from each configured station arrives.
- **Rich Sensor Metadata**: Uses standard Home Assistant device classes, state classes, units of measurement, and icons.
- **Device Tracker Support**: Automatically tracks mobile or fixed weather station GPS coordinates on your Home Assistant map.
- **Diagnostics**: Built-in diagnostics platform to inspect connection state, budlist filters, and received telemetry.

---

## Installation

### Method 1: HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed and running in your Home Assistant instance.
2. In Home Assistant, open **HACS** > **Integrations**.
3. Click the three dots (`⋮`) in the top right corner and select **Custom repositories**.
4. Enter the repository details:
   - **Repository**: `https://github.com/zinuzoid/aprs_weather_station_hacs`
   - **Type**: `Integration`
5. Click **Add**, find **APRS Weather Station**, and click **Download**.
6. Restart Home Assistant to load the new integration.

### Method 2: Manual Installation

1. Download the latest release from the [GitHub Releases](https://github.com/zinuzoid/aprs_weather_station_hacs/releases) page.
2. Copy the `custom_components/aprs_weather_station` folder into your Home Assistant configuration directory under `config/custom_components/aprs_weather_station`.
3. Restart Home Assistant.

---

## Configuration Walkthrough

### Step 1: Add the Integration (Main Entry)

1. In Home Assistant, navigate to **Settings** > **Devices & Services**.
2. Click **Add Integration** in the bottom right.
3. Search for **APRS Weather Station** and select it.
4. Enter **Your Callsign**:
   - If you have an amateur radio license, enter your callsign (e.g., `N0CALL` or `W3ADO`).
   - If you do not have an amateur radio license, you can enter any identifier or guest callsign.
5. Click **Submit**. This creates the main APRS-IS connection and the **APRS-IS Connection** diagnostic sensor.

### Step 2: Add Weather Stations to Monitor (Subentries)

1. On the **APRS Weather Station** integration card, click **Add weather station**.
2. Enter the **Station Callsign** you wish to monitor (e.g., `W3ADO-1`, `CW1234`, etc.).
   - Callsigns are automatically normalized to uppercase and checked for duplicates.
3. Click **Submit**.
4. Repeat this step for each additional station you want to monitor.

As soon as a monitored station broadcasts an APRS packet, Home Assistant will create a dedicated device for that station along with its weather sensors and location tracker.

---

## Supported Entities

### Weather & Telemetry Sensors

| Sensor Type | Entity Name | Device Class | State Class | Unit | Source |
|-------------|-------------|--------------|-------------|------|--------|
| **temperature** | Temperature | `temperature` | `measurement` | °C | `weather["temperature"]` |
| **humidity** | Humidity | `humidity` | `measurement` | % | `weather["humidity"]` |
| **atmospheric_pressure** | Atmospheric Pressure | `atmospheric_pressure` | `measurement` | hPa | `weather["pressure"]` |
| **wind_speed** | Wind Speed | `wind_speed` | `measurement` | m/s | `weather["wind_speed"]` |
| **wind_direction** | Wind Direction | `wind_direction` | `measurement_angle` | ° | `packet["course"]` |
| **wind_gust** | Wind Gust | `wind_speed` | `measurement` | m/s | `weather["wind_gust"]` |
| **precipitation** | Precipitation | `precipitation` | `measurement` | mm | `weather["rain_1h"]` |
| **illuminance** | Illuminance | `illuminance` | `measurement` | lx | `weather["luminosity"]` |

### Diagnostic Sensors

| Sensor Type | Entity Name | Device Class | Category | Description |
|-------------|-------------|--------------|----------|-------------|
| **is_connected** | Connection | `enum` | Diagnostic | Real-time connection status to APRS-IS server |
| **timestamp** | Last Timestamp | `timestamp` | Diagnostic | Timestamp of the most recently received packet |
| **packet_received** | Packets Received | - | Diagnostic | Counter of packets received during current session |

### Device Tracker

| Platform | Entity Name | Description | Source |
|----------|-------------|-------------|--------|
| **device_tracker** | Location | Latitude and longitude tracking on the Home Assistant map | `packet["latitude"]`, `packet["longitude"]` |

---

## Diagnostics & Troubleshooting

### Enable Debug Logging

If you encounter issues receiving packets or connecting to APRS-IS, enable debug logging by adding the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.aprs_weather_station: debug
```

### Download Diagnostics

1. Go to **Settings** > **Devices & Services**.
2. Find the **APRS Weather Station** entry.
3. Click the three dots menu (`⋮`) and select **Download diagnostics**.
4. The downloaded JSON file includes connection state, registered stations, and the latest sensor payloads (with sensitive tokens scrubbed).

---

## Contributing

Contributions are welcome! Please check out [CONTRIBUTING.md](CONTRIBUTING.md) for local development, testing, and linting instructions.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
