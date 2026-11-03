"""Config flow for the NSClock integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import api
from .const import CONF_HOST, CONF_PASSWORD, DOMAIN


class NightscoutClockConfigFlow(config_entries.ConfigFlow, domain="nsclock"):
    VERSION = 1

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Start reauthentication for an existing clock entry."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Validate and save a replacement web password."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()

        if user_input is not None:
            password = user_input[CONF_PASSWORD]
            client = api.NightscoutClockApiClient(
                entry.data[CONF_HOST],
                password,
                session=async_get_clientsession(self.hass),
            )
            try:
                await client.get_status()
                auth = await client.get_auth_status()
                if not auth.get("enabled"):
                    errors["base"] = "auth_not_enabled"
                else:
                    result = await client.login(password)
                    if result.get("status") != "ok":
                        errors["base"] = "invalid_auth"
            except ConfigEntryAuthFailed:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_PASSWORD: password},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            password = user_input.get(CONF_PASSWORD) or None
            await self.async_set_unique_id(f"nsclock-{host}")
            self._abort_if_unique_id_configured()
            client = api.NightscoutClockApiClient(
                host, password, session=async_get_clientsession(self.hass)
            )
            try:
                await client.get_status()
                auth = await client.get_auth_status()
                if auth.get("enabled"):
                    if not password:
                        errors["base"] = "missing_password"
                    else:
                        result = await client.login(password)
                        if result.get("status") != "ok":
                            errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"
            if not errors:
                data = {CONF_HOST: host}
                if password:
                    data[CONF_PASSWORD] = password
                return self.async_create_entry(title="NSClock", data=data)
        return self.async_show_form(step_id="user", data_schema=vol.Schema({vol.Required(CONF_HOST): str, vol.Optional(CONF_PASSWORD): str}), errors=errors)
