"""Base entity for NSClock integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NightscoutClockCoordinator


class NightscoutClockEntity(CoordinatorEntity[NightscoutClockCoordinator]):
    """Base entity for NSClock devices."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
        object_id: str | None = None,
        name: str | None = None,
        device_class: Any = None,
        icon: str | None = None,
        state_class: Any = None,
        native_unit_of_measurement: str | None = None,
        entity_category: Any = None,
    ) -> None:
        # Capture class-level _attr_object_id before Entity.__init__ resets it
        class_object_id = getattr(self, "_attr_object_id", None)
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._object_id = object_id or class_object_id
        self._attr_object_id = self._object_id
        self._attr_name = name
        if device_class is not None:
            self._attr_device_class = device_class
        if icon is not None:
            self._attr_icon = icon
        if state_class is not None:
            self._attr_state_class = state_class
        if native_unit_of_measurement is not None:
            self._attr_native_unit_of_measurement = native_unit_of_measurement
        if entity_category is not None:
            self._attr_entity_category = entity_category

        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, config_entry.unique_id or config_entry.entry_id)
            },
            name="NSClock",
            manufacturer="Ulanzi",
            model="TC001",
            sw_version=coordinator.data.get("firmware_version")
            if coordinator.data
            else None,
            configuration_url=f"http://{entry_host(config_entry)}",
        )

    @property
    def available(self) -> bool:
        """Return True if the coordinator's last update succeeded."""
        return super().available and self.coordinator.last_update_success


def entry_host(config_entry: Any) -> str:
    """Return the host from a config entry, without logging credentials."""
    return str(config_entry.data.get("host", ""))
