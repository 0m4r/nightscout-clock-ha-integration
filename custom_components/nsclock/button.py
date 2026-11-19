"""Button entities for the NSClock integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity

from .api import NightscoutClockApiClient
from .const import DEFAULT_MELODY
from .coordinator import NightscoutClockCoordinator
from .entity import NightscoutClockEntity
from .runtime_data import NightscoutClockConfigEntry


async def async_setup_entry(hass, entry: NightscoutClockConfigEntry, async_add_entities) -> None:
    """Set up NSClock button entities."""
    coordinator = entry.runtime_data.coordinator
    api = entry.runtime_data.api

    buttons: list[ButtonEntity] = [
        NightscoutClockPlayAlarmButton(coordinator, entry, api),
        NightscoutClockDisplayPowerButton(coordinator, entry, api, "on"),
        NightscoutClockDisplayPowerButton(coordinator, entry, api, "off"),
        NightscoutClockFaceNavigationButton(coordinator, entry, api, "next"),
        NightscoutClockFaceNavigationButton(coordinator, entry, api, "previous"),
        NightscoutClockBrightnessNavigationButton(coordinator, entry, api, "next"),
        NightscoutClockBrightnessNavigationButton(coordinator, entry, api, "previous"),
        NightscoutClockForceRefreshButton(coordinator, entry),
    ]

    # Restart button is disabled by default (plan requirement).
    if entry.options.get("enable_restart", False):
        buttons.append(NightscoutClockRestartButton(coordinator, entry, api))

    # Device-only controls that the firmware exposes over HTTP but the UI
    # has no exposed HA entity for yet.
    buttons.extend(
        [
            NightscoutClockWifiScanButton(coordinator, entry, api),
            NightscoutClockLluPatientsButton(coordinator, entry, api),
            NightscoutClockLogsButton(coordinator, entry, api),
        ]
    )

    async_add_entities(buttons)


class NightscoutClockPlayAlarmButton(NightscoutClockEntity, ButtonEntity):
    """Play alarm melody button."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: NightscoutClockConfigEntry,
        api: NightscoutClockApiClient,
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


class NightscoutClockDisplayPowerButton(NightscoutClockEntity, ButtonEntity):
    """Turn the display on or off without claiming to report its current state."""

    def __init__(self, coordinator, config_entry, api, power: str) -> None:
        self._api = api
        self._power = power
        is_on = power == "on"
        super().__init__(
            coordinator,
            config_entry,
            object_id=f"display_{power}",
            name=f"Display {power.title()}",
            icon="mdi:monitor" if is_on else "mdi:monitor-off",
        )

    async def async_press(self) -> None:
        await self._api.set_display_power(self._power)


class NightscoutClockFaceNavigationButton(NightscoutClockEntity, ButtonEntity):
    """Navigate between active clock faces."""

    def __init__(self, coordinator, config_entry, api, direction: str) -> None:
        self._api = api
        self._direction = direction
        is_next = direction == "next"
        super().__init__(
            coordinator,
            config_entry,
            object_id=f"face_{direction}",
            name=f"{direction.title()} Face",
            icon="mdi:skip-forward" if is_next else "mdi:skip-backward",
        )

    async def async_press(self) -> None:
        if self._direction == "next":
            await self._api.next_face()
        else:
            await self._api.previous_face()
        await self.coordinator.async_request_refresh()


class NightscoutClockBrightnessNavigationButton(NightscoutClockEntity, ButtonEntity):
    """Navigate the temporary brightness cycle."""

    def __init__(self, coordinator, config_entry, api, direction: str) -> None:
        self._api = api
        self._direction = direction
        is_next = direction == "next"
        super().__init__(
            coordinator,
            config_entry,
            object_id=f"brightness_{direction}",
            name=f"Brightness {direction.title()}",
            icon="mdi:brightness-7" if is_next else "mdi:brightness-5",
        )

    async def async_press(self) -> None:
        if self._direction == "next":
            await self._api.next_brightness()
        else:
            await self._api.previous_brightness()


class NightscoutClockRestartButton(NightscoutClockEntity, ButtonEntity):
    """Restart clock button (disabled by default)."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: NightscoutClockConfigEntry,
        api: NightscoutClockApiClient,
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


class NightscoutClockForceRefreshButton(NightscoutClockEntity, ButtonEntity):
    """Force re-fetch /version.txt and /revision.txt into coordinator.data."""

    def __init__(
        self, coordinator: NightscoutClockCoordinator, config_entry: Any
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="force_refresh",
            name="Force Refresh",
            icon="mdi:arrow-repeat",
        )

    async def async_press(self) -> None:
        await self.coordinator.force_refresh()


class NightscoutClockWifiScanButton(NightscoutClockEntity, ButtonEntity):
    """Run a Wi-Fi scan on the clock and show the results."""

    def __init__(
        self, coordinator: NightscoutClockCoordinator, config_entry: Any, api: NightscoutClockApiClient
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="wifi_scan",
            name="Wi-Fi Scan",
            icon="mdi:wifi-scan",
        )
        self._api = api

    async def async_press(self) -> None:
        await self._api.scan_wifi()
        await self.coordinator.async_request_refresh()


class NightscoutClockLluPatientsButton(NightscoutClockEntity, ButtonEntity):
    """Fetch Libre Link Up patients from the clock."""

    def __init__(
        self, coordinator: NightscoutClockCoordinator, config_entry: Any, api: NightscoutClockApiClient
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="llu_patients",
            name="Libre Link Up Patients",
            icon="mdi:account-multiple",
        )
        self._api = api

    async def async_press(self) -> None:
        await self._api.scan_llu_patients()
        await self.coordinator.async_request_refresh()


class NightscoutClockLogsButton(NightscoutClockEntity, ButtonEntity):
    """Fetch the clock's log buffer."""

    def __init__(
        self, coordinator: NightscoutClockCoordinator, config_entry: Any, api: NightscoutClockApiClient
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="logs",
            name="Device Logs",
            icon="mdi:file-document",
        )
        self._api = api

    async def async_press(self) -> None:
        await self._api.get_logs()
        await self.coordinator.async_request_refresh()
