"""Switch entities."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory

from .api import NightscoutClockApiClient
from .coordinator import NightscoutClockCoordinator
from .entity import NightscoutClockEntity
from .runtime_data import NightscoutClockConfigEntry


async def async_setup_entry(hass, entry: NightscoutClockConfigEntry, async_add_entities) -> None:
    """Set up NSClock switch entities."""
    coordinator = entry.runtime_data.coordinator
    api = entry.runtime_data.api

    async_add_entities(
        [
            NightscoutClockConfigSwitch(
                coordinator, entry, "alarm_high_enabled", "High Alarm Enabled"
            ),
            NightscoutClockConfigSwitch(
                coordinator, entry, "alarm_low_enabled", "Low Alarm Enabled"
            ),
            NightscoutClockConfigSwitch(
                coordinator,
                entry,
                "alarm_urgent_low_enabled",
                "Urgent Low Alarm Enabled",
            ),
            NightscoutClockConfigSwitch(
                coordinator,
                entry,
                "surprise_mode",
                "Surprise Mode",
                object_id="surprise_mode_setting",
                icon="mdi:party-popper",
            ),
            NightscoutClockConfigSwitch(
                coordinator,
                entry,
                "low_battery_alert_enable",
                "Low Battery Alert Enabled",
                object_id="low_battery_alert_setting",
                icon="mdi:battery-alert",
            ),
        ]
    )


class NightscoutClockConfigSwitch(NightscoutClockEntity, SwitchEntity):
    """Staged boolean configuration setting."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
        config_key: str,
        name: str,
        object_id: str | None = None,
        icon: str = "mdi:alarm",
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id=object_id or config_key.removesuffix("_enabled") + "_setting",
            name=name,
            icon=icon,
            entity_category=EntityCategory.CONFIG,
        )
        self._config_key = config_key

    @property
    def is_on(self) -> bool:
        """Return the staged or current device setting."""
        return bool(self.coordinator.config_value(self._config_key))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Stage enabling the setting."""
        self.coordinator.stage_config_value(self._config_key, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stage disabling the setting."""
        self.coordinator.stage_config_value(self._config_key, False)
        self.async_write_ha_state()
