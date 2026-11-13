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

from .coordinator import NightscoutClockCoordinator
from .entity import NightscoutClockEntity
from .runtime_data import NightscoutClockConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry: NightscoutClockConfigEntry, async_add_entities) -> None:
    """Set up NSClock sensor entities."""
    coordinator: NightscoutClockCoordinator = entry.runtime_data.coordinator

    async_add_entities(
        [
            NightscoutClockGlucoseSensor(coordinator, entry),
            NightscoutClockDataSourceSensor(coordinator, entry),
            NightscoutClockSourceStatusSensor(coordinator, entry),
            NightscoutClockFirmwareVersionSensor(coordinator, entry),
            NightscoutClockFirmwareRevisionSensor(coordinator, entry),
            NightscoutClockCurrentFaceSensor(coordinator, entry),
            NightscoutClockBrightnessModeSensor(coordinator, entry),
            NightscoutClockBrightnessLevelSensor(coordinator, entry),
            NightscoutClockUnitsSensor(coordinator, entry),
            NightscoutClockTimeFormatSensor(coordinator, entry),
            NightscoutClockClockNameSensor(coordinator, entry),
            NightscoutClockDefaultFaceSensor(coordinator, entry),
            NightscoutClockFaceCycleIntervalSensor(coordinator, entry),
            NightscoutClockAlarmHighThresholdSensor(coordinator, entry),
            NightscoutClockAlarmLowThresholdSensor(coordinator, entry),
            NightscoutClockAlarmUrgentLowThresholdSensor(coordinator, entry),
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


class NightscoutClockFirmwareRevisionSensor(NightscoutClockEntity, SensorEntity):
    """Firmware source revision sensor."""

    def __init__(self, coordinator, config_entry: Any) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="firmware_revision",
            name="Firmware Revision",
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:source-commit",
        )

    @property
    def native_value(self) -> Any:
        if self.coordinator.data:
            return self.coordinator.data.get("firmware_revision")
        return None


class NightscoutClockCurrentFaceSensor(NightscoutClockEntity, SensorEntity):
    """Currently displayed clock face sensor."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="current_face",
            name="Current Face",
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:clock-digital",
        )

    @property
    def native_value(self) -> Any:
        status = self.coordinator.data.get("status", {}) if self.coordinator.data else {}
        return status.get("faceId")


class NightscoutClockConfigValueSensor(NightscoutClockEntity, SensorEntity):
    """Read-only configuration value sensor."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
        object_id: str,
        name: str,
        config_key: str,
        icon: str | None = None,
        entity_category: EntityCategory | None = None,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id=object_id,
            name=name,
            entity_category=entity_category,
            icon=icon,
        )
        self._config_key = config_key

    @property
    def native_value(self) -> Any:
        if not self.coordinator.data:
            return None
        config = self.coordinator.data.get("config") or {}
        return config.get(self._config_key)


class NightscoutClockBrightnessModeSensor(NightscoutClockConfigValueSensor):
    """Brightness mode sensor."""

    def __init__(self, coordinator, config_entry: Any) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="brightness_mode",
            name="Brightness Mode",
            config_key="brightness_mode",
            icon="mdi:brightness-6",
            entity_category=EntityCategory.DIAGNOSTIC,
        )


class NightscoutClockBrightnessLevelSensor(NightscoutClockConfigValueSensor):
    """Brightness level sensor."""

    def __init__(self, coordinator, config_entry: Any) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="brightness_level",
            name="Brightness Level",
            config_key="brightness_level",
            icon="mdi:brightness-5",
            entity_category=EntityCategory.DIAGNOSTIC,
        )


class NightscoutClockUnitsSensor(NightscoutClockConfigValueSensor):
    """Glucose units sensor."""

    def __init__(self, coordinator, config_entry: Any) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="glucose_units",
            name="Glucose Units",
            config_key="units",
            icon="mdi:beaker",
            entity_category=EntityCategory.DIAGNOSTIC,
        )


class NightscoutClockTimeFormatSensor(NightscoutClockConfigValueSensor):
    """Time format sensor."""

    def __init__(self, coordinator, config_entry: Any) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="time_format",
            name="Time Format",
            config_key="time_format",
            icon="mdi:clock-time-four",
            entity_category=EntityCategory.DIAGNOSTIC,
        )


class NightscoutClockClockNameSensor(NightscoutClockConfigValueSensor):
    """Clock name sensor."""

    def __init__(self, coordinator, config_entry: Any) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="clock_name",
            name="Clock Name",
            config_key="clock_name",
            icon="mdi:badge-account",
            entity_category=EntityCategory.DIAGNOSTIC,
        )


class NightscoutClockDefaultFaceSensor(NightscoutClockConfigValueSensor):
    """Default face sensor."""

    def __init__(self, coordinator, config_entry: Any) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="default_face",
            name="Default Face",
            config_key="default_face",
            icon="mdi:monitor-dashboard",
            entity_category=EntityCategory.DIAGNOSTIC,
        )


class NightscoutClockFaceCycleIntervalSensor(NightscoutClockConfigValueSensor):
    """Face cycle interval sensor."""

    def __init__(self, coordinator, config_entry: Any) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="face_cycle_interval",
            name="Face Cycle Interval",
            config_key="face_cycle_interval_seconds",
            icon="mdi:timer-outline",
            entity_category=EntityCategory.DIAGNOSTIC,
        )


class NightscoutClockAlarmHighThresholdSensor(NightscoutClockConfigValueSensor):
    """High alarm threshold sensor."""

    def __init__(self, coordinator, config_entry: Any) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="alarm_high_threshold",
            name="Alarm High Threshold",
            config_key="alarm_high_value",
            icon="mdi:alert",
            entity_category=EntityCategory.DIAGNOSTIC,
        )


class NightscoutClockAlarmLowThresholdSensor(NightscoutClockConfigValueSensor):
    """Low alarm threshold sensor."""

    def __init__(self, coordinator, config_entry: Any) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="alarm_low_threshold",
            name="Alarm Low Threshold",
            config_key="alarm_low_value",
            icon="mdi:alert-circle",
            entity_category=EntityCategory.DIAGNOSTIC,
        )


class NightscoutClockAlarmUrgentLowThresholdSensor(NightscoutClockConfigValueSensor):
    """Urgent-low alarm threshold sensor."""

    def __init__(self, coordinator, config_entry: Any) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="alarm_urgent_low_threshold",
            name="Alarm Urgent Low Threshold",
            config_key="alarm_urgent_low_value",
            icon="mdi:alert-octagon",
            entity_category=EntityCategory.DIAGNOSTIC,
        )
