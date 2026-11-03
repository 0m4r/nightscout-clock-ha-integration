"""Data update coordinator for the NSClock integration."""

from __future__ import annotations

import logging
import time
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NightscoutClockApiClient, NightscoutClockApiUnauthorized
from .const import CONF_PASSWORD, DEFAULT_POLLING_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Refresh /version.txt no more often than every 6 hours.
VERSION_REFRESH_INTERVAL = timedelta(hours=6)


class NightscoutClockCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate polling of the NSClock API."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: Any,
        client: NightscoutClockApiClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {config_entry.title}",
            update_interval=timedelta(seconds=DEFAULT_POLLING_INTERVAL),
        )
        self.config_entry = config_entry
        self.client = client
        self._last_version_fetch: float | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self._fetch_data()
        except NightscoutClockApiUnauthorized:
            # Auth expired: log in once, then retry the original request.
            password = self.config_entry.data.get(CONF_PASSWORD)
            if password:
                _LOGGER.debug("Auth expired, logging in and retrying")
                await self.client.login(password)
                return await self._fetch_data()
            raise ConfigEntryAuthFailed("Authentication required but no password configured")
        except Exception as error:
            raise UpdateFailed(f"Error communicating with NSClock: {error}") from error

    async def _fetch_data(self) -> dict[str, Any]:
        status = await self.client.get_status()
        if status.get("sgv") == 0:
            status["sgv"] = None

        data: dict[str, Any] = {"status": status}

        # Fetch firmware version infrequently (every 6 hours).
        now = time.monotonic()
        if (
            self._last_version_fetch is None
            or (now - self._last_version_fetch) >= VERSION_REFRESH_INTERVAL.total_seconds()
        ):
            version = await self.client.get_version()
            data["firmware_version"] = version
            self._last_version_fetch = now

        return data
