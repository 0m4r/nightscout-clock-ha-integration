"""Data update coordinator for the NSClock integration."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    NightscoutClockApiClient,
    NightscoutClockApiError,
    NightscoutClockApiUnauthorized,
)
from .const import CONF_PASSWORD, DEFAULT_POLLING_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Refresh /version.txt no more often than every 6 hours.
VERSION_REFRESH_INTERVAL = timedelta(hours=6)
CONFIG_REFRESH_INTERVAL = timedelta(minutes=5)
RESTART_POLL_INTERVAL = 2
RESTART_TIMEOUT = 60

WRITABLE_CONFIG_OPTIONS: dict[str, tuple[type, Any]] = {
    "brightness_mode": (str, {"auto_linear", "auto_dimmed", "manual"}),
    "brightness_level": (int, (1, 101)),
    "time_format": (str, {"12", "24"}),
    "clock_name": (str, 32),
    "alarm_high_enabled": (bool, None),
    "alarm_low_enabled": (bool, None),
    "alarm_urgent_low_enabled": (bool, None),
    "surprise_mode": (bool, None),
    "low_battery_alert_enable": (bool, None),
    "alarm_high_value": (int, None),
    "alarm_low_value": (int, None),
    "alarm_urgent_low_value": (int, None),
}


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
        self._last_config_fetch: float | None = None
        self._config_cache: dict[str, Any] | None = None
        self._pending_config: dict[str, Any] = {}
        self._apply_lock = asyncio.Lock()

    @property
    def pending_config(self) -> dict[str, Any]:
        """Return a copy of the staged settings."""
        return self._pending_config.copy()

    def config_value(self, key: str) -> Any:
        """Return a staged value when present, otherwise the last device value."""
        if key in self._pending_config:
            return self._pending_config[key]
        config = self._config_cache or {}
        return config.get(key)

    def stage_config_value(self, key: str, value: Any) -> None:
        """Stage a supported configuration value without writing to the device."""
        if key not in WRITABLE_CONFIG_OPTIONS:
            raise HomeAssistantError(f"Configuration option {key!r} is not writable")

        expected_type, constraint = WRITABLE_CONFIG_OPTIONS[key]
        if type(value) is not expected_type:
            raise HomeAssistantError(f"Invalid value type for configuration option {key!r}")

        if isinstance(constraint, set) and value not in constraint:
            raise HomeAssistantError(f"Invalid value for configuration option {key!r}")
        if isinstance(constraint, tuple) and not constraint[0] <= value <= constraint[1]:
            raise HomeAssistantError(f"Invalid value for configuration option {key!r}")
        if isinstance(constraint, int) and len(value) > constraint:
            raise HomeAssistantError(f"Configuration option {key!r} is too long")

        self._pending_config[key] = value

    async def async_apply_settings(self) -> None:
        """Apply staged supported settings while preserving the full device config."""
        if not self._pending_config:
            raise HomeAssistantError("There are no staged NSClock settings to apply")

        async with self._apply_lock:
            await self._async_apply_staged_settings()

    async def async_report_glucose(self, entry: dict[str, Any]) -> None:
        """Append a glucose entry only when the clock is currently in API mode."""
        try:
            status = await self.client.get_status()
        except ConfigEntryAuthFailed:
            raise
        except Exception as error:
            raise HomeAssistantError(
                f"Unable to verify the NSClock glucose source: {error}"
            ) from error

        if not isinstance(status, dict) or status.get("bgSource") != "API":
            source = status.get("bgSource") if isinstance(status, dict) else None
            raise HomeAssistantError(
                f"Cannot report glucose because the NSClock source is {source!r}, not 'API'"
            )

        try:
            result = await self.client.report_glucose_entries([entry])
        except ConfigEntryAuthFailed:
            raise
        except Exception as error:
            raise HomeAssistantError(
                f"Failed to report glucose to NSClock: {error}"
            ) from error

        if not isinstance(result, dict) or result.get("status") != "ok":
            raise HomeAssistantError("The NSClock rejected the glucose entry")

        updated_data = dict(self.data or {})
        updated_data["status"] = status
        self.async_set_updated_data(updated_data)

    async def async_set_face(self, face: str) -> None:
        """Request a temporary display-face switch."""
        try:
            result = await self.client.set_face(face)
        except ConfigEntryAuthFailed:
            raise
        except Exception as error:
            raise HomeAssistantError(
                f"Failed to switch the NSClock face: {error}"
            ) from error

        if not isinstance(result, dict) or result.get("status") != "ok":
            raise HomeAssistantError("The NSClock rejected the face change")

    async def _async_apply_staged_settings(self) -> None:
        """Apply one snapshot of staged settings."""
        staged_config = self._pending_config.copy()
        try:
            # Always start from a fresh full config so hidden fields are retained.
            config = await self.client.get_config()
            if not isinstance(config, dict):
                raise HomeAssistantError("The clock returned an invalid configuration")
            full_config = config.copy()
            full_config.update(staged_config)
            save_result = await self.client.save_config(full_config)
            if not isinstance(save_result, dict) or save_result.get("status") != "ok":
                raise HomeAssistantError("The clock rejected the settings")
            restart_result = await self.client.restart()
            if not isinstance(restart_result, dict) or restart_result.get("status") != "ok":
                raise HomeAssistantError("The clock did not accept the restart request")
            await self._async_wait_for_restart()

            refreshed_config = await self.client.get_config()
            if not isinstance(refreshed_config, dict):
                raise HomeAssistantError("The clock returned an invalid configuration")
        except ConfigEntryAuthFailed:
            raise
        except HomeAssistantError:
            raise
        except Exception as error:
            raise HomeAssistantError(f"Failed to apply NSClock settings: {error}") from error

        for key, value in staged_config.items():
            if self._pending_config.get(key) == value:
                self._pending_config.pop(key, None)
        self._config_cache = refreshed_config
        self._last_config_fetch = time.monotonic()
        updated_data = dict(self.data or {})
        updated_data["config"] = refreshed_config
        self.async_set_updated_data(updated_data)

    async def _async_wait_for_restart(self) -> None:
        """Wait for the clock API to return after restarting."""
        deadline = time.monotonic() + RESTART_TIMEOUT
        while time.monotonic() < deadline:
            await asyncio.sleep(RESTART_POLL_INTERVAL)
            try:
                await self.client.get_version()
                return
            except ConfigEntryAuthFailed:
                raise
            except NightscoutClockApiError:
                continue
        raise HomeAssistantError("The clock did not return after restarting")

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

        now = time.monotonic()
        if (
            self._last_version_fetch is None
            or (now - self._last_version_fetch) >= VERSION_REFRESH_INTERVAL.total_seconds()
        ):
            version = await self.client.get_version()
            data["firmware_version"] = version
            self._last_version_fetch = now

        if (
            self._last_config_fetch is None
            or (now - self._last_config_fetch) >= CONFIG_REFRESH_INTERVAL.total_seconds()
        ):
            config = await self.client.get_config()
            if not isinstance(config, dict):
                raise UpdateFailed("The clock returned an invalid configuration")
            self._config_cache = config.copy()
            self._last_config_fetch = now

        if self._config_cache is not None:
            data["config"] = self._config_cache

        return data
