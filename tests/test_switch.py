"""Tests for the NSClock display switch."""

from typing import Any

from pytest_homeassistant_custom_component.common import MockConfigEntry


async def async_setup(hass: Any, entry: MockConfigEntry, client: Any) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_turn_display_off(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)
    await hass.services.async_call("switch", "turn_off", {"entity_id": "switch.display"}, blocking=True)
    mock_api_client.set_display_power.assert_awaited_once_with("off")


async def test_turn_display_on(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)
    await hass.services.async_call("switch", "turn_on", {"entity_id": "switch.display"}, blocking=True)
    mock_api_client.set_display_power.assert_awaited_once_with("on")


async def test_surprise_mode_is_staged(
    hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any
) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)

    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.surprise_mode"},
        blocking=True,
    )

    coordinator = mock_config_entry.runtime_data.coordinator
    assert coordinator.pending_config == {"surprise_mode": False}
    mock_api_client.save_config.assert_not_awaited()


async def test_low_battery_alert_setting_is_staged(
    hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any
) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)

    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.low_battery_alert_enabled"},
        blocking=True,
    )

    coordinator = mock_config_entry.runtime_data.coordinator
    assert coordinator.pending_config == {"low_battery_alert_enable": True}
    mock_api_client.save_config.assert_not_awaited()
