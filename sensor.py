from __future__ import annotations

from homeassistant.components.sensor import SensorEntity

from homeassistant.const import UnitOfTemperature
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN, TEMP_REGS, ACTIVE_CIRCUIT_ENUM, ERROR_ENUM, NOT_RUNNING_ENUM, MANUFACTURER, MODEL, DEVICE_NAME
)
from .coordinator import SpiralaCoordinator

SENSOR_DESCRIPTORS = []
for key in TEMP_REGS.keys():
    SENSOR_DESCRIPTORS.append({
        "key": key,
        "name": f"Spirala {key.replace('_', ' ').title()}",
        "unit": UnitOfTemperature.CELSIUS,
        "icon": "mdi:thermometer",
        "device_class": SensorDeviceClass.TEMPERATURE,
    })

SENSOR_DESCRIPTORS += [
    {"key": "starts_count", "name": "Spirala Starts Count", "unit": None, "icon": "mdi:counter"},
    {"key": "runtime_hours", "name": "Spirala Runtime Hours", "unit": "h", "icon": "mdi:clock-outline"},
    {"key": "error_code", "name": "Spirala Error", "unit": None, "icon": "mdi:alert"},
    {"key": "not_running_reason", "name": "Spirala Not Running", "unit": None, "icon": "mdi:pause-octagon"},
    {"key": "active_circuit", "name": "Spirala Active Circuit", "unit": None, "icon": "mdi:selection-ellipse-arrow-inside", "device_class": SensorDeviceClass.ENUM, "options": list(ACTIVE_CIRCUIT_ENUM.values())},
    # {"key": "io_state", "name": "Spirala IO State", "unit": None, "icon": "mdi:gpio"},
    # {"key": "relay_state", "name": "Spirala Relay State", "unit": None, "icon": "mdi:toggle-switch"},
]

class SpiralaSensor(CoordinatorEntity[SpiralaCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: SpiralaCoordinator, d: dict) -> None:
        super().__init__(coordinator)
        self._key = d["key"]
        self._attr_unique_id = f"{coordinator.host}-{coordinator.port}-{coordinator.unit_id}-sensor-{self._key}"
        self._attr_has_entity_name = True
        self._attr_icon = d.get("icon")
        self._attr_device_class = d.get("device_class")
        self._attr_translation_key = d["key"]
        if d.get("device_class") != SensorDeviceClass.ENUM:
            self._attr_native_unit_of_measurement = d.get("unit")
            # Enum sensors: no unit, but provide options
        else:
            self._attr_options = d.get("options", [])
        # self._attr_native_value =


    @property
    def native_value(self):
        val = self.coordinator.data.get(self._key)
        if self._key == "error_code":
            return ERROR_ENUM.get(val) if val is not None else None
        if self._key == "not_running_reason":
            return NOT_RUNNING_ENUM.get(val) if val is not None else None
        if self._key == "active_circuit":
            return ACTIVE_CIRCUIT_ENUM.get(val) if val is not None else None
        return val

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

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator: SpiralaCoordinator = hass.data[DOMAIN][entry.entry_id]
    ents = [SpiralaSensor(coordinator, d) for d in SENSOR_DESCRIPTORS]
    async_add_entities(ents)
