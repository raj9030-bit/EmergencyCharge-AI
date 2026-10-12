"""
Configuration and Hardware Specifications for EmergencyCharge AI.
"""

from dataclasses import dataclass
from typing import Dict, Tuple

APP_TITLE = "EmergencyCharge AI"
VERSION = "1.0.0"

# Safety Defaults
DEFAULT_LAPTOP_RESERVE_PERCENT = 20  # Stop or alert when laptop battery hits this level
CRITICAL_LAPTOP_PERCENT = 10         # Critical cutoff alert
PHONE_WARNING_TEMP_C = 39.0          # Warning temperature for phone battery
PHONE_CRITICAL_TEMP_C = 44.0         # Critical thermal throttling / safety risk
POLL_INTERVAL_MS = 5000              # UI / telemetry refresh interval (exactly 5 seconds)

# Typical phone battery capacity in mAh (used when real battery capacity not readable via ADB)
DEFAULT_PHONE_CAPACITY_MAH = 4500
TYPICAL_BATTERY_NOMINAL_VOLTAGE = 3.85  # Lithium-ion / Li-Po nominal cell voltage

@dataclass(frozen=True)
class USBSpec:
    name: str
    voltage: float     # Volts
    current: float     # Amperes
    power_watts: float # Watts
    description: str

USB_SPECS: Dict[str, USBSpec] = {
    "USB_2_0": USBSpec(
        name="USB 2.0 Standard (SDP)",
        voltage=5.0,
        current=0.5,
        power_watts=2.5,
        description="Standard legacy USB port (black tongue). Limited by USB-IF spec to 500mA."
    ),
    "USB_3_0": USBSpec(
        name="USB 3.0 / 3.2 Gen 1 (SDP)",
        voltage=5.0,
        current=0.9,
        power_watts=4.5,
        description="SuperSpeed USB port (blue tongue). Standard specification limit is 900mA."
    ),
    "USB_BC_1_2": USBSpec(
        name="USB BC 1.2 / Always-On (CDP)",
        voltage=5.0,
        current=1.5,
        power_watts=7.5,
        description="Charging Downstream Port (often marked with battery icon or yellow tongue). Up to 1.5A."
    ),
    "TYPE_C_1_5A": USBSpec(
        name="USB Type-C Standard (1.5A)",
        voltage=5.0,
        current=1.5,
        power_watts=7.5,
        description="USB-C standard current advertisement on CC pin (Rp = 22kΩ). 5V @ 1.5A."
    ),
    "TYPE_C_3_0A": USBSpec(
        name="USB Type-C High Power (3.0A)",
        voltage=5.0,
        current=3.0,
        power_watts=15.0,
        description="USB-C high-power mode on CC pin (Rp = 10kΩ). 5V @ 3.0A without PD negotiation."
    ),
    "USB_PD_18W": USBSpec(
        name="USB Power Delivery (18W)",
        voltage=9.0,
        current=2.0,
        power_watts=18.0,
        description="Negotiated USB-PD contract via BMC packets on CC pin. 9V @ 2.0A."
    ),
    "USB_PD_27W": USBSpec(
        name="USB Power Delivery (27W)",
        voltage=9.0,
        current=3.0,
        power_watts=27.0,
        description="Fast negotiated USB-PD contract via Type-C PD controller. 9V @ 3.0A."
    ),
}

# Known Smartphone USB Vendor IDs (VID in hexadecimal)
SMARTPHONE_VENDORS: Dict[str, str] = {
    "18D1": "Google Pixel / Nexus",
    "04E8": "Samsung Electronics",
    "05AC": "Apple Inc. (iPhone / iPad)",
    "2717": "Xiaomi / Redmi / POCO",
    "22D9": "OPPO / OnePlus / Realme",
    "12D1": "Huawei Technologies",
    "22B8": "Motorola Mobility",
    "1004": "LG Electronics",
    "0FCE": "Sony Mobile",
    "2D95": "Vivo Mobile",
    "2A70": "OnePlus",
    "0BB4": "HTC Corporation",
    "0489": "Foxconn / FIH Mobile",
    "29A9": "Nothing Technology",
    "17EF": "Lenovo Mobile",
    "04B3": "Transsion (Tecno / Infinix / Itel)",
}
