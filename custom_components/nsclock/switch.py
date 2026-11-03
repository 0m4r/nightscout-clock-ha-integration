"""Switch entities."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN
from .coordinator import NightscoutClockCoordinator
from .entity import NightscoutClockEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up NSClock switch entities."""
    domain_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: NightscoutClockCoordinator = domain_data["coordinator"]
    api = domain_data["api"]

    async_add_entities([NightscoutClockDisplaySwitch(coordinator, entry, api)])


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
