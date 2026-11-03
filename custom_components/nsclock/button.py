"""Button entities."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity

from .const import DEFAULT_MELODY, DOMAIN
from .coordinator import NightscoutClockCoordinator
from .entity import NightscoutClockEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up NSClock button entities."""
    domain_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: NightscoutClockCoordinator = domain_data["coordinator"]
    api = domain_data["api"]

    buttons: list[ButtonEntity] = [
        NightscoutClockPlayAlarmButton(coordinator, entry, api),
    ]

    # Restart button is disabled by default (plan requirement).
    if entry.options.get("enable_restart", False):
        buttons.append(NightscoutClockRestartButton(coordinator, entry, api))

    async_add_entities(buttons)


class NightscoutClockPlayAlarmButton(NightscoutClockEntity, ButtonEntity):
    """Play alarm melody button."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
        api,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="play_alarm_melody",
            name="Play Alarm Melody",
            icon="mdi:bell",
        )
        self._api = api

    async def async_press(self) -> None:
        melody = self._config_entry.options.get("default_melody", DEFAULT_MELODY)
        await self._api.play_alarm(melody)


class NightscoutClockRestartButton(NightscoutClockEntity, ButtonEntity):
    """Restart clock button (disabled by default)."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
        api,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="restart",
            name="Restart",
            icon="mdi:restart",
        )
        self._api = api

    async def async_press(self) -> None:
        await self._api.restart()
