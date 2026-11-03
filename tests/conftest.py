"""Shared fixtures for NSClock Home Assistant integration tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

import custom_components.nsclock.api as nsclock_api

DOMAIN = "nsclock"
TEST_HOST = "192.168.1.50"
TEST_PASSWORD = "test-password"
TEST_UNIQUE_ID = "nsclock-test-device"


TEST_UNIQUE_ID = "nsclock-test-device"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> Generator[None, None, None]:
    yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    return MockConfigEntry(domain=DOMAIN, title="NSClock", unique_id=TEST_UNIQUE_ID, data={"host": TEST_HOST}, options={})


@pytest.fixture
def authenticated_config_entry() -> MockConfigEntry:
    return MockConfigEntry(domain=DOMAIN, title="NSClock", unique_id=TEST_UNIQUE_ID, data={"host": TEST_HOST, "password": TEST_PASSWORD}, options={})


@pytest.fixture
def mock_api_client() -> Generator[Any, None, None]:
    """Mock the NSClock API client so no real HTTP requests are made."""
    with patch.object(nsclock_api, "NightscoutClockApiClient") as mock_client_class:
        client = mock_client_class.return_value
        
        status_data = {
            "isConnected": True,
            "hasInternet": True,
            "isInAPMode": False,
            "bgSource": "NIGHTSCOUT",
            "bgSourceStatus": "connected",
            "sgv": 118,
        }

        client.get_status = AsyncMock(return_value=status_data)
        client.get_version = AsyncMock(return_value="1.2.3")
        client.get_auth_status = AsyncMock(
            return_value={"enabled": False, "authenticated": True, "hasPassword": False}
        )
        client.login = AsyncMock(return_value={"status": "ok"})
        client.set_display_power = AsyncMock(return_value={"status": "ok"})
        client.play_alarm = AsyncMock(return_value={"status": "ok"})
        client.restart = AsyncMock(return_value={"status": "ok"})
        client.get_config = AsyncMock(
            return_value={
                "brightness_mode": "manual",
                "brightness_level": 50,
                "time_format": "24",
                "clock_name": "Test Clock",
                "alarm_high_enabled": True,
                "alarm_low_enabled": True,
                "alarm_urgent_low_enabled": False,
                "alarm_high_value": 250,
                "alarm_low_value": 70,
                "alarm_urgent_low_value": 55,
                "api_secret": "preserve-this-hidden-value",
                "wifi_password": "preserve-this-hidden-password",
            }
        )
        client.save_config = AsyncMock(return_value={"status": "ok"})

        yield client
