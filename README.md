# Kerbl Welt Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Home Assistant custom integration for [Kerbl Welt](https://app.kerbl-iot.com) electric fence monitoring system (AKO Smart Satellite).

## Features

- **Automatic Discovery**: Set up via UI with email and password
- **Real-time Monitoring**: Track fence voltage, battery level, and signal quality
- **Multiple Devices**: Support for multiple Smart Satellite devices
- **Event Tracking**: Monitor alert counts
- **Device Information**: View device details in Home Assistant device registry
- **Efficient Updates**: Polls API every 5 minutes by default

## Sensors

For each AKO Smart Satellite device, the following sensors are created:

| Sensor | Description | Unit | Device Class |
|--------|-------------|------|--------------|
| **Fence Voltage** | Current electric fence voltage | V | Voltage |
| **Battery Level** | Device battery percentage | % | Battery |
| **Battery Voltage** | Device battery voltage | V | Voltage |
| **Signal Quality** | Cellular signal strength | % | - |
| **Event Count** | Number of new events/alerts | - | - |

### Sensor Attributes

Each sensor includes additional attributes:

- **Fence Voltage**:
  - `alarm_threshold`: Voltage level that triggers alerts

- **Battery Level**:
  - `battery_voltage`: Raw battery voltage

- **All Sensors**:
  - `device_id`: Device UUID
  - `serial_number`: Device serial number
  - `brand`: Device brand (ako)
  - `registered_at`: Device registration timestamp
  - `last_online`: Last time device was offline (if applicable)

## Installation

### HACS (Recommended - Future)

1. Open HACS
2. Go to "Integrations"
3. Click the three dots in the top right
4. Select "Custom repositories"
5. Add `https://github.com/stgarrity/homeassistant-kerblwelt` as an integration
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/kerblwelt` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Kerbl Welt"
4. Enter your Kerbl Welt account credentials:
   - Email address
   - Password
5. Click **Submit**

Your devices will be automatically discovered and added to Home Assistant!

## Usage

### Viewing Device Data

After setup, your fence monitors will appear in the Devices page:

- Navigate to **Settings** → **Devices & Services** → **Kerbl Welt**
- Click on a device to see all sensors

### Creating Automations

#### Low Voltage Alert

```yaml
automation:
  - alias: "Fence Voltage Low Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.homestead_fence_voltage
        below: 5
    action:
      - service: notify.mobile_app
        data:
          title: "Fence Alert"
          message: "Electric fence voltage is low: {{ states('sensor.homestead_fence_voltage') }}V"
```

#### Low Battery Alert

```yaml
automation:
  - alias: "Fence Monitor Battery Low"
    trigger:
      - platform: numeric_state
        entity_id: sensor.homestead_battery_level
        below: 20
    action:
      - service: notify.mobile_app
        data:
          title: "Battery Alert"
          message: "Fence monitor battery is low: {{ states('sensor.homestead_battery_level') }}%"
```

#### Device Offline Alert

```yaml
automation:
  - alias: "Fence Monitor Offline"
    trigger:
      - platform: state
        entity_id: sensor.homestead_fence_voltage
        to: "unavailable"
        for:
          minutes: 10
    action:
      - service: notify.mobile_app
        data:
          title: "Monitor Offline"
          message: "Fence monitor has gone offline"
```

### Dashboard Card Examples

#### Simple Entity Card

```yaml
type: entities
entities:
  - entity: sensor.homestead_fence_voltage
    name: Fence Voltage
  - entity: sensor.homestead_battery_level
    name: Battery
  - entity: sensor.homestead_signal_quality
    name: Signal
title: Electric Fence Monitor
```

#### Gauge Card for Voltage

```yaml
type: gauge
entity: sensor.homestead_fence_voltage
min: 0
max: 20
severity:
  red: 0
  yellow: 5
  green: 7
needle: true
```

#### Multiple Devices

```yaml
type: vertical-stack
cards:
  - type: horizontal-stack
    cards:
      - type: gauge
        entity: sensor.homestead_fence_voltage
        name: Homestead
        min: 0
        max: 20
      - type: gauge
        entity: sensor.north_pasture_fence_voltage
        name: North Pasture
        min: 0
        max: 20
```

## Troubleshooting

### Integration Not Found

If you don't see "Kerbl Welt" in the integration list:
1. Make sure you copied the files to the correct directory
2. Restart Home Assistant completely
3. Clear your browser cache

### Authentication Failed

If you get "Invalid email or password":
1. Verify your credentials at [app.kerbl-iot.com](https://app.kerbl-iot.com)
2. Make sure you're using your email (not username)
3. Try resetting your password if needed

### Sensors Show "Unavailable"

If sensors show as unavailable:
1. Check if your device is online in the Kerbl Welt app
2. Wait for the next update cycle (up to 5 minutes)
3. Check Home Assistant logs for errors:
   - Settings → System → Logs
   - Filter by "kerblwelt"

### No Data Updating

If sensors aren't updating:
1. Check your internet connection
2. Verify the Kerbl Welt API is accessible
3. Try removing and re-adding the integration
4. Check logs for API errors

## API Details

- **Update Interval**: 5 minutes (configurable in future versions)
- **API Endpoint**: `https://backend.kerbl-iot.com/api/v0.1`
- **Authentication**: JWT token-based
- **Data Source**: Kerbl Welt cloud service

## Supported Devices

- AKO Smart Satellite electric fence monitor

Other Kerbl Welt devices may work but are untested.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Development

### Setup Development Environment

```bash
# Clone repo
git clone https://github.com/sgarrity/homeassistant-kerblwelt
cd homeassistant-kerblwelt

# Install Home Assistant Core for development
# (Follow Home Assistant developer docs)
```

### Testing

The integration includes the required structure for Home Assistant testing:
- Config flow tests
- Sensor tests
- Integration tests

## License

MIT License - see [LICENSE](../LICENSE) file

## Credits

- Built by Steve Garrity
- Uses the [kerblwelt-api](https://github.com/sgarrity/kerblwelt-api) Python library
- Designed for [Home Assistant](https://www.home-assistant.io/)

## Links

- [Kerbl Welt Web App](https://app.kerbl-iot.com)
- [AKO Smart Satellite Product](https://www.kerbl.com/en/product/ako-smart-satellite/)
- [Home Assistant](https://www.home-assistant.io)
- [HACS](https://hacs.xyz)

## Support

- [GitHub Issues](https://github.com/stgarrity/homeassistant-kerblwelt/issues)
- [Home Assistant Community](https://community.home-assistant.io/)

## Disclaimer

This is an unofficial integration and is not affiliated with, endorsed by, or connected to Kerbl GmbH or AKO.
