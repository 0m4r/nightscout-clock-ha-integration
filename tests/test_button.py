"""Tests for NSClock button entities."""

from typing import Any

from pytest_homeassistant_custom_component.common import MockConfigEntry


async def async_setup(hass: Any, entry: MockConfigEntry, client: Any) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_play_alarm_melody(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)
    await hass.services.async_call("button", "press", {"entity_id": "button.play_alarm_melody"}, blocking=True)
    mock_api_client.play_alarm.assert_awaited_once()
