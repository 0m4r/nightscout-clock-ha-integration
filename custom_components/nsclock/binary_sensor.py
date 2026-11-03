"""Binary sensor entities."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)

from .coordinator import NightscoutClockCoordinator
from .entity import NightscoutClockEntity
from .runtime_data import NightscoutClockConfigEntry


async def async_setup_entry(hass, entry: NightscoutClockConfigEntry, async_add_entities) -> None:
    """Set up NSClock binary sensor entities."""
    coordinator: NightscoutClockCoordinator = entry.runtime_data.coordinator

    async_add_entities(
        [
            NightscoutClockConnectedBinarySensor(coordinator, entry),
            NightscoutClockInternetBinarySensor(coordinator, entry),
            NightscoutClockAccessPointBinarySensor(coordinator, entry),
        ]
    )


class NightscoutClockConnectedBinarySensor(NightscoutClockEntity, BinarySensorEntity):
    """Clock connected binary sensor."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="clock_connected",
            name="Clock Connected",
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
            icon="mdi:lan-connect",
        )

    @property
    def is_on(self) -> bool:
        status = self.coordinator.data.get("status", {}) if self.coordinator.data else {}
        return bool(status.get("isConnected", False))


class NightscoutClockInternetBinarySensor(NightscoutClockEntity, BinarySensorEntity):
    """Internet available binary sensor."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="internet_available",
            name="Internet Available",
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
            icon="mdi:cloud",
        )

    @property
    def is_on(self) -> bool:
        status = self.coordinator.data.get("status", {}) if self.coordinator.data else {}
        return bool(status.get("hasInternet", False))


class NightscoutClockAccessPointBinarySensor(NightscoutClockEntity, BinarySensorEntity):
    """Access point mode binary sensor."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="access_point_mode",
            name="Access Point Mode",
            icon="mdi:wifi",
        )

    @property
    def is_on(self) -> bool:
        status = self.coordinator.data.get("status", {}) if self.coordinator.data else {}
        return bool(status.get("isInAPMode", False))
