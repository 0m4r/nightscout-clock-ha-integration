"""Runtime data for the NSClock integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry

from .api import NightscoutClockApiClient
from .coordinator import NightscoutClockCoordinator


@dataclass
class NightscoutClockRuntimeData:
    """Data available while an NSClock config entry is loaded."""

    api: NightscoutClockApiClient
    coordinator: NightscoutClockCoordinator


NightscoutClockConfigEntry = ConfigEntry[NightscoutClockRuntimeData]
