"""Tests for staged NSClock configuration settings."""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nsclock.coordinator import NightscoutClockCoordinator


async def make_coordinator(
    hass: Any, config_entry: MockConfigEntry, client: Any
) -> NightscoutClockCoordinator:
    config_entry.add_to_hass(hass)
    coordinator = NightscoutClockCoordinator(hass, config_entry, client)
    await coordinator._async_update_data()
    return coordinator


async def test_staged_settings_are_not_written_until_apply(
    hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any
) -> None:
    coordinator = await make_coordinator(hass, mock_config_entry, mock_api_client)

    coordinator.stage_config_value("brightness_mode", "auto_dimmed")
    assert coordinator.config_value("brightness_mode") == "auto_dimmed"
    mock_api_client.save_config.assert_not_awaited()


async def test_apply_preserves_hidden_config_and_updates_changed_values(
    hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any
) -> None:
    coordinator = await make_coordinator(hass, mock_config_entry, mock_api_client)
    coordinator.stage_config_value("brightness_level", 70)
    coordinator.stage_config_value("clock_name", "Bedroom")

    with patch(
        "custom_components.nsclock.coordinator.asyncio.sleep",
        new_callable=AsyncMock,
    ):
        await coordinator.async_apply_settings()

    saved_config = mock_api_client.save_config.await_args.args[0]
    assert saved_config["brightness_level"] == 70
    assert saved_config["clock_name"] == "Bedroom"
    assert saved_config["api_secret"] == "preserve-this-hidden-value"
    assert saved_config["wifi_password"] == "preserve-this-hidden-password"
    mock_api_client.restart.assert_awaited_once()
    assert coordinator.pending_config == {}
    assert coordinator.config_value("brightness_level") == 50


async def test_apply_without_pending_settings_fails(
    hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any
) -> None:
    coordinator = await make_coordinator(hass, mock_config_entry, mock_api_client)

    with pytest.raises(HomeAssistantError, match="no staged"):
        await coordinator.async_apply_settings()

    mock_api_client.save_config.assert_not_awaited()
    mock_api_client.restart.assert_not_awaited()


async def test_failed_save_keeps_staged_settings_and_does_not_restart(
    hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any
) -> None:
    coordinator = await make_coordinator(hass, mock_config_entry, mock_api_client)
    coordinator.stage_config_value("brightness_mode", "auto_dimmed")
    mock_api_client.save_config.return_value = {"status": "Settings save error"}

    with pytest.raises(HomeAssistantError, match="rejected"):
        await coordinator.async_apply_settings()

    assert coordinator.pending_config == {"brightness_mode": "auto_dimmed"}
    mock_api_client.restart.assert_not_awaited()


async def test_stage_rejects_unsupported_or_invalid_values(
    hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any
) -> None:
    coordinator = await make_coordinator(hass, mock_config_entry, mock_api_client)

    with pytest.raises(HomeAssistantError, match="not writable"):
        coordinator.stage_config_value("api_secret", "replacement")
    with pytest.raises(HomeAssistantError, match="Invalid value"):
        coordinator.stage_config_value("brightness_mode", "unknown")
    with pytest.raises(HomeAssistantError, match="Invalid value"):
        coordinator.stage_config_value("brightness_level", 0)
    with pytest.raises(HomeAssistantError, match="Invalid value type"):
        coordinator.stage_config_value("alarm_high_enabled", 1)

    assert coordinator.pending_config == {}
