"""Main client for Watts Vision API."""

from __future__ import annotations

from http import HTTPStatus
import logging
from typing import Any, Self

import aiohttp

from .auth import WattsVisionAuth
from .const import (
    API_BASE_URL,
    API_ENDPOINTS,
    API_TIMEOUT,
    DEFAULT_THERMOSTAT_MAX_TEMPERATURE,
    DEFAULT_THERMOSTAT_MIN_TEMPERATURE,
    ThermostatMode,
)
from .exceptions import (
    WattsVisionConnectionError,
    WattsVisionDeviceError,
    WattsVisionError,
    WattsVisionTimeoutError,
)
from .models import Device, SwitchDevice, ThermostatDevice, create_device_from_data

_LOGGER = logging.getLogger(__name__)


class WattsVisionClient:
    """Client for Watts Vision API."""

    def __init__(
        self,
        auth: WattsVisionAuth,
        session: aiohttp.ClientSession | None = None,
        timeout: int = API_TIMEOUT,
    ) -> None:
        """Initialize the client."""

        self.auth = auth
        self._session = session
        self._close_session = session is None
        self.timeout = timeout
        self._devices_cache: dict[str, Device] = {}

    async def __aenter__(self) -> Self:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        await self.auth.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.auth.__aexit__(exc_type, exc_val, exc_tb)
        if self._close_session and self._session:
            await self._session.close()

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make authenticated request to API."""

        url = f"{API_BASE_URL}{endpoint}"

        try:
            token = await self.auth.get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            timeout = aiohttp.ClientTimeout(total=self.timeout)

            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                timeout=timeout,
                **kwargs,
            ) as response:
                # Handle 401 with token refresh retry
                if response.status == HTTPStatus.UNAUTHORIZED:
                    token = await self.auth.get_access_token()
                    headers["Authorization"] = f"Bearer {token}"

                    async with self.session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=json_data,
                        timeout=timeout,
                        **kwargs,
                    ) as retry_response:
                        retry_response.raise_for_status()
                        return await retry_response.json()

                response.raise_for_status()
                return await response.json()

        except TimeoutError as err:
            raise WattsVisionTimeoutError(
                f"Request timed out after {self.timeout}s"
            ) from err
        except aiohttp.ClientResponseError as err:
            if err.status == HTTPStatus.NOT_FOUND:
                raise WattsVisionDeviceError(f"Device not found: {endpoint}") from err
            raise WattsVisionError(f"API request failed: {err}") from err
        except aiohttp.ClientError as err:
            raise WattsVisionConnectionError(f"Connection error: {err}") from err

    async def discover_devices(self) -> list[Device]:
        """Discover all devices with their states."""

        try:
            data = await self._make_request("GET", API_ENDPOINTS["discover"])

            devices_data = data.get("devices", [])
            device_states = data.get("deviceStates", [])

            # Create device states mapping
            states_by_id = {state["deviceId"]: state for state in device_states}

            devices = []
            for device_data in devices_data:
                device_id = device_data.get("deviceId")

                if device_id in states_by_id:
                    merged_data = {**device_data, **states_by_id[device_id]}
                else:
                    merged_data = device_data

                device = create_device_from_data(merged_data)
                devices.append(device)
                self._devices_cache[device_id] = device

            _LOGGER.debug("Discovered %d devices", len(devices))
            return devices

        except Exception as err:
            _LOGGER.error("Failed to discover devices: %s", err)
            raise

    async def get_device_report(self, device_id: str) -> dict[str, Any]:
        """Get device state report."""

        endpoint = API_ENDPOINTS["device_report"].format(device_id=device_id)
        return await self._make_request("GET", endpoint)

    async def get_device(self, device_id: str, refresh: bool = False) -> Device | None:
        """Get device data by ID."""

        try:
            state_data = await self.get_device_report(device_id)

            cached_device = self._devices_cache[device_id]
            device_data = cached_device.to_dict()
            device_data.update(state_data)
            device = create_device_from_data(device_data)
            self._devices_cache[device_id] = device

            return device

        except Exception as err:
            _LOGGER.error("Failed to get device %s: %s", device_id, err)
            raise

    async def get_devices_report(self, device_ids: list[str]) -> dict[str, Device]:
        """Get device state reports for multiple devices."""

        if not device_ids:
            return {}

        params = [("deviceIds", device_id) for device_id in device_ids]

        endpoint = API_ENDPOINTS["devices_report"]

        try:
            data = await self._make_request("GET", endpoint, params=params)

            device_states = data.get("deviceStates", [])

            devices_by_id = {}
            for state in device_states:
                device_id = state["deviceId"]

                if device_id in self._devices_cache:
                    cached_device = self._devices_cache[device_id]
                    merged_data = {**cached_device.to_dict(), **state}
                else:
                    merged_data = state

                device = create_device_from_data(merged_data)
                devices_by_id[device_id] = device

                self._devices_cache[device_id] = device

            return devices_by_id

        except Exception as err:
            _LOGGER.error("Failed to get multiple device reports: %s", err)
            raise

    async def set_thermostat_temperature(
        self, device_id: str, temperature: float
    ) -> None:
        """Set thermostat target temperature."""

        device = await self.get_device(device_id)
        if not isinstance(device, ThermostatDevice):
            raise WattsVisionDeviceError(f"Device {device_id} is not a thermostat")

        min_temp = device.min_allowed_temperature or DEFAULT_THERMOSTAT_MIN_TEMPERATURE
        max_temp = device.max_allowed_temperature or DEFAULT_THERMOSTAT_MAX_TEMPERATURE

        if not (min_temp <= temperature <= max_temp):
            raise WattsVisionDeviceError(
                f"Temperature {temperature} is outside allowed range "
                f"({min_temp}-{max_temp})"
            )

        endpoint = API_ENDPOINTS["set_temperature"].format(device_id=device_id)
        await self._make_request("POST", endpoint, {"targetTemperature": temperature})

        # Update cached device
        device.setpoint = temperature
        _LOGGER.debug("Set temperature to %s°C for device %s", temperature, device_id)

    async def set_thermostat_mode(
        self, device_id: str, mode: ThermostatMode | int
    ) -> None:
        """Set thermostat mode."""

        device = await self.get_device(device_id)
        if not isinstance(device, ThermostatDevice):
            raise WattsVisionDeviceError(f"Device {device_id} is not a thermostat")

        mode_value = mode.value if isinstance(mode, ThermostatMode) else mode

        endpoint = API_ENDPOINTS["set_thermostat_mode"].format(device_id=device_id)
        await self._make_request("POST", endpoint, {"mode": mode_value})

        _LOGGER.debug("Set thermostat mode to %s for device %s", mode_value, device_id)

    async def set_switch_state(self, device_id: str, is_on: bool) -> None:
        """Set switch state."""

        device = await self.get_device(device_id)
        if not isinstance(device, SwitchDevice):
            raise WattsVisionDeviceError(f"Device {device_id} is not a switch")

        endpoint = API_ENDPOINTS["set_switch_state"].format(device_id=device_id)
        await self._make_request("POST", endpoint, {"isTurnedOn": is_on})

        device.is_turned_on = is_on
        _LOGGER.debug(
            "Set switch %s for device %s", "on" if is_on else "off", device_id
        )

    async def close(self) -> None:
        """Close the client and cleanup resources."""

        await self.auth.close()
        if self._close_session and self._session:
            await self._session.close()
            self._session = None
