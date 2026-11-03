"""Select entities for staged NSClock settings."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import EntityCategory

from .coordinator import NightscoutClockCoordinator
from .entity import NightscoutClockEntity
from .runtime_data import NightscoutClockConfigEntry


async def async_setup_entry(hass, entry: NightscoutClockConfigEntry, async_add_entities) -> None:
    """Set up NSClock select entities."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        [
            NightscoutClockBrightnessModeSelect(coordinator, entry),
            NightscoutClockTimeFormatSelect(coordinator, entry),
        ]
    )


class NightscoutClockConfigSelect(NightscoutClockEntity, SelectEntity):
    """Base class for a staged configuration select."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
        object_id: str,
        name: str,
        config_key: str,
        options: list[str],
        icon: str,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id=object_id,
            name=name,
            icon=icon,
            entity_category=EntityCategory.CONFIG,
        )
        self._config_key = config_key
        self._attr_options = options

    @property
    def current_option(self) -> str | None:
        """Return the staged or current device option."""
        value = self.coordinator.config_value(self._config_key)
        return str(value) if value is not None else None

    async def async_select_option(self, option: str) -> None:
        """Stage a supported option for the next apply service call."""
        self.coordinator.stage_config_value(self._config_key, option)
        self.async_write_ha_state()


class NightscoutClockBrightnessModeSelect(NightscoutClockConfigSelect):
    """Brightness mode setting."""

    def __init__(self, coordinator: NightscoutClockCoordinator, config_entry: Any) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="brightness_mode_setting",
            name="Brightness Mode Setting",
            config_key="brightness_mode",
            options=["auto_linear", "auto_dimmed", "manual"],
            icon="mdi:brightness-6",
        )


class NightscoutClockTimeFormatSelect(NightscoutClockConfigSelect):
    """Time format setting."""

    def __init__(self, coordinator: NightscoutClockCoordinator, config_entry: Any) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="time_format_setting",
            name="Time Format Setting",
            config_key="time_format",
            options=["12", "24"],
            icon="mdi:clock-time-four",
        )
