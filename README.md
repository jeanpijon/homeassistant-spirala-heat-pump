# Spirála Heat Pump – Home Assistant Integration

This custom component integrates **Tepelná čerpadla Spirála** heat pumps with Home Assistant via Modbus RTU/TCP.

It provides real-time monitoring and control of heating, domestic hot water (DHW), and passive cooling functions, automatically detecting the hardware configuration from the controller.

---

## 🌡️ Features

| Category | Description |
|-----------|--------------|
| **Temperature Sensors** | Reads all main temperatures (tank, DHW, outlet/inlet, outdoor, room, etc.) |
| **Operating State** | Reports errors, not-running reason, active circuit, compressor status |
| **Setpoints** | Displays and allows adjusting heating/DHW setpoints |
| **Counters** | Compressor start count and runtime hours |
| **Cooling** | Detects if passive cooling is installed and active |
| **Hardware Detection** | Automatically detects:  |
| | – Passive cooling (reg 88) |
| | – Separate cooling circuit (reg 89) |
| | – Second heating circuit (reg 90) |
| | – Boiler / DHW circuit installed (reg 87) |
| | – Outdoor temperature sensor presence |
| **Device Identification** | Reads serial number and model type from registers 170–177 |
| **Write Support** | Allows writing selected Modbus registers (e.g. DHW enable, setpoints) |

---

## ⚙️ Supported Devices

All **Spirála heat pumps** using the 2019+ Modbus interface (`Modbus protokol Spirála 7-2019.pdf`):

- WW-F series (F…)
- WW-H series (H…)
- WW-R series (R…)
  
Connection may be either **Modbus TCP** (via RS-485 → TCP bridge) or **Modbus RTU** if supported by your setup.

---

## 🧰 Installation

### HACS (recommended)

1. Go to **HACS → Integrations → Custom repositories**.
2. Add the repository URL of this component.
3. Search for **Spirála Heat Pump** and install.
4. Restart Home Assistant.

### Manual

1. Copy the folder `custom_components/spirala_heat_pump` into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

---

## 🔌 Configuration

The integration is configured through the **UI (Integrations → Add Integration → Spirála Heat Pump)**.

### Required fields
| Field | Description |
|--------|-------------|
| **Host** | IP address or hostname of your Modbus-TCP converter |
| **Port** | TCP port (default `502`) |
| **Unit ID** | Modbus device ID (default `60`) |
| **Scan interval** | Optional polling interval in seconds (default 30s) |

### Auto-detected from device
No manual topology setup is needed — the component automatically reads:
- serial number (`db170–177`)
- model series (F/H/R)
- passive cooling / second circuit / DHW boiler / sensors presence

---

## 🏠 Entities

| Domain | Example entity | Description |
|---------|----------------|--------------|
| `climate` | `climate.spirala_heating` | Main heating circuit control |
| `sensor` | `sensor.spirala_outdoor_temp` | Outdoor temperature |
| `sensor` | `sensor.spirala_error_code` | Current error code (with translation) |
| `sensor` | `sensor.spirala_not_running_reason` | Reason why compressor is not running |
| `binary_sensor` | `binary_sensor.spirala_passive_cooling_installed` | Hardware feature flags |
| `switch` / `button` | `button.spirala_enable_dhw` | Optional DHW enable/disable |

All entity names follow the Home Assistant naming and translation system.

---

## 🧠 Device Information

The integration uses data read directly from the heat pump:

| Attribute | Source | Example |
|------------|--------|----------|
| **Model** | decoded from serial (H-series → `WW-H`) | `WW-H` |
| **Serial number** | registers 170–177 | `H1gm30350:151120` |
| **Firmware version** | if exposed | `1.23` |
| **Hardware configuration** | derived from regs 87–90 | `Passive cooling, 1 circuit` |

You can view these in the **Device Info** panel in Home Assistant.

---

## 🧪 Developer Notes

### Modbus implementation
- Uses `pymodbus.AsyncModbusTcpClient`
- Registers read in efficient batches defined by `REG_BATCHES`
- Uses `device_id` parameter to address the correct slave

### Register Map Highlights
| Purpose | Address | Notes |
|----------|----------|-------|
| Temperature tank 1 | 0 | external sensor |
| Outdoor temp | 3 | sentinel `-51/-52/-53` = invalid/missing |
| Error code | 27 | enum decoded to readable text |
| Not running reason | 28 | enum decoded to readable text |
| DHW enable | 40 | writable |
| DHW installed | 87 | read-only |
| Passive cooling installed | 88 | read-only |
| Separate cooling circuit | 89 | read-only |
| Second circuit installed | 90 | read-only |
| Serial number | 170–177 | ASCII, 16 chars |

---

## 🔧 Services (optional)

| Service | Description |
|----------|-------------|
| `spirala_heat_pump.set_dhw_allowed` | Write register 40 (enable/disable DHW) |
| `spirala_heat_pump.request_refresh` | Force immediate data poll |

---

Enable debug logging for detailed Modbus traces:
```yaml
logger:
  default: info
  logs:
    custom_components.spirala_heat_pump: debug
    pymodbus: warning
