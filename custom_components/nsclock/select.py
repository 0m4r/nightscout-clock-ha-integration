"""Select entities for staged NSClock settings."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.exceptions import HomeAssistantError
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

    def _face_options(self) -> list[tuple[str, str]]:
        """Return display names and IDs for the active faces."""
        faces = (
            self.coordinator.data.get("faces", [])
            if self.coordinator.data
            else []
        )
        labels: list[tuple[str, str]] = []
        used_labels: set[str] = set()
        for face in faces:
            if not isinstance(face, dict) or not face.get("id"):
                continue
            face_id = str(face["id"])
            base_label = str(face.get("name") or face_id)
            label = base_label
            if label in used_labels:
                label = f"{base_label} ({face_id})"
                suffix = 2
                while label in used_labels:
                    label = f"{base_label} ({face_id}, {suffix})"
                    suffix += 1
            used_labels.add(label)
            labels.append((label, face_id))
        return labels

    @property
    def options(self) -> list[str]:
        """Return active face names in navigation order."""
        return [label for label, _ in self._face_options()]

    @property
    def current_option(self) -> str | None:
        """Return the name of the face currently shown on the clock."""
        status = self.coordinator.data.get("status", {}) if self.coordinator.data else {}
        current_face_id = status.get("faceId")
        return next(
            (
                label
                for label, face_id in self._face_options()
                if face_id == current_face_id
            ),
            None,
        )

    async def async_select_option(self, option: str) -> None:
        """Switch to the selected face and refresh face state."""
        face_id = next(
            (face_id for label, face_id in self._face_options() if label == option),
            None,
        )
        if face_id is None:
            raise HomeAssistantError("The selected face is no longer active")
        await self.coordinator.async_set_face(face_id)


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
