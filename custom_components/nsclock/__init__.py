"""Nightscout Clock Home Assistant Integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from . import api
from .coordinator import NightscoutClockCoordinator
from .const import DOMAIN, CONF_HOST, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up NSClock integration from YAML (not used, kept for compatibility)."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NSClock from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    api_client = api.NightscoutClockApiClient(entry.data[CONF_HOST], entry.data.get(CONF_PASSWORD))
    coordinator = NightscoutClockCoordinator(hass, entry, api_client)

    # Fetch initial data so entities have something to show on first add.
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api_client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload NSClock config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the NSClock config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)