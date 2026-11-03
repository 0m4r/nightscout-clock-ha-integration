"""Async client for the NSClock local HTTP API."""

from __future__ import annotations

import logging
from typing import Any, Literal

import aiohttp
from aiohttp.client_exceptions import ClientResponseError

from homeassistant.config_entries import ConfigEntryAuthFailed

_LOGGER = logging.getLogger(__name__)


class NightscoutClockApiError(Exception):
    """Base error for NSClock API failures."""


class NightscoutClockApiUnauthorized(NightscoutClockApiError):
    """Raised when authentication is required or has expired."""


class NightscoutClockApiClient:
    """Client for the NSClock HTTP API.

    Owns the base URL, optional password, cookie jar, login, retry, and request
    methods. Never logs passwords, cookies, API secrets, or Wi-Fi credentials.
    """

    def __init__(
        self,
        host: str,
        password: str | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._host = host.rstrip("/")
        self._password = password
        self._cookie: str | None = None
        self._session = session
        self._owns_session = session is None

    @property
    def host(self) -> str:
        """Return the host (no credentials)."""
        return self._host

    def _url(self, path: str) -> str:
        return f"http://{self._host}{path}"

    def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session."""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": "HomeAssistant/2026.2/nsclock"}
            )
        return self._session

    async def async_close(self) -> None:
        """Close the session if this client owns it."""
        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None

    def _attach_cookie(self, headers: dict[str, str]) -> None:
        """Attach the current auth cookie to request headers, if present."""
        if self._cookie:
            headers["Cookie"] = self._cookie

    async def _request(
        self,
        method: str,
        path: str,
        json: Any | None = None,
        retry_auth: bool = True,
    ) -> Any:
        session = self._get_session()
        headers: dict[str, str] = {}
        self._attach_cookie(headers)

        try:
            response = await session.request(
                method, self._url(path), json=json, headers=headers
            )

            # Capture auth cookie without logging its value.
            if "Set-Cookie" in response.headers:
                self._cookie = response.headers["Set-Cookie"].split(";", 1)[0]

            if response.status == 401 and retry_auth and self._password:
                # Auth expired: log in once, update cookie, retry the original request.
                _LOGGER.debug("Received 401 on %s, attempting login retry", path)
                await self.login(self._password)
                headers = {}
                self._attach_cookie(headers)
                response = await session.request(
                    method, self._url(path), json=json, headers=headers
                )
                if "Set-Cookie" in response.headers:
                    self._cookie = response.headers["Set-Cookie"].split(";", 1)[0]

            response.raise_for_status()

            if response.content_type == "application/json":
                return await response.json()
            return await response.text()
        except ClientResponseError as err:
            if err.status == 401:
                raise ConfigEntryAuthFailed("Authentication failed") from err
            raise NightscoutClockApiError(
                f"Request to {path} failed: {err}"
            ) from err
        except Exception as err:
            raise NightscoutClockApiError(
                f"Request to {path} failed: {err}"
            ) from err

    async def get_status(self) -> dict[str, Any]:
        """Get device status including glucose reading."""
        return await self._request("GET", "/api/status")

    async def get_version(self) -> str:
        """Get firmware version."""
        return await self._request("GET", "/version.txt")

    async def get_auth_status(self) -> dict[str, Any]:
        """Check authentication status."""
        return await self._request("GET", "/api/auth/status")

    async def login(self, password: str) -> dict[str, Any]:
        """Login with password and update session cookies."""
        return await self._request("POST", "/api/auth/login", {"password": password})

    async def set_display_power(self, power: Literal["on", "off"]) -> dict[str, Any]:
        """Set display power."""
        return await self._request("POST", "/api/displaypower", {"power": power})

    async def play_alarm(self, rtttl: str) -> dict[str, Any]:
        """Play alarm melody."""
        return await self._request("POST", "/api/alarm", {"rtttl": rtttl})

    async def restart(self) -> dict[str, Any]:
        """Restart the clock."""
        return await self._request("POST", "/api/reset", {})

    async def get_config(self) -> dict[str, Any]:
        """Get current configuration.

        Refreshes /config.json no more often than every 5-15 minutes because these are
        persisted settings, not live telemetry.
        """
        return await self._request("GET", "/config.json")

    async def save_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Save the complete device configuration."""
        return await self._request("POST", "/api/save", config)