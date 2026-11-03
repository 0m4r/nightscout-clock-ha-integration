"""Switch entities."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .coordinator import NightscoutClockCoordinator
from .entity import NightscoutClockEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up NSClock switch entities."""
    domain_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: NightscoutClockCoordinator = domain_data["coordinator"]
    api = domain_data["api"]

    async_add_entities(
        [
            NightscoutClockDisplaySwitch(coordinator, entry, api),
            NightscoutClockAlarmEnabledSwitch(
                coordinator, entry, "alarm_high_enabled", "High Alarm Enabled"
            ),
            NightscoutClockAlarmEnabledSwitch(
                coordinator, entry, "alarm_low_enabled", "Low Alarm Enabled"
            ),
            NightscoutClockAlarmEnabledSwitch(
                coordinator,
                entry,
                "alarm_urgent_low_enabled",
                "Urgent Low Alarm Enabled",
            ),
        ]
    )


class NightscoutClockDisplaySwitch(NightscoutClockEntity, SwitchEntity):
    """Display power switch."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
        api,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="display",
            name="Display",
            icon="mdi:display",
        )
        self._api = api

    @property
    def is_on(self) -> bool:
        status = self.coordinator.data.get("status", {}) if self.coordinator.data else {}
        return bool(status.get("isConnected", True))

    async def async_turn_on(self, **kwargs) -> None:
        await self._api.set_display_power("on")

    async def async_turn_off(self, **kwargs) -> None:
        await self._api.set_display_power("off")


class NightscoutClockAlarmEnabledSwitch(NightscoutClockEntity, SwitchEntity):
    """Staged alarm-enabled setting."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
        config_key: str,
        name: str,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id=config_key.removesuffix("_enabled") + "_setting",
            name=name,
            icon="mdi:alarm",
            entity_category=EntityCategory.CONFIG,
        )
        self._config_key = config_key

    @property
    def is_on(self) -> bool:
        """Return the staged or current device setting."""
        return bool(self.coordinator.config_value(self._config_key))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Stage enabling the alarm."""
        self.coordinator.stage_config_value(self._config_key, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stage disabling the alarm."""
        self.coordinator.stage_config_value(self._config_key, False)
        self.async_write_ha_state()
