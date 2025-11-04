from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    DOMAIN, DEFAULT_SCAN_SECS, TEMP_REGS, STATUS_REGS, PERCENT_REGS,
    COUNTER_REGS32, SETPOINT_REGS, MODE_TOGGLE_REGS, DIFF_REGS, FEATURE_FLAGS
)

_LOGGER = logging.getLogger(__name__)

REG_BATCHES = [
    (0, 16),   # temps 0-15
    (16, 20),  # 16-35
    (27, 10),  # status 27-36
    (36, 4),   # counters hi/lo
    (40, 51),  # constants around 40-90
    (150, 4),  # 150+
]

class SpiralaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        data = {**entry.data, **entry.options}
        self.host = data["host"]
        self.port = data.get("port")
        self.unit_id = data.get("unit_id")
        self.scan_secs = data.get("scan_interval", DEFAULT_SCAN_SECS)
        self.client = AsyncModbusTcpClient(self.host, port=self.port)
        self._serial: str | None = None
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=self.scan_secs))

    async def async_config_entry_first_refresh(self):
        await self.client.connect()
        # Try to read and cache serial once at startup
        try:
            rr = await self.client.read_holding_registers(170, count=8, device_id=self.unit_id)
            if not rr.isError() and getattr(rr, "registers", None):
                self._serial = _decode_ascii(rr.registers, False)
                self._model = f"WW-{self._serial[0]}"
        except ModbusException as exc:
           _LOGGER.debug("Serial read failed on startup: %s", exc)
        return await super().async_config_entry_first_refresh()

    async def _async_update_data(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        unit = self.unit_id
        try:
            for start, count in REG_BATCHES:
                rr = await self.client.read_holding_registers(start, count=count, device_id=unit)
                if rr.isError():
                    _LOGGER.debug("Read error at %s len %s: %s", start, count, rr)
                    continue
                for i in range(count):
                    data[start + i] = rr.registers[i]

            # 32-bit assemble
            for name, hi_addr in COUNTER_REGS32.items():
                hi = data.get(hi_addr, 0)
                lo = data.get(hi_addr + 1, 0)
                data[name] = (hi << 16) | lo

            # Friendly aliases/scaling
            for k, addr in TEMP_REGS.items():
                raw = data.get(addr)
                data[k] = None if raw is None else raw / 256.0
            for k, addr in STATUS_REGS.items():
                data[k] = data.get(addr)
            for k, addr in PERCENT_REGS.items():
                data[k] = data.get(addr)
            for k, addr in SETPOINT_REGS.items():
                raw = data.get(addr)
                data[k] = None if raw is None else raw / 256.0
            for k, addr in DIFF_REGS.items():
                data[k] = data.get(addr)
            for k, addr in MODE_TOGGLE_REGS.items():
                data[k] = data.get(addr)
            for k, addr in FEATURE_FLAGS.items():
                data[k] = data.get(addr)

        except ModbusException as exc:
            _LOGGER.warning("Modbus exception: %s", exc)
          # Ensure serial is present for consumers; lazy-read if startup read failed
        
        if self._serial is None:
            try:
                rr = await self.client.read_holding_registers(170, count=8, device_id=self.unit_id)
                if not rr.isError() and getattr(rr, "registers", None):
                    self._serial = _decode_ascii(rr.registers, False)
            except ModbusException as exc:
                _LOGGER.debug("Serial read failed in update: %s", exc)
        data["serial_number"] = self._serial
        data["model"] = self._model
        return data

    async def async_write_register(self, address: int, value: int) -> None:
        await self.client.write_register(address, value, device_id=self.unit_id)

    async def async_close(self):
        self.client.close()

# --- helpers ---
def _decode_ascii(registers: list[int], swap_bytes: bool = False) -> str:
    _LOGGER.info(f"Raw serial {registers}")

    b = bytearray()
    for reg in registers:
        hi = (reg >> 8) & 0xFF
        lo = reg & 0xFF
        if swap_bytes:
            hi, lo = lo, hi
        b.append(hi)
        b.append(lo)
    # keep printable ASCII only; strip NULs/spaces
    s = "".join(chr(x) for x in b if 32 <= x <= 126).strip()
    return s