from __future__ import annotations

import socket
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import callback

from .const import DOMAIN, DEFAULT_PORT, DEFAULT_UNIT_ID, DEFAULT_SCAN_SECS

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("host"): str,
    vol.Optional("port", default=DEFAULT_PORT): int,
    vol.Optional("unit_id", default=DEFAULT_UNIT_ID): int,
    vol.Optional("scan_interval", default=DEFAULT_SCAN_SECS): int,
    vol.Optional("enable_cooling", default=True): bool,
    # vol.Optional("enable_dhw", default=True): bool,
    # vol.Optional("has_circuit_2", default=False): bool,
    vol.Optional("external_temp_sensor_installed", default=False): bool,
})

class SpiralaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input["host"]
            try:
                socket.gethostbyname(host)
            except socket.gaierror:
                errors["host"] = "cannot_connect"
            if not errors:
                await self.async_set_unique_id(f"{host}:{user_input['port']}:{user_input['unit_id']}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=f"Spirála @ {host}", data=user_input)
        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return SpiralaOptionsFlow(config_entry)

class SpiralaOptionsFlow(config_entries.OptionsFlowWithConfigEntry):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        super().__init__(config_entry)

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        data = {**self.config_entry.data, **(self.config_entry.options or {})}
        schema = vol.Schema({
            vol.Optional("scan_interval", default=data.get("scan_interval", DEFAULT_SCAN_SECS)): int,
            vol.Optional("enable_cooling", default=data.get("enable_cooling", True)): bool,
            # vol.Optional("enable_dhw", default=data.get("enable_dhw", True)): bool,
            # vol.Optional("has_circuit_2", default=data.get("has_circuit_2", False)): bool,
            vol.Optional("external_temp_sensor_installed", default=data.get("external_temp_sensor_installed", False)): bool,

        })
        if user_input is not None:
            return self.async_create_entry(title="Options", data=user_input)
        return self.async_show_form(step_id="init", data_schema=schema)
