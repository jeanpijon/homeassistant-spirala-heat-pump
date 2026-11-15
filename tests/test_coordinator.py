"""Coordinator behaviour against a fake Modbus client: decoding and failure handling."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed
from pymodbus.exceptions import ConnectionException, ModbusIOException
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.spirala_heat_pump.const import DOMAIN
from custom_components.spirala_heat_pump.coordinator import SpiralaCoordinator, _decode_ascii


class Response:
    def __init__(self, registers=None, error=False):
        self.registers = registers or []
        self._error = error

    def isError(self):
        return self._error


class FakeClient:
    """Stands in for AsyncModbusTcpClient. mode: ok | silent | refused | error."""

    mode = "ok"
    regs: dict[int, int] = {}
    fail_batches: set[int] = set()

    def __init__(self, host, port=None):
        pass

    async def connect(self):
        return True

    def close(self):
        pass

    async def write_register(self, address, value, device_id=None):
        self.regs[address] = value

    async def read_holding_registers(self, address, count=1, device_id=None):
        if self.mode == "silent":
            raise ModbusIOException("No response received after 3 retries")
        if self.mode == "refused":
            raise ConnectionException("Not connected")
        if self.mode == "error" or address in self.fail_batches:
            return Response(error=True)
        return Response([self.regs.get(address + i, 0) for i in range(count)])


def ascii_regs(text: str) -> list[int]:
    data = text.encode().ljust(16, b"\0")
    return [(data[i] << 8) | data[i + 1] for i in range(0, 16, 2)]


@pytest.fixture
def device():
    FakeClient.mode = "ok"
    FakeClient.fail_batches = set()
    FakeClient.regs = {
        0: int(21.5 * 256), 1: int(40.0 * 256), 2: int(54.7 * 256),
        10: int(28.6 * 256), 11: int(23.5 * 256),
        18: int(35 * 256), 19: int(30 * 256), 20: int(50 * 256),
        27: 0, 28: 4, 31: 3,
        36: 1, 37: 5,          # starts_count = 65541
        38: 0, 39: 1234,       # runtime_hours = 1234
        41: 2, 40: 1, 56: 0,
    }
    for i, reg in enumerate(ascii_regs("7A123456")):
        FakeClient.regs[170 + i] = reg
    return FakeClient


@pytest.fixture
async def coordinator(hass, device):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "192.0.2.1", "port": 4196, "unit_id": 60, "scan_interval": 1},
    )
    entry.add_to_hass(hass)
    with patch("custom_components.spirala_heat_pump.coordinator.AsyncModbusTcpClient", FakeClient):
        yield SpiralaCoordinator(hass, entry)


def test_decode_ascii_strips_padding():
    assert _decode_ascii([0x4142, 0x4300]) == "ABC"


def test_decode_ascii_swapped_bytes():
    assert _decode_ascii([0x4241], swap_bytes=True) == "AB"


async def test_update_decodes_registers(coordinator):
    data = await coordinator._async_update_data()
    assert data["dhw_tank_temp"] == pytest.approx(54.7, abs=0.01)
    assert data["supply_temp"] == pytest.approx(28.6, abs=0.01)
    assert data["setpoint_dhw"] == 50.0
    assert data["starts_count"] == (1 << 16) | 5
    assert data["runtime_hours"] == 1234
    assert data["error_code"] == 0
    assert data["not_running_reason"] == 4
    assert data["active_circuit"] == 3
    assert data["serial_number"] == "7A123456"
    assert data["model"] == "WW-7"


async def test_silent_device_raises_update_failed(coordinator, device):
    device.mode = "silent"
    with pytest.raises(UpdateFailed, match="No Modbus reply"):
        await coordinator._async_update_data()


async def test_connection_refused_raises_update_failed(coordinator, device):
    device.mode = "refused"
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_error_responses_everywhere_raise_update_failed(coordinator, device):
    device.mode = "error"
    with pytest.raises(UpdateFailed, match="answered every read with an error"):
        await coordinator._async_update_data()


async def test_one_failing_batch_keeps_the_rest(coordinator, device):
    device.fail_batches = {150}
    data = await coordinator._async_update_data()
    assert data["dhw_tank_temp"] == pytest.approx(54.7, abs=0.01)
    assert data["thermostat_mode_2"] is None


async def test_entities_unavailable_while_silent_and_recover(coordinator, device):
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    device.mode = "silent"
    await coordinator.async_refresh()
    assert not coordinator.last_update_success
    device.mode = "ok"
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert coordinator.data["dhw_tank_temp"] == pytest.approx(54.7, abs=0.01)
