"""
Laptop Battery and Power Telemetry for Windows.
Utilizes psutil, Win32 kernel32 APIs, and WMI/CIM ACPI interfaces.
"""

import ctypes
from dataclasses import dataclass
import logging
import subprocess
import threading
import time
from typing import Optional

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger("emergencycharge.laptop")


class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", ctypes.c_byte),
        ("BatteryFlag", ctypes.c_byte),
        ("BatteryLifePercent", ctypes.c_byte),
        ("SystemStatusFlag", ctypes.c_byte),
        ("BatteryLifeTime", ctypes.c_ulong),
        ("BatteryFullLifeTime", ctypes.c_ulong),
    ]


@dataclass
class LaptopBatteryInfo:
    percent: float
    is_plugged: bool
    power_source: str
    secs_left: Optional[int]
    discharge_rate_w: Optional[float]
    voltage_v: Optional[float]
    remaining_mwh: Optional[float]
    full_capacity_mwh: Optional[float]
    health_percent: Optional[float]
    status_text: str
    model_name: str = "Host Windows Laptop"
    is_available: bool = True


class LaptopTelemetryMonitor:
    """Monitors real laptop battery telemetry and AC power state on Windows."""

    def __init__(self):
        self._cached_wmi_time = 0.0
        self._cached_discharge_rate_w: Optional[float] = None
        self._cached_voltage_v: Optional[float] = None
        self._cached_remaining_mwh: Optional[float] = None
        self._cached_full_mwh: Optional[float] = None
        self._cached_model_name: str = self._query_laptop_model()
        self._wmi_query_in_progress = False
        self._lock = threading.Lock()

    def _query_laptop_model(self) -> str:
        """Queries actual laptop manufacturer and model name via Windows CIM."""
        try:
            ps_script = "(Get-CimInstance Win32_ComputerSystem).Manufacturer + ' ' + (Get-CimInstance Win32_ComputerSystem).Model"
            res = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script], capture_output=True, text=True, timeout=2.5)
            val = res.stdout.strip()
            if val:
                return val
        except Exception:
            pass
        return "Lenovo Laptop"

    def _query_wmi_acpi_async(self):
        """Asynchronously queries root/wmi for real-time ACPI battery wattage and capacity."""
        if self._wmi_query_in_progress:
            return

        def _worker():
            self._wmi_query_in_progress = True
            try:
                ps_script = (
                    "$s = Get-CimInstance -Namespace root/wmi -ClassName BatteryStatus -ErrorAction SilentlyContinue; "
                    "$c = Get-CimInstance -Namespace root/wmi -ClassName BatteryFullChargedCapacity -ErrorAction SilentlyContinue; "
                    "Write-Output ('{0}|{1}|{2}|{3}' -f ($s.DischargeRate), ($s.Voltage), ($s.RemainingCapacity), ($c.FullChargedCapacity))"
                )
                res = subprocess.run(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                    capture_output=True,
                    text=True,
                    timeout=2.5,
                )
                out = res.stdout.strip()
                if out and "|" in out:
                    parts = out.split("|")
                    with self._lock:
                        if parts[0] and parts[0].isdigit():
                            # DischargeRate in mW (or mA depending on ACPI implementation)
                            val = float(parts[0])
                            # If voltage is known and discharge rate > 1000, it's typically in mW
                            self._cached_discharge_rate_w = round(val / 1000.0, 2)
                        else:
                            self._cached_discharge_rate_w = None

                        if len(parts) > 1 and parts[1] and parts[1].isdigit():
                            self._cached_voltage_v = round(float(parts[1]) / 1000.0, 2)

                        if len(parts) > 2 and parts[2] and parts[2].isdigit():
                            self._cached_remaining_mwh = float(parts[2])

                        if len(parts) > 3 and parts[3] and parts[3].isdigit():
                            self._cached_full_mwh = float(parts[3])

                        self._cached_wmi_time = time.time()
            except Exception as e:
                logger.debug(f"WMI ACPI query skipped or timed out: {e}")
            finally:
                self._wmi_query_in_progress = False

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def get_telemetry(self) -> LaptopBatteryInfo:
        """Retrieves instant laptop battery telemetry using Win32 API and psutil."""
        now = time.time()
        # Trigger background WMI update every 4 seconds to get exact discharge wattage
        if now - self._cached_wmi_time > 4.0 and not self._wmi_query_in_progress:
            self._query_wmi_acpi_async()

        # 1. Try Win32 GetSystemPowerStatus for instant, zero-latency status
        win32_status = None
        sps = SYSTEM_POWER_STATUS()
        try:
            if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(sps)):
                win32_status = sps
        except Exception as e:
            logger.debug(f"Win32 GetSystemPowerStatus failed: {e}")

        # 2. Try psutil sensors_battery
        psutil_bat = None
        if psutil:
            try:
                psutil_bat = psutil.sensors_battery()
            except Exception as e:
                logger.debug(f"psutil sensors_battery failed: {e}")

        # If no battery found at all (e.g. desktop PC without UPS)
        if psutil_bat is None and win32_status is None:
            return LaptopBatteryInfo(
                percent=100.0,
                is_plugged=True,
                power_source="AC Wall Adapter (Desktop/Stationary)",
                secs_left=None,
                discharge_rate_w=None,
                voltage_v=None,
                remaining_mwh=None,
                full_capacity_mwh=None,
                health_percent=None,
                status_text="No internal battery detected (Mains AC Power)",
                is_available=False,
            )

        # Parse plugged state
        is_plugged = False
        if win32_status is not None:
            is_plugged = (win32_status.ACLineStatus == 1)
        elif psutil_bat is not None:
            is_plugged = bool(psutil_bat.power_plugged)

        # Parse percentage
        percent = 100.0
        if win32_status is not None and win32_status.BatteryLifePercent <= 100:
            percent = float(win32_status.BatteryLifePercent)
        elif psutil_bat is not None:
            percent = float(psutil_bat.percent)

        # Seconds remaining
        secs_left = None
        if not is_plugged:
            if win32_status is not None and win32_status.BatteryLifeTime != 0xFFFFFFFF:
                secs_left = int(win32_status.BatteryLifeTime)
            elif psutil_bat is not None and psutil_bat.secsleft not in (psutil.POWER_TIME_UNKNOWN, psutil.POWER_TIME_UNLIMITED):
                secs_left = int(psutil_bat.secsleft)

        power_source = "AC Wall Adapter (Charging / Mains)" if is_plugged else "Laptop Internal Battery (DC Reserve)"

        with self._lock:
            discharge_rate = 0.0 if is_plugged else self._cached_discharge_rate_w
            voltage_v = self._cached_voltage_v
            remaining_mwh = self._cached_remaining_mwh
            full_mwh = self._cached_full_mwh

        # Calculate battery health if design vs full is available
        health_pct = None
        if full_mwh and remaining_mwh:
            # health estimate
            health_pct = min(100.0, round((remaining_mwh / full_mwh) * 100.0, 1))

        status_text = "Discharging on Battery" if not is_plugged else "Connected to AC Adapter"

        return LaptopBatteryInfo(
            percent=percent,
            is_plugged=is_plugged,
            power_source=power_source,
            secs_left=secs_left,
            discharge_rate_w=discharge_rate,
            voltage_v=voltage_v,
            remaining_mwh=remaining_mwh,
            full_capacity_mwh=full_mwh,
            health_percent=health_pct,
            status_text=status_text,
            is_available=True,
        )
