"""Tests for NSClock sensor entities."""

from typing import Any
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def async_setup(hass: Any, entry: MockConfigEntry, client: Any) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_blood_glucose_sensor(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)
    state = hass.states.get("sensor.blood_glucose")
    assert state is not None
    assert state.state == "118"
    assert state.attributes["unit_of_measurement"] == "mg/dL"


async def test_zero_glucose_becomes_unknown(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    mock_api_client.get_status.return_value["sgv"] = 0
    await async_setup(hass, mock_config_entry, mock_api_client)
    state = hass.states.get("sensor.blood_glucose")
    assert state is not None
    assert state.state == "unknown"


async def test_data_source_sensor(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)
    state = hass.states.get("sensor.data_source")
    assert state is not None
    assert state.state == "NIGHTSCOUT"


async def test_source_status_sensor(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)
    state = hass.states.get("sensor.source_status")
    assert state is not None
    assert state.state == "connected"


async def test_firmware_version_sensor(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)
    state = hass.states.get("sensor.firmware_version")
    assert state is not None
    assert state.state == "1.2.3"


async def test_current_face_sensor(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    await async_setup(hass, mock_config_entry, mock_api_client)
    state = hass.states.get("sensor.current_face")
    assert state is not None
    assert state.state == "big_text"
