from enum import Enum

# API Configuration
API_BASE_URL = "https://dev-vision.watts.io/api"
API_TIMEOUT = 20

# OAuth2 Token Endpoint
OAUTH2_TOKEN = (
    "https://visionlogindev.b2clogin.com/visionlogindev.onmicrosoft.com/"
    "B2C_1A_VISION_UNIFIEDSIGNUPORSIGNIN/oauth2/v2.0/token"
)

# Device Interface Types
INTERFACE_THERMOSTAT = "homeassistant.components.THERMOSTAT"
INTERFACE_SWITCH = "homeassistant.components.SWITCH"

DEFAULT_MIN_TEMPERATURE = 5.0
DEFAULT_MAX_TEMPERATURE = 35.0

# API Endpoints
API_ENDPOINTS = {
    "discover": "/integrations/home-assistant/discover",
    "device_report": "/integrations/home-assistant/report/{device_id}",
    "set_temperature": "/integrations/home-assistant/control/thermostat/{device_id}/set-temperature",
    "set_thermostat_mode": "/integrations/home-assistant/control/thermostat/{device_id}/set-mode",
    "set_switch_state": "/integrations/home-assistant/control/switch/{device_id}/change-state",
}


# Thermostat Modes
class ThermostatMode(Enum):
    """Supported thermostat modes."""

    COMFORT = 1
    OFF = 2
    ECO = 3
    DEFROST = 4
    TIMER = 5
    PROGRAM = 6
