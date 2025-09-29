"""Authentication module for Watts Vision API."""

from __future__ import annotations

import asyncio
from typing import Any, Protocol, Self

import aiohttp
import jwt

from .exceptions import WattsVisionAuthError


class OAuth2Session(Protocol):
    """Protocol for OAuth2 session objects."""

    @property
    def token(self) -> dict[str, Any]:
        """Get the current token."""
        ...

    async def async_ensure_token_valid(self) -> None:
        """Ensure the token is valid."""
        ...


class WattsVisionAuth:
    """Handle authentication for Watts Vision + API."""

    def __init__(
        self,
        oauth_session: OAuth2Session,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize authentication."""
        self._oauth_session = oauth_session
        self._session = session
        self._close_session = session is None
        self._lock = asyncio.Lock()

    @staticmethod
    def extract_user_id_from_token(token: str) -> str | None:
        """Extract user ID from JWT access token."""
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get("sub")
        except (jwt.DecodeError, jwt.InvalidTokenError, KeyError):
            return None

    async def __aenter__(self) -> Self:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._close_session and self._session:
            await self._session.close()

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def get_access_token(self) -> str:
        """Get a valid access token."""
        async with self._lock:
            await self._oauth_session.async_ensure_token_valid()

            access_token = self._oauth_session.token.get("access_token")
            if not access_token:
                raise WattsVisionAuthError("No access token available in OAuth session")

            return str(access_token)

    @property
    def refresh_token(self) -> str | None:
        """Get the current refresh token."""
        return self._oauth_session.token.get("refresh_token")

    async def close(self) -> None:
        """Close the session."""
        if self._close_session and self._session:
            await self._session.close()
            self._session = None
