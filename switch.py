from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODE_TOGGLE_REGS, MANUFACTURER, MODEL, DEVICE_NAME
from .coordinator import SpiralaCoordinator

class RegisterSwitch(CoordinatorEntity[SpiralaCoordinator], SwitchEntity):
    def __init__(self, coordinator: SpiralaCoordinator, key: str, name: str, addr: int) -> None:
        super().__init__(coordinator)
        self._key = key
        self._addr = addr
        self._attr_unique_id = f"{coordinator.host}-{coordinator.port}-{coordinator.unit_id}-switch-{key}"
        self._attr_has_entity_name = True
        self._attr_translation_key = key

    @property
    def is_on(self) -> bool | None:
        v = self.coordinator.data.get(self._key)
        return None if v is None else bool(v)

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

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_write_register(self._addr, 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_write_register(self._addr, 0)
        await self.coordinator.async_request_refresh()

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: SpiralaCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = {**entry.data, **entry.options}
    ents = []
    if data.get("enable_cooling", True):
        ents.append(RegisterSwitch(coordinator, "cooling_enable", "Spirala Cooling Enable", MODE_TOGGLE_REGS["cooling_enable"]))
    if data.get("enable_dhw", True):
        ents.append(RegisterSwitch(coordinator, "dhw_enable", "Spirala DHW Enable", MODE_TOGGLE_REGS["dhw_enable"]))
    async_add_entities(ents)
