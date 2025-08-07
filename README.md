# visionpluspython

[![PyPI version](https://badge.fury.io/py/visionpluspython.svg)](https://badge.fury.io/py/visionpluspython)
[![Python Support](https://img.shields.io/pypi/pyversions/visionpluspython.svg)](https://pypi.org/project/visionpluspython/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python API wrapper for Watts Vision+ smart home system, providing easy Home Assistant integration with thermostats and switches.

## Features

- **OAuth2 authentication** - Secure token-based authentication with automatic refresh
- **Device discovery** - Automatic discovery of all connected devices
- **Thermostat control** - Set temperature, modes, and read current status
- **Switch control** - Control on/off switches

## Installation

### From PyPI (recommended)

```bash
pip install visionpluspython
```

## Supported Device Types

### Thermostat
Control and monitor Watts heating devices.

**Available thermostat modes:**
- `PROGRAM` - Follow programmed schedule
- `COMFORT` - Comfort mode
- `ECO` - Energy saving mode
- `OFF` - Turn off heating
- `DEFROST` - Defrost mode
- `TIMER` - Timer mode

### Switch
Control Watts switch (on/off) devices

## Requirements

- Python 3.9+
- aiohttp >= 3.8.0

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### 1.0.0 (2025-08-01)
- Initial release
- OAuth2 authentication support
- Device discovery and control
- Thermostat and switch support