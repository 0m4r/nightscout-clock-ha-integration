"""Tests for integration setup and unloading."""

from typing import Any
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_setup_entry_creates_entities(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is __import__("homeassistant.config_entries", fromlist=["ConfigEntryState"]).ConfigEntryState.LOADED
    assert hass.states.get("select.brightness_mode_setting") is not None
    assert hass.states.get("number.brightness_level_setting") is not None
    assert hass.states.get("text.clock_name_setting") is not None
    assert hass.services.has_service("nsclock", "apply_settings")


async def test_unload_entry(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is __import__("homeassistant.config_entries", fromlist=["ConfigEntryState"]).ConfigEntryState.NOT_LOADED


async def test_setup_fails_when_status_is_unavailable(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    mock_api_client.get_status = AsyncMock(side_effect=ConnectionError("offline"))
    mock_config_entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()


async def test_apply_settings_service_applies_selected_device(
    hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any
) -> None:
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.brightness_mode_setting", "option": "auto_dimmed"},
        blocking=True,
    )
    with patch(
        "custom_components.nsclock.coordinator.asyncio.sleep",
        new_callable=AsyncMock,
    ):
        await hass.services.async_call(
            "nsclock",
            "apply_settings",
            {"entity_id": "select.brightness_mode_setting"},
            blocking=True,
        )

    saved_config = mock_api_client.save_config.await_args.args[0]
    assert saved_config["brightness_mode"] == "auto_dimmed"
