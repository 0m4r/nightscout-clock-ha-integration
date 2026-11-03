"""Nightscout Clock Home Assistant Integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er

from . import api
from .coordinator import NightscoutClockCoordinator
from .const import (
    CONF_HOST,
    CONF_PASSWORD,
    DOMAIN,
    SERVICE_APPLY_SETTINGS,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.TEXT,
]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up NSClock integration from YAML (not used, kept for compatibility)."""
    hass.data.setdefault(DOMAIN, {})

    async def async_apply_settings(call: ServiceCall) -> None:
        """Apply staged settings for the device identified by the target entity."""
        registry = er.async_get(hass)
        config_entry_ids: set[str] = set()
        for entity_id in call.data[ATTR_ENTITY_ID]:
            entity = registry.async_get(entity_id)
            if entity is None or entity.config_entry_id is None:
                raise HomeAssistantError(
                    "Select an entity belonging to a configured NSClock device"
                )
            config_entry_ids.add(entity.config_entry_id)

        if len(config_entry_ids) != 1:
            raise HomeAssistantError(
                "Select entities from exactly one NSClock device"
            )
        entry_id = config_entry_ids.pop()
        config_entry = hass.config_entries.async_get_entry(entry_id)
        if config_entry is None or config_entry.domain != DOMAIN:
            raise HomeAssistantError(
                "Select an entity belonging to a configured NSClock device"
            )
        domain_data = hass.data[DOMAIN].get(entry_id)
        if domain_data is None:
            raise HomeAssistantError("The selected NSClock device is not loaded")
        await domain_data["coordinator"].async_apply_settings()

    hass.services.async_register(
        DOMAIN,
        SERVICE_APPLY_SETTINGS,
        async_apply_settings,
        schema=vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_ids}),
    )
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