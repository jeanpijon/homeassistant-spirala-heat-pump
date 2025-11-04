from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODE_TOGGLE_REGS, THERMOSTAT_ENUM, MANUFACTURER, MODEL, DEVICE_NAME
from .coordinator import SpiralaCoordinator

OPTIONS = [THERMOSTAT_ENUM[i] for i in sorted(THERMOSTAT_ENUM.keys())]
VALUE_BY_OPTION = {v: k for k, v in THERMOSTAT_ENUM.items()}

class ThermostatModeSelect(CoordinatorEntity[SpiralaCoordinator], SelectEntity):
    def __init__(self, coordinator: SpiralaCoordinator, key: str, name: str, addr: int) -> None:
        super().__init__(coordinator)
        self._key = key
        self._addr = addr
        self._attr_unique_id = f"{coordinator.host}-{coordinator.port}-{coordinator.unit_id}-select-{key}"
        self._attr_has_entity_name = True
        self._attr_options = OPTIONS
        self._attr_translation_key = key

    @property
    def current_option(self) -> str | None:
        v = self.coordinator.data.get(self._key)
        return None if v is None else THERMOSTAT_ENUM.get(v)

    @property
    def device_info(self) -> DeviceInfo:
        serial = self.coordinator.data.get("serial_number") or "unknown"
        model = self.coordinator.data.get("model") or "unknown"
        return DeviceInfo(
            identifiers={(DOMAIN, serial)},
            manufacturer=MANUFACTURER,
            model=model,
            name=DEVICE_NAME,
            suggested_area="Technická místnost",
            serial_number=serial,
        )

    async def async_select_option(self, option: str) -> None:
        val = VALUE_BY_OPTION[option]
        await self.coordinator.async_write_register(self._addr, val)
        await self.coordinator.async_request_refresh()

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: SpiralaCoordinator = hass.data[DOMAIN][entry.entry_id]
    ents = [
        ThermostatModeSelect(coordinator, "thermostat_mode_1", "Spirala Thermostat Mode (Circuit 1)", MODE_TOGGLE_REGS["thermostat_mode_1"]),
    ]

    data = {**entry.data, **entry.options}
    if data.get("has_circuit_2", False):
        ents.append(ThermostatModeSelect(coordinator, "thermostat_mode_2", "Spirala Thermostat Mode (Circuit 2)", MODE_TOGGLE_REGS["thermostat_mode_2"]))
    async_add_entities(ents)
