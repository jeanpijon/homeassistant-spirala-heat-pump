from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfTemperature

from .const import DOMAIN, SETPOINT_REGS, DIFF_REGS, MANUFACTURER, MODEL, DEVICE_NAME
from .coordinator import SpiralaCoordinator
import logging

# _LOGGER = logging.getLogger(__name__)
SETPOINT_META = {
    "setpoint_1": {"name": "Spirala Setpoint Circuit 1", "min": 0, "max": 80, "step": 0.5},
    "setpoint_dhw": {"name": "Spirala Setpoint DHW", "min": 0, "max": 80, "step": 0.5},

}

SETPOINT_META2 = {
    "setpoint_2": {"name": "Spirala Setpoint Circuit 2", "min": 0, "max": 80, "step": 0.5},
}

DIFF_META = {
    "diff_circuit_1": {"name": "Diff Circuit 1", "min": 1, "max": 25, "step": 1},
    "diff_dhw":       {"name": "Diff DHW", "min": 1, "max": 25, "step": 1},
    "setpoint_circuit_1_hours_rotation": {"name": "Spirala Rotation after stop circuit 1", "min": 1, "max": 125, "step": 1},
}

DIFF_META2 = {
    "diff_circuit_2": {"name": "Diff Circuit 2", "min": 0, "max": 25, "step": 1},
}


class SpiralaNumber(CoordinatorEntity[SpiralaCoordinator], NumberEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: SpiralaCoordinator, key: str, meta: dict) -> None:
        super().__init__(coordinator)
        self._key = key
        self._addr = SETPOINT_REGS[key]
        self._attr_unique_id = f"{coordinator.host}-{coordinator.port}-{coordinator.unit_id}-number-{key}"
        self._attr_has_entity_name = True
        self._attr_native_min_value = meta["min"]
        self._attr_native_max_value = meta["max"]
        self._attr_native_step = meta["step"]
        self._attr_icon = "mdi:thermometer"
        self._attr_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_translation_key = key

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)

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

    async def async_set_native_value(self, value: float) -> None:
        raw = int(round(value * 256))
        await self.coordinator.async_write_register(self._addr, raw)
        await self.coordinator.async_request_refresh()

class SpiralaDiffNumber(CoordinatorEntity[SpiralaCoordinator], NumberEntity):
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, key, meta, addr):
        super().__init__(coordinator)
        self._key = key
        self._addr = addr
        self._attr_has_entity_name = True
        self._attr_unique_id = (
            f"{coordinator.host}-{coordinator.port}-{coordinator.unit_id}-number-{key}"
        )
        self._attr_translation_key = key
        self._attr_native_min_value = meta["min"]
        self._attr_native_max_value = meta["max"]
        self._attr_native_step = meta["step"]

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)

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

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write_register(self._addr, int(value))
        await self.coordinator.async_request_refresh()

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: SpiralaCoordinator = hass.data[DOMAIN][entry.entry_id]
    ents = [SpiralaNumber(coordinator, key, meta) for key, meta in SETPOINT_META.items()]
    for key, meta in DIFF_META.items():
        ents.append(SpiralaDiffNumber(coordinator, key, DIFF_META[key], DIFF_REGS[key]))
    # _LOGGER.error(f"DataX: {coordinator.data.get('has_circuit_2', True)}")
    data = {**entry.data, **entry.options}
    if data.get("has_circuit_2", False):
        for key, meta in SETPOINT_META2.items():
            ents.append(SpiralaNumber(coordinator, key, SETPOINT_META2[key]))
        for key, meta in DIFF_META2.items():
            ents.append(SpiralaDiffNumber(coordinator, key, DIFF_META2[key], DIFF_REGS[key]))
    async_add_entities(ents)
