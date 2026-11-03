"""Config flow for the NSClock integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries

from . import api
from .const import CONF_HOST, CONF_PASSWORD, DOMAIN


class NightscoutClockConfigFlow(config_entries.ConfigFlow, domain="nsclock"):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            password = user_input.get(CONF_PASSWORD) or None
            await self.async_set_unique_id(f"nsclock-{host}")
            self._abort_if_unique_id_configured()
            client = api.NightscoutClockApiClient(host, *([password] if password else []))
            try:
                await client.get_status()
                auth = await client.get_auth_status()
                if auth.get("enabled") and password:
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
