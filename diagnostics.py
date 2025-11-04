from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "host": coordinator.host,
        "port": coordinator.port,
        "unit_id": coordinator.unit_id,
        "last_data": coordinator.data,
    }
