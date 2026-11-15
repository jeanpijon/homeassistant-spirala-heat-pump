"""Power-outage behaviour: the unit (or its gateway) comes up after Home Assistant."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed

from custom_components.spirala_heat_pump.const import DOMAIN
from tests.fakes import FakeClient, ascii_regs

RETRY = timedelta(minutes=3)


@pytest.fixture
def device():
    FakeClient.mode = "ok"
    FakeClient.fail_batches = set()
    FakeClient.serial_failures = 0
    FakeClient.instances = []
    FakeClient.regs = {
        0: int(21.5 * 256), 2: int(54.7 * 256), 10: int(28.6 * 256), 11: int(23.5 * 256),
        27: 0, 28: 4, 31: 3, 87: 1, 88: 0, 89: 0, 90: 1,   # DHW and circuit 2 present
    }
    for i, reg in enumerate(ascii_regs("7A123456")):
        FakeClient.regs[170 + i] = reg
    return FakeClient


@pytest.fixture
async def entry(hass, device):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "192.0.2.1", "port": 4196, "unit_id": 60, "scan_interval": 1},
    )
    entry.add_to_hass(hass)
    with patch("custom_components.spirala_heat_pump.coordinator.AsyncModbusTcpClient", FakeClient), patch(
        "custom_components.spirala_heat_pump.coordinator.SERIAL_RETRY_DELAY", 0
    ):
        yield entry


async def start(hass, entry):
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def retry(hass):
    async_fire_time_changed(hass, dt_util.utcnow() + RETRY)
    await hass.async_block_till_done(wait_background_tasks=True)


def unique_ids(hass, entry):
    return {e.unique_id for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)}


async def test_unit_off_at_start_is_retried_until_it_answers(hass, entry, device):
    device.mode = "silent"
    await start(hass, entry)
    assert entry.state is ConfigEntryState.SETUP_RETRY

    device.mode = "ok"
    await retry(hass)
    assert entry.state is ConfigEntryState.LOADED
    assert len(unique_ids(hass, entry)) > 20


async def test_failed_attempts_do_not_leak_gateway_connections(hass, entry, device):
    device.mode = "silent"
    await start(hass, entry)
    await retry(hass)
    await retry(hass)
    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert len(device.instances) >= 3
    assert all(client.closed for client in device.instances)


async def test_half_booted_unit_does_not_create_a_partial_entity_set(hass, entry, device):
    device.fail_batches = {40}          # configuration registers 40-90 not answered yet
    await start(hass, entry)
    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert not unique_ids(hass, entry)

    device.fail_batches = set()
    await retry(hass)
    assert entry.state is ConfigEntryState.LOADED
    ids = unique_ids(hass, entry)
    assert any(i.endswith("relay_pump_circuit2") for i in ids)
    assert any(i.endswith("relay_dhw") for i in ids)


async def test_late_serial_number_does_not_create_an_unknown_device(hass, entry, device):
    device.serial_failures = 2          # controller answers registers but not the serial yet
    await start(hass, entry)
    assert entry.state is ConfigEntryState.LOADED
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    identifiers = {i for d in devices for i in d.identifiers}
    assert (DOMAIN, "7A123456") in identifiers
    assert (DOMAIN, "unknown") not in identifiers
