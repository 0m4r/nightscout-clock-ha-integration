"""Tests for the NSClock data update coordinator."""

from typing import Any
from unittest.mock import AsyncMock

from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nsclock.api import NightscoutClockApiClient
from custom_components.nsclock.api import NightscoutClockApiError
from custom_components.nsclock.coordinator import NightscoutClockCoordinator

TEST_HOST = "192.168.1.50"


async def make_coordinator(
    hass: Any, config_entry: MockConfigEntry, client: Any = None
) -> NightscoutClockCoordinator:
    config_entry.add_to_hass(hass)
    if client is None:
        client = NightscoutClockApiClient(TEST_HOST, None)
    return NightscoutClockCoordinator(hass, config_entry, client)


async def test_coordinator_refresh_success(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    coordinator = await make_coordinator(hass, mock_config_entry, mock_api_client)
    data = await coordinator._async_update_data()
    assert data["status"]["sgv"] == 118
    assert data["firmware_version"] == "1.2.3"
    assert data["config"]["clock_name"] == "Test Clock"


async def test_cached_config_remains_available_between_refreshes(
    hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any
) -> None:
    coordinator = await make_coordinator(hass, mock_config_entry, mock_api_client)
    first_data = await coordinator._async_update_data()
    second_data = await coordinator._async_update_data()

    assert first_data["config"]["clock_name"] == "Test Clock"
    assert second_data["config"]["clock_name"] == "Test Clock"
    assert mock_api_client.get_config.await_count == 1


async def test_cached_firmware_version_remains_available_between_refreshes(
    hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any
) -> None:
    coordinator = await make_coordinator(hass, mock_config_entry, mock_api_client)
    first_data = await coordinator._async_update_data()
    coordinator.data = first_data
    second_data = await coordinator._async_update_data()

    assert first_data["firmware_version"] == "1.2.3"
    assert second_data["firmware_version"] == "1.2.3"
    assert mock_api_client.get_version.await_count == 1


async def test_missing_revision_endpoint_does_not_fail_refresh(
    hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any
) -> None:
    mock_api_client.get_revision.side_effect = NightscoutClockApiError("not found")
    coordinator = await make_coordinator(hass, mock_config_entry, mock_api_client)

    data = await coordinator._async_update_data()

    assert data["firmware_version"] == "1.2.3"
    assert "firmware_revision" not in data


async def test_unavailable_face_endpoint_uses_retry_interval(
    hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any
) -> None:
    mock_api_client.get_faces.side_effect = NightscoutClockApiError("not found")
    coordinator = await make_coordinator(hass, mock_config_entry, mock_api_client)

    await coordinator._async_update_data()
    await coordinator._async_update_data()

    mock_api_client.get_faces.assert_awaited_once()


async def test_zero_glucose_maps_to_none(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    mock_api_client.get_status.return_value["sgv"] = 0
    coordinator = await make_coordinator(hass, mock_config_entry, mock_api_client)
    data = await coordinator._async_update_data()
    assert data["status"]["sgv"] is None


async def test_connection_error_raises_update_failed(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    mock_api_client.get_status = AsyncMock(side_effect=ConnectionError("offline"))
    coordinator = await make_coordinator(hass, mock_config_entry, mock_api_client)
    try:
        await coordinator._async_update_data()
    except UpdateFailed:
        pass
    else:
        raise AssertionError("Expected UpdateFailed")


async def test_auth_failure_propagates_for_reauthentication(
    hass: Any, authenticated_config_entry: MockConfigEntry, mock_api_client: Any
) -> None:
    mock_api_client.get_status.side_effect = ConfigEntryAuthFailed("bad credentials")
    coordinator = await make_coordinator(hass, authenticated_config_entry, mock_api_client)
    try:
        await coordinator._async_update_data()
    except ConfigEntryAuthFailed:
        pass
    else:
        raise AssertionError("Expected ConfigEntryAuthFailed")


async def test_stage_and_apply_adds_new_config_keys(
    hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any
) -> None:
    coordinator = await make_coordinator(hass, mock_config_entry, mock_api_client)
    coordinator._config_cache = {
        "clock_name": "Test Clock",
        "alarm_high_value": 180,
        "low_urgent_mgdl": 54,
        "high_urgent_mgdl": 250,
        "custom_nodatatimer": 30,
        "custom_nodatatimer_enable": True,
        "face_cycle_enabled": True,
        "alarm_repeat_interval_seconds": 600,
        "bg_color_normal": "green",
        "bg_color_urgent_low": "yellow",
    }
    # Stage the same values so the apply service has staged settings to write.
    for key, value in coordinator._config_cache.items():
        coordinator.stage_config_value(key, value)
    await coordinator.async_apply_settings()

    assert mock_api_client.get_config.await_count == 2
    # One initial fetch plus one during apply.
    assert mock_api_client.get_config.await_count == 2

    # The staged values must be merged into the full config before saving.
    save_call = mock_api_client.save_config.await_args_list[0]
    saved = save_call[0][0]  # positional arg: the full config dict
    assert saved["low_urgent_mgdl"] == 54
    assert saved["high_urgent_mgdl"] == 250
    assert saved["custom_nodatatimer"] == 30
    assert saved["face_cycle_enabled"] is True
    assert saved["alarm_repeat_interval_seconds"] == 600
    assert saved["bg_color_normal"] == "green"
    assert saved["bg_color_urgent_low"] == "yellow"


async def test_staging_unsupported_config_key_raises(
    hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any
) -> None:
    coordinator = await make_coordinator(hass, mock_config_entry, mock_api_client)
    try:
        coordinator.stage_config_value("some_unknown_key", True)
    except HomeAssistantError:
        pass
    else:
        raise AssertionError("Expected HomeAssistantError")
