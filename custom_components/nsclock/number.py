"""Number entities for staged NSClock settings."""

from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .coordinator import NightscoutClockCoordinator
from .entity import NightscoutClockEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up NSClock number entities."""
    coordinator: NightscoutClockCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    async_add_entities(
        [
            NightscoutClockBrightnessLevelNumber(coordinator, entry),
            NightscoutClockAlarmThresholdNumber(
                coordinator, entry, "alarm_high_value", "High Alarm Threshold"
            ),
            NightscoutClockAlarmThresholdNumber(
                coordinator, entry, "alarm_low_value", "Low Alarm Threshold"
            ),
            NightscoutClockAlarmThresholdNumber(
                coordinator,
                entry,
                "alarm_urgent_low_value",
                "Urgent Low Alarm Threshold",
            ),
        ]
    )


class NightscoutClockConfigNumber(NightscoutClockEntity, NumberEntity):
    """Base class for a staged numeric configuration setting."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
        object_id: str,
        name: str,
        config_key: str,
        minimum: int,
        maximum: int,
        icon: str,
        unit: str | None = None,
    ) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id=object_id,
            name=name,
            icon=icon,
            native_unit_of_measurement=unit,
            entity_category=EntityCategory.CONFIG,
        )
        self._config_key = config_key
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = 1
        self._attr_mode = NumberMode.BOX

    @property
    def native_value(self) -> float | None:
        """Return the staged or current device value."""
        value = self.coordinator.config_value(self._config_key)
        return float(value) if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        """Stage an integer value for the next apply service call."""
        if not float(value).is_integer():
            raise HomeAssistantError("NSClock settings must be whole numbers")
        self.coordinator.stage_config_value(self._config_key, int(value))
        self.async_write_ha_state()


class NightscoutClockBrightnessLevelNumber(NightscoutClockConfigNumber):
    """Brightness level setting."""

    def __init__(self, coordinator: NightscoutClockCoordinator, config_entry: Any) -> None:
        super().__init__(
            coordinator,
            config_entry,
            object_id="brightness_level_setting",
            name="Brightness Level Setting",
            config_key="brightness_level",
            minimum=1,
            maximum=101,
            icon="mdi:brightness-5",
        )


class NightscoutClockAlarmThresholdNumber(NightscoutClockConfigNumber):
    """Alarm threshold setting."""

    def __init__(
        self,
        coordinator: NightscoutClockCoordinator,
        config_entry: Any,
        config_key: str,
        name: str,
    ) -> None:
        object_id = config_key.removesuffix("_value") + "_setting"
        super().__init__(
            coordinator,
            config_entry,
            object_id=object_id,
            name=name,
            config_key=config_key,
            minimum=0,
            maximum=400,
            icon="mdi:alert",
            unit="mg/dL",
        )
