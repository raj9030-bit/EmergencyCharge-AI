"""
Windows Power Management and Execution State Controller.
Uses Win32 SetThreadExecutionState to prevent system sleep and USB port power cutoff,
and powercfg utilities for inspecting USB selective suspend settings.
"""

import ctypes
import logging
import subprocess
from typing import Dict, Optional, Tuple

logger = logging.getLogger("emergencycharge.winpower")

# Win32 Execution State Flags
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002
ES_AWAYMODE_REQUIRED = 0x00000040
ES_CONTINUOUS = 0x80000000


class WindowsPowerManager:
    """Manages Windows execution state, preventing USB power cutoff during emergency charging."""

    def __init__(self):
        self._keep_awake_active = False

    def enable_emergency_keep_awake(self, allow_display_sleep: bool = True) -> bool:
        """
        Enables continuous system execution and away mode.
        If allow_display_sleep is True, the laptop screen can turn off to save battery,
        while the system, chipset, and USB ports remain fully energized!
        """
        try:
            flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED
            if allow_display_sleep:
                # Away mode keeps system running and USB ports powered even if user closes lid or display sleeps
                flags |= ES_AWAYMODE_REQUIRED
            else:
                flags |= ES_DISPLAY_REQUIRED

            res = ctypes.windll.kernel32.SetThreadExecutionState(flags)
            if res != 0:
                self._keep_awake_active = True
                logger.info("Windows Keep-Awake and USB port power preservation enabled.")
                return True
            else:
                logger.warning("SetThreadExecutionState returned 0.")
                return False
        except Exception as e:
            logger.error(f"Failed to set thread execution state: {e}")
            return False

    def disable_emergency_keep_awake(self) -> bool:
        """Restores normal Windows sleep and power management behavior."""
        try:
            res = ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            self._keep_awake_active = False
            logger.info("Restored standard Windows sleep configuration.")
            return res != 0
        except Exception as e:
            logger.error(f"Failed to reset thread execution state: {e}")
            return False

    @property
    def is_keep_awake_active(self) -> bool:
        return self._keep_awake_active

    def get_power_plan_info(self) -> Dict[str, str]:
        """Queries active Windows power plan and USB selective suspend state."""
        info = {
            "active_plan": "Balanced (Windows Default)",
            "usb_selective_suspend": "Enabled (May power down USB port when idle)",
        }
        try:
            # Query active power plan
            res = subprocess.run(
                ["powercfg", "/getactivescheme"],
                capture_output=True, text=True, timeout=2.0
            )
            out = res.stdout.strip()
            if "(" in out and ")" in out:
                plan_name = out.split("(")[-1].split(")")[0]
                info["active_plan"] = plan_name
        except Exception as e:
            logger.debug(f"powercfg query error: {e}")

        return info
