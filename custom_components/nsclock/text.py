"""Text entities for staged NSClock settings."""

from __future__ import annotations

from typing import Any

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.helpers.entity import EntityCategory

from .coordinator import NightscoutClockCoordinator
from .entity import NightscoutClockEntity
from .runtime_data import NightscoutClockConfigEntry


async def async_setup_entry(hass, entry: NightscoutClockConfigEntry, async_add_entities) -> None:
    """Set up NSClock text entities."""
    coordinator: NightscoutClockCoordinator = entry.runtime_data.coordinator
    async_add_entities([NightscoutClockNameText(coordinator, entry)])


class NightscoutClockNameText(NightscoutClockEntity, TextEntity):
    """Clock name setting."""

    _attr_native_max = 32
    _attr_mode = TextMode.TEXT

    def __init__(self, coordinator: NightscoutClockCoordinator, config_entry: Any) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="clock_name_setting",
            name="Clock Name Setting",
            icon="mdi:badge-account",
            entity_category=EntityCategory.CONFIG,
        )

    @property
    def native_value(self) -> str | None:
        """Return the staged or current device name."""
        value = self.coordinator.config_value("clock_name")
        return str(value) if value is not None else None

    async def async_set_value(self, value: str) -> None:
        """Stage a name for the next apply service call."""
        self.coordinator.stage_config_value("clock_name", value)
        self.async_write_ha_state()
