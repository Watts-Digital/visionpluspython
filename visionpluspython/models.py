"""Data models for Watts Vision API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .const import (
    DEFAULT_THERMOSTAT_MAX_TEMPERATURE,
    DEFAULT_THERMOSTAT_MIN_TEMPERATURE,
    DEFAULT_THERMOSTAT_MODE,
    INTERFACE_SWITCH,
    INTERFACE_THERMOSTAT,
    ThermostatMode,
)
from .exceptions import WattsVisionDeviceError


@dataclass
class Device:
    """Base device model."""

    device_id: str
    device_name: str
    device_type: str | None = None
    interface: str = ""
    room_name: str | None = None
    is_online: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Device:
        """Create Device from API response data."""
        return cls(
            device_id=data.get("deviceId", ""),
            device_name=data.get("deviceName", ""),
            device_type=data.get("deviceType"),
            interface=data.get("interface", ""),
            room_name=data.get("roomName"),
            is_online=data.get("isOnline", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert device to dictionary."""
        return {
            "deviceId": self.device_id,
            "deviceName": self.device_name,
            "deviceType": self.device_type,
            "interface": self.interface,
            "roomName": self.room_name,
            "isOnline": self.is_online,
        }

    def __str__(self) -> str:
        status = "online" if self.is_online else "offline"
        return f"{self.device_name} ({self.device_id}) - {status}"


@dataclass
class ThermostatDevice(Device):
    """Thermostat device model."""

    current_temperature: float | None = None
    setpoint: float | None = None
    thermostat_mode: str = "Off"
    min_allowed_temperature: float = DEFAULT_THERMOSTAT_MIN_TEMPERATURE
    max_allowed_temperature: float = DEFAULT_THERMOSTAT_MAX_TEMPERATURE
    temperature_unit: str = "°C"
    available_thermostat_modes: list[str] | None = None

    def is_temperature_valid(self, temperature: float) -> bool:
        """Check if temperature is within allowed range."""
        return (
            self.min_allowed_temperature <= temperature <= self.max_allowed_temperature
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ThermostatDevice:
        """Create ThermostatDevice from API response data."""
        base_device = Device.from_dict(data)

        min_temp = data.get("minAllowedTemperature")
        max_temp = data.get("maxAllowedTemperature")
        thermostat_mode = data.get("thermostatMode")

        if min_temp is None:
            min_temp = DEFAULT_THERMOSTAT_MIN_TEMPERATURE
        if max_temp is None:
            max_temp = DEFAULT_THERMOSTAT_MAX_TEMPERATURE
        if thermostat_mode is None:
            thermostat_mode = DEFAULT_THERMOSTAT_MODE

        return cls(
            device_id=base_device.device_id,
            device_name=base_device.device_name,
            device_type=base_device.device_type,
            interface=base_device.interface,
            room_name=base_device.room_name,
            is_online=base_device.is_online,
            current_temperature=data.get("currentTemperature"),
            setpoint=data.get("setpoint"),
            thermostat_mode=thermostat_mode,
            min_allowed_temperature=min_temp,
            max_allowed_temperature=max_temp,
            temperature_unit=data.get("temperatureUnit", "°C"),
            available_thermostat_modes=data.get("availableThermostatModes", []),
        )

    @property
    def mode_enum(self) -> ThermostatMode | None:
        """Get thermostat mode as enum."""
        if not self.thermostat_mode:
            return None

        mode_mapping = {
            "Program": ThermostatMode.PROGRAM,
            "Eco": ThermostatMode.ECO,
            "Comfort": ThermostatMode.COMFORT,
            "Off": ThermostatMode.OFF,
            "Defrost": ThermostatMode.DEFROST,
            "Timer": ThermostatMode.TIMER,
        }

        return mode_mapping.get(self.thermostat_mode)


@dataclass
class SwitchDevice(Device):
    """Switch device model."""

    is_turned_on: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SwitchDevice:
        """Create SwitchDevice from API response data."""
        base_device = Device.from_dict(data)
        return cls(
            device_id=base_device.device_id,
            device_name=base_device.device_name,
            device_type=base_device.device_type,
            interface=base_device.interface,
            room_name=base_device.room_name,
            is_online=base_device.is_online,
            is_turned_on=data.get("isTurnedOn", False),
        )


def create_device_from_data(data: dict[str, Any]) -> Device:
    """Create appropriate device type from API data."""
    if not data or not data.get("deviceId"):
        raise WattsVisionDeviceError("Invalid device data")

    interface = data.get("interface", "")

    if interface == INTERFACE_THERMOSTAT:
        return ThermostatDevice.from_dict(data)
    if interface == INTERFACE_SWITCH:
        return SwitchDevice.from_dict(data)
    return Device.from_dict(data)
