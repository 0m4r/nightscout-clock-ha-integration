"""Tests for NSClock button entities."""

from typing import Any
from unittest.mock import call

from pytest_homeassistant_custom_component.common import MockConfigEntry


async def async_setup(hass: Any, entry: MockConfigEntry, client: Any) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_play_alarm_melody(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)
    await hass.services.async_call("button", "press", {"entity_id": "button.play_alarm_melody"}, blocking=True)
    mock_api_client.play_alarm.assert_awaited_once()


async def test_display_power_buttons(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)
    for entity_id in ("button.display_on", "button.display_off"):
        await hass.services.async_call(
            "button", "press", {"entity_id": entity_id}, blocking=True
        )

    mock_api_client.set_display_power.assert_has_awaits([call("on"), call("off")])


async def test_face_and_brightness_navigation_buttons(
    hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any
) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)
    for entity_id in (
        "button.next_face",
        "button.previous_face",
        "button.brightness_next",
        "button.brightness_previous",
    ):
        await hass.services.async_call(
            "button", "press", {"entity_id": entity_id}, blocking=True
        )

    mock_api_client.next_face.assert_awaited_once()
    mock_api_client.previous_face.assert_awaited_once()
    mock_api_client.next_brightness.assert_awaited_once()
    mock_api_client.previous_brightness.assert_awaited_once()

async def test_wifi_scan_button(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)
    await hass.services.async_call(
        "button", "press", {"entity_id": "button.wi_fi_scan"}, blocking=True
    )
    mock_api_client.scan_wifi.assert_awaited_once()
    mock_api_client.get_status.assert_awaited()


async def test_llu_patients_button(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)
    await hass.services.async_call(
        "button", "press", {"entity_id": "button.libre_link_up_patients"}, blocking=True
    )
    mock_api_client.scan_llu_patients.assert_awaited_once()


async def test_logs_button(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)
    await hass.services.async_call(
        "button", "press", {"entity_id": "button.device_logs"}, blocking=True
    )
    mock_api_client.get_logs.assert_awaited_once()
    assert mock_api_client.get_status.await_count >= 2
