"""Nightscout Clock Home Assistant Integration."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from . import api
from .coordinator import NightscoutClockCoordinator
from .const import (
    CONF_HOST,
    CONF_PASSWORD,
    DOMAIN,
    SERVICE_APPLY_SETTINGS,
    SERVICE_REPORT_GLUCOSE,
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


def _validate_sgv(value: Any) -> int:
    """Validate a positive integer glucose value in mg/dL."""
    if type(value) is not int or value <= 0:
        raise vol.Invalid("sgv must be a positive integer in mg/dL")
    return value


def _validate_integer(value: Any) -> int:
    """Validate an integer without coercing strings or booleans."""
    if type(value) is not int:
        raise vol.Invalid("value must be an integer")
    return value


def _validate_glucose_timestamp(value: datetime) -> datetime:
    """Require an explicit timezone to avoid ambiguous glucose timestamps."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise vol.Invalid("timestamp must include a timezone")
    return value


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up NSClock integration from YAML (not used, kept for compatibility)."""
    hass.data.setdefault(DOMAIN, {})

    def get_target_coordinator(call: ServiceCall) -> NightscoutClockCoordinator:
        """Resolve the one loaded NSClock selected by the service target."""
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
        return domain_data["coordinator"]

    async def async_apply_settings(call: ServiceCall) -> None:
        """Apply staged settings for the device identified by the target entity."""
        coordinator = get_target_coordinator(call)
        await coordinator.async_apply_settings()

    async def async_report_glucose(call: ServiceCall) -> None:
        """Report one glucose reading to a clock using the API source."""
        timestamp = dt_util.as_utc(call.data["timestamp"])
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        elapsed = timestamp - epoch
        timestamp_ms = (
            elapsed.days * 86_400_000
            + elapsed.seconds * 1_000
            + elapsed.microseconds // 1_000
        )
        date_string = timestamp.isoformat(timespec="milliseconds").replace(
            "+00:00", "Z"
        )
        glucose_entry: dict[str, Any] = {
            "dateString": date_string,
            "sgv": call.data["sgv"],
            "date": timestamp_ms,
        }
        for field in ("direction", "trend"):
            if field in call.data:
                glucose_entry[field] = call.data[field]

        coordinator = get_target_coordinator(call)
        await coordinator.async_report_glucose(glucose_entry)

    hass.services.async_register(
        DOMAIN,
        SERVICE_APPLY_SETTINGS,
        async_apply_settings,
        schema=vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_ids}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REPORT_GLUCOSE,
        async_report_glucose,
        schema=vol.Schema(
            {
                vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
                vol.Required("sgv"): _validate_sgv,
                vol.Required("timestamp"): vol.All(
                    cv.datetime, _validate_glucose_timestamp
                ),
                vol.Optional("direction"): str,
                vol.Optional("trend"): _validate_integer,
            }
        ),
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NSClock from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    api_client = api.NightscoutClockApiClient(
        entry.data[CONF_HOST],
        entry.data.get(CONF_PASSWORD),
        session=async_get_clientsession(hass),
    )
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