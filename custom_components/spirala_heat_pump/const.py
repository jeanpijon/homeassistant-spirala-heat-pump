from __future__ import annotations

DOMAIN = "spirala_heat_pump"
MANUFACTURER = "Spirala"
MODEL = "Spirala"
DEVICE_NAME = "Spirala Heat Pump"
PLATFORMS = ["sensor", "number", "switch", "select", "binary_sensor"]
DEFAULT_PORT = 4196
DEFAULT_UNIT_ID = 60
DEFAULT_SCAN_SECS = 1

# Register map (from Spirála Modbus sheet)
TEMP_REGS = {
    "tank_temp_1": 0,
    "tank_temp_2": 1,
    "dhw_tank_temp": 2,
    # "outdoor_temp": 3,
    "supply_temp": 10,
    "return_temp": 11,
}

STATUS_REGS = {
    "error_code": 27,
    "not_running_reason": 28,
    "io_state": 29,
    "relay_state": 30,
    "active_circuit": 31,
}

PERCENT_REGS = {
    "injector_valve_pct": 32,
    "cold_pump_pct": 33,
}

COUNTER_REGS32 = {
    "starts_count": 36,  # 36-37
    "runtime_hours": 38,  # 38-39
}

SETPOINT_REGS = {
    "setpoint_1": 18,
    "setpoint_2": 19,
    "setpoint_dhw": 20,
}

MODE_TOGGLE_REGS = {
    "thermostat_mode_1": 41,
    "thermostat_mode_2": 151,
    "cooling_enable": 56,
    "dhw_enable": 40,
}

TIME_REGS = {
    # key: (address, "seconds" | "minutes")
    "pump_overrun":      (None, "seconds"),   # e.g., pump overrun after compressor stop
    "anti_cycle_time":   (None, "minutes"),   # e.g., min time between compressor starts
    "pump_min_run":      (None, "seconds"),   # e.g., min circulation pump runtime
    "pump_post_defrost": (None, "seconds"),   # e.g., circulation after defrost
}

# bit definitions for io_state (reg 29)
IO_BITS = [
    ("io_hdo", 0),
    ("io_preso_evap", 1),
    ("io_preso_cond", 2),
    ("io_control_1", 3),
    ("io_control_2", 4),
    ("io_contactor", 5),
    ("io_valve", 6),
]

# bit definitions for relay_state (reg 30)
RELAY_BITS = [
    ("relay_pump_circuit2", 0),
    ("relay_dhw", 1),
    ("relay_bivalence", 2),
    ("relay_radiators", 3),
    ("relay_primary_pump", 4),
    # ("relay_fault", 5),
    ("relay_cooling", 6),
    ("relay_pump_circuit1", 7),
]

ERROR_ENUM = {
    0: "ok", 1: "sensor_internal_1", 2: "sensor_internal_2", 3: "sensor_internal_3",
    4: "sensor_internal_4", 5: "sensor_internal_5", 8: "actuator_error",
    9: "evaporator_pressure", 10: "condenser_pressure", 11: "max_temp_reached",
    12: "freeze_warning", 13: "hot_compressor", 14: "sensor_dhw_external",
    15: "defrost_error", 16: "hdo_loss", 17: "control_loss", 18: "setpoint_reached",
    19: "primary_flow_lost", 20: "water_on_floor", 21: "well_level", 23: "power_loss",
    24: "phase_order?", 26: "compressor_stopped", 28: "cold_pump_fault",
}

NOT_RUNNING_ENUM = {
    0: "active_circuit", 1: "heated", 2: "cold_input", 3: "start_in",
    4: "no_run_request", 5: "expensive_tariff", 6: "thermostat_selection",
    7: "call_manufacturer", 8: "frost_test", 9: "primary_flush",
    10: "water_on_floor", 11: "well_level", 12: "preparing_start",
    13: "fm_no_comm", 14: "actuator_error", 15: "rm_no_comm",
    16: "fm_cold_error", 17: "cooling", 18: "hot_output", 19: "bad_compressor_code",
}

ACTIVE_CIRCUIT_ENUM = {0: "none", 1: "circuit_1", 2: "circuit_2", 3: "dhw"}
THERMOSTAT_ENUM = {0: "machine", 1: "opentherm", 2: "equitherm", 3: "room", 4: "remote"}

DIFF_REGS = {
    "diff_circuit_1":  44,  # Diference okruhu 1
    "diff_circuit_2":  81,  # Diference okruhu 2
    "diff_dhw":        52,  # Diference TUV
}

FEATURE_FLAGS = {
    "enable_dhw": 87,
    "has_passive_cooling": 88,
    "has_separate_cooling_circuit": 89,
    "has_circuit_2": 90,
}
