"""Authentication module for Watts Vision API."""

from __future__ import annotations

import asyncio
import time
from typing import Self

import aiohttp
import jwt

from .const import API_TIMEOUT, OAUTH2_TOKEN
from .exceptions import WattsVisionAuthError, WattsVisionConnectionError


class WattsVisionAuth:
    """Handle authentication for Watts Vision + API."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize authentication."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self._session = session
        self._close_session = session is None

        # Token storage
        self._access_token: str | None = None
        self._token_expires_at: float | None = None
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
            if self._is_token_valid():
                return self._access_token

            if not self.refresh_token:
                raise WattsVisionAuthError("No refresh token available. Please reauth.")

            await self._refresh_access_token()
            return self._access_token

    def _is_token_valid(self) -> bool:
        """Check if current token is valid (with 60s buffer)."""
        if not self._access_token or not self._token_expires_at:
            return False
        return time.time() < (self._token_expires_at - 60)

    async def _refresh_access_token(self) -> None:
        """Refresh access token using refresh token."""
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }

        try:
            async with self.session.post(
                OAUTH2_TOKEN,
                data=data,
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise WattsVisionAuthError(
                        f"Token request failed with status {response.status}: {error_text}"
                    )

                token_data = await response.json()

                self._access_token = token_data.get("access_token")
                if not self._access_token:
                    raise WattsVisionAuthError("No access token in response")

                expires_in = token_data.get("expires_in", 3600)
                self._token_expires_at = time.time() + expires_in

                if "refresh_token" in token_data:
                    self.refresh_token = token_data["refresh_token"]

        except aiohttp.ClientError as err:
            raise WattsVisionConnectionError(
                f"Connection error during authentication: {err}"
            ) from err
        except Exception as err:
            raise WattsVisionAuthError(f"Authentication failed: {err}") from err

    async def close(self) -> None:
        """Close the session."""
        if self._close_session and self._session:
            await self._session.close()
            self._session = None
