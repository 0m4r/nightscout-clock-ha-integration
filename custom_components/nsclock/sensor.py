"""Sensor entities."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .coordinator import NightscoutClockCoordinator
from .entity import NightscoutClockEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up NSClock sensor entities."""
    domain_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: NightscoutClockCoordinator = domain_data["coordinator"]

    async_add_entities(
        [
            NightscoutClockGlucoseSensor(coordinator, entry),
            NightscoutClockDataSourceSensor(coordinator, entry),
            NightscoutClockSourceStatusSensor(coordinator, entry),
            NightscoutClockFirmwareVersionSensor(coordinator, entry),
        ]
    )


class NightscoutClockGlucoseSensor(NightscoutClockEntity, SensorEntity):
    """Blood glucose sensor."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="blood_glucose",
            name="Blood Glucose",
            device_class=SensorDeviceClass.BLOOD_GLUCOSE_CONCENTRATION,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement="mg/dL",
            icon="mdi:drop",
        )

    @property
    def native_value(self) -> Any:
        status = self.coordinator.data.get("status", {}) if self.coordinator.data else {}
        return status.get("sgv")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        status = self.coordinator.data.get("status", {}) if self.coordinator.data else {}
        return {
            "data_source": status.get("bgSource"),
            "source_status": status.get("bgSourceStatus"),
        }


class NightscoutClockDataSourceSensor(NightscoutClockEntity, SensorEntity):
    """Data source sensor."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="data_source",
            name="Data Source",
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:source-branch",
        )

    @property
    def native_value(self) -> Any:
        status = self.coordinator.data.get("status", {}) if self.coordinator.data else {}
        return status.get("bgSource")


class NightscoutClockSourceStatusSensor(NightscoutClockEntity, SensorEntity):
    """Source status sensor."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="source_status",
            name="Source Status",
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:information",
        )

    @property
    def native_value(self) -> Any:
        status = self.coordinator.data.get("status", {}) if self.coordinator.data else {}
        return status.get("bgSourceStatus")


class NightscoutClockFirmwareVersionSensor(NightscoutClockEntity, SensorEntity):
    """Firmware version sensor."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="firmware_version",
            name="Firmware Version",
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:firmware",
        )

    @property
    def native_value(self) -> Any:
        if self.coordinator.data:
            return self.coordinator.data.get("firmware_version")
        return None

