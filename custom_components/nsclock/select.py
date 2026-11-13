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
            NightscoutClockFaceSelect(coordinator, entry),
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


class NightscoutClockFaceSelect(NightscoutClockEntity, SelectEntity):
    """Select an active clock face to display.

    The options come from the clock's ``/api/faces`` endpoint, so the list
    reflects the faces activated on the device. Selecting a face temporarily
    switches to it without changing the default face, schedule, or cycling.
    """

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="face",
            name="Face",
            icon="mdi:view-dashboard",
        )

    @property
    def options(self) -> list[str]:
        """Return the active faces in navigation order."""
        faces = (
            self.coordinator.data.get("faces", [])
            if self.coordinator.data
            else []
        )
        return [str(face.get("id", "")) for face in faces if face.get("id")]

    @property
    def current_option(self) -> str | None:
        """Return the id of the face currently shown on the clock."""
        status = self.coordinator.data.get("status", {}) if self.coordinator.data else {}
        return status.get("faceId")

    async def async_select_option(self, option: str) -> None:
        """Switch to the selected face and refresh face state."""
        await self.coordinator.async_set_face(option)


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
