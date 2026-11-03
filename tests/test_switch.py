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
