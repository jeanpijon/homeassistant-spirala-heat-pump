from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, IO_BITS, RELAY_BITS, MANUFACTURER, MODEL, DEVICE_NAME
from .coordinator import SpiralaCoordinator

class BitBinarySensor(CoordinatorEntity[SpiralaCoordinator], BinarySensorEntity):
    def __init__(self, coordinator: SpiralaCoordinator, key_word: str, bit_name: str, bit_index: int) -> None:
        super().__init__(coordinator)
        self._word_key = key_word  # "io_state" or "relay_state"
        # self._bit_name = bit_name
        self._bit_index = bit_index
        self._attr_translation_key = bit_name
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.host}-{coordinator.port}-{coordinator.unit_id}-bin-{key_word}-{bit_name}"
        # self._attr_name = f"Spirala {bit_name.replace('_',' ').title()}"

    @property
    def is_on(self) -> bool | None:
        word = self.coordinator.data.get(self._word_key)
        if word is None:
            return None
        return bool((word >> self._bit_index) & 1)

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
    ents = []
    for name, bit in IO_BITS:
        if name == "io_control_2":
            if coordinator.data.get("has_circuit_2"):
                ents.append(BitBinarySensor(coordinator, "io_state", name, bit))
        else:
            ents.append(BitBinarySensor(coordinator, "io_state", name, bit))
    for name, bit in RELAY_BITS:
        if name == "relay_pump_circuit2":
            if coordinator.data.get("has_circuit_2"):
                ents.append(BitBinarySensor(coordinator, "relay_state", name, bit))
        elif name == "relay_dhw":
            if coordinator.data.get("enable_dhw"):
                ents.append(BitBinarySensor(coordinator, "relay_state", name, bit))
        else:
            ents.append(BitBinarySensor(coordinator, "relay_state", name, bit))
    async_add_entities(ents)
