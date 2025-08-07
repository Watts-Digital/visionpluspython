"""Exceptions for Watts Vision API."""


class WattsVisionError(Exception):
    """Base exception for Watts Vision API."""


class WattsVisionAuthError(WattsVisionError):
    """Authentication error."""


class WattsVisionConnectionError(WattsVisionError):
    """Connection error."""


class WattsVisionDeviceError(WattsVisionError):
    """Device operation error."""


class WattsVisionTimeoutError(WattsVisionError):
    """Request timeout error."""
