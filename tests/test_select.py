"""Tests for NSClock select entities."""

from typing import Any

from pytest_homeassistant_custom_component.common import MockConfigEntry


async def async_setup(hass: Any, entry: MockConfigEntry, client: Any) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_face_select_options(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)
    state = hass.states.get("select.face")
    assert state is not None
    assert state.attributes["options"] == ["Big Text", "Unicorn"]


async def test_face_select_current_option(
    hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any
) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)
    state = hass.states.get("select.face")
    assert state.state == "Big Text"


async def test_face_select_switches_face(
    hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any
) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.face", "option": "Unicorn"},
        blocking=True,
    )
    mock_api_client.set_face.assert_awaited_once_with("unicorn")
