"""Fake Modbus device shared by the coordinator and setup tests."""
from __future__ import annotations

from pymodbus.exceptions import ConnectionException, ModbusIOException


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
    serial_failures = 0          # answer the serial registers with an error this many times
    instances: list["FakeClient"] = []

    def __init__(self, host, port=None):
        self.closed = False
        FakeClient.instances.append(self)

    async def connect(self):
        return True

    def close(self):
        self.closed = True

    async def write_register(self, address, value, device_id=None):
        self.regs[address] = value

    async def read_holding_registers(self, address, count=1, device_id=None):
        if self.mode == "silent":
            raise ModbusIOException("No response received after 3 retries")
        if self.mode == "refused":
            raise ConnectionException("Not connected")
        if address == 170 and FakeClient.serial_failures > 0:
            FakeClient.serial_failures -= 1
            return Response(error=True)
        if self.mode == "error" or address in self.fail_batches:
            return Response(error=True)
        return Response([self.regs.get(address + i, 0) for i in range(count)])


def ascii_regs(text: str) -> list[int]:
    data = text.encode().ljust(16, b"\0")
    return [(data[i] << 8) | data[i + 1] for i in range(0, 16, 2)]
