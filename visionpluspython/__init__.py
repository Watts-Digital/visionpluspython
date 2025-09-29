"""Python API wrapper for Watts Vision+ heating system."""

from .auth import WattsVisionAuth
from .client import WattsVisionClient
from .const import ThermostatMode
from .exceptions import (
    WattsVisionAuthError,
    WattsVisionConnectionError,
    WattsVisionDeviceError,
    WattsVisionError,
    WattsVisionTimeoutError,
)
from .models import Device, SwitchDevice, ThermostatDevice

__version__ = "1.0.1"

__all__ = [
    "Device",
    "SwitchDevice",
    "ThermostatDevice",
    "ThermostatMode",
    "WattsVisionAuth",
    "WattsVisionAuthError",
    "WattsVisionClient",
    "WattsVisionConnectionError",
    "WattsVisionDeviceError",
    "WattsVisionError",
    "WattsVisionTimeoutError",
]
