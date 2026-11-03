"""Tests for the NSClock config flow."""

from typing import Any
from unittest.mock import AsyncMock

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nsclock.const import DOMAIN
from .conftest import TEST_HOST, TEST_PASSWORD


async def test_user_form_is_shown(hass: Any, mock_config_entry: MockConfigEntry) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}


async def test_successful_flow_without_password(hass: Any, mock_config_entry: MockConfigEntry, mock_api_client: Any) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": TEST_HOST})
    await hass.async_block_till_done()
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {"host": TEST_HOST}
    assert result["result"].unique_id == f"nsclock-{TEST_HOST}"


async def test_authentication_enabled_requires_password(
    hass: Any, mock_api_client: Any
) -> None:
    mock_api_client.get_auth_status.return_value = {
        "enabled": True,
        "authenticated": False,
        "hasPassword": True,
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": TEST_HOST}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "missing_password"}
    mock_api_client.login.assert_not_awaited()


async def test_successful_flow_with_password(hass: Any, mock_api_client: Any) -> None:
    mock_api_client.get_auth_status.return_value = {"enabled": True, "authenticated": False, "hasPassword": True}
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": TEST_HOST, "password": TEST_PASSWORD})
    await hass.async_block_till_done()
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {"host": TEST_HOST, "password": TEST_PASSWORD}


async def test_invalid_host_shows_error(hass: Any, mock_api_client: Any) -> None:
    mock_api_client.get_status = AsyncMock(side_effect=ConnectionError("offline"))
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": "192.0.2.1"})
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_invalid_password_shows_error(hass: Any, mock_api_client: Any) -> None:
    mock_api_client.get_auth_status.return_value = {"enabled": True, "authenticated": False, "hasPassword": True}
    mock_api_client.login.return_value = {"status": "invalid"}
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": TEST_HOST, "password": "wrong"})
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_reauth_updates_existing_entry_password(
    hass: Any, mock_api_client: Any
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="NSClock",
        unique_id=f"nsclock-{TEST_HOST}",
        data={"host": TEST_HOST, "password": "old-password"},
    )
    entry.add_to_hass(hass)
    mock_api_client.get_auth_status.return_value = {
        "enabled": True,
        "authenticated": False,
        "hasPassword": True,
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": entry.entry_id,
        },
        data=entry.data,
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"password": "new-password"}
    )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data == {"host": TEST_HOST, "password": "new-password"}
    mock_api_client.login.assert_awaited_once_with("new-password")


async def test_reauth_rejects_invalid_password(
    hass: Any, mock_api_client: Any
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="NSClock",
        unique_id=f"nsclock-{TEST_HOST}",
        data={"host": TEST_HOST, "password": "old-password"},
    )
    entry.add_to_hass(hass)
    mock_api_client.get_auth_status.return_value = {
        "enabled": True,
        "authenticated": False,
        "hasPassword": True,
    }
    mock_api_client.login.return_value = {"status": "invalid"}

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": entry.entry_id,
        },
        data=entry.data,
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"password": "wrong-password"}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "invalid_auth"}
    assert entry.data["password"] == "old-password"


async def test_duplicate_host_aborts(hass: Any, mock_api_client: Any) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN, title="NSClock",
        unique_id=f"nsclock-{TEST_HOST}",
        data={"host": TEST_HOST},
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": TEST_HOST})
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
