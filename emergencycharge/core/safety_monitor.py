"""
Safety Monitoring and Guardrails Module.
Enforces laptop battery preservation, thermal threshold checks,
and disconnection detection.
"""

from dataclasses import dataclass
from enum import Enum
import logging
from typing import List, Optional

from emergencycharge.config import (
    CRITICAL_LAPTOP_PERCENT,
    DEFAULT_LAPTOP_RESERVE_PERCENT,
    PHONE_CRITICAL_TEMP_C,
    PHONE_WARNING_TEMP_C,
)

logger = logging.getLogger("emergencycharge.safety")


class AlertLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class SafetyAlert:
    level: AlertLevel
    title: str
    message: str
    action_required: str
    timestamp: float


class SafetyMonitor:
    """Monitors battery, thermal, and connection telemetry to prevent damage or total depletion."""

    def __init__(self, laptop_reserve_pct: float = DEFAULT_LAPTOP_RESERVE_PERCENT):
        self.laptop_reserve_pct = laptop_reserve_pct
        self._was_previously_connected = False
        self._alerts_history: List[SafetyAlert] = []

    def check_safety(
        self,
        laptop_pct: float,
        is_laptop_plugged: bool,
        phone_connected: bool,
        phone_temp_c: Optional[float] = None,
        phone_pct: Optional[float] = None,
    ) -> List[SafetyAlert]:
        """Evaluates all safety constraints and returns any triggered alerts."""
        alerts: List[SafetyAlert] = []
        import time
        now = time.time()

        # 1. Laptop battery reserve check (only applies if laptop is running on battery)
        if not is_laptop_plugged:
            if laptop_pct <= CRITICAL_LAPTOP_PERCENT:
                alerts.append(SafetyAlert(
                    level=AlertLevel.CRITICAL,
                    title="CRITICAL LAPTOP BATTERY",
                    message=f"Laptop battery has dropped to {laptop_pct:.0f}% (below critical {CRITICAL_LAPTOP_PERCENT}% floor)!",
                    action_required="DISCONNECT PHONE NOW. Save your laptop from sudden shutdown.",
                    timestamp=now
                ))
            elif laptop_pct <= self.laptop_reserve_pct:
                alerts.append(SafetyAlert(
                    level=AlertLevel.WARNING,
                    title="Laptop Battery Reserve Reached",
                    message=f"Laptop battery is at {laptop_pct:.0f}%, reaching your configured reserve cutoff ({self.laptop_reserve_pct:.0f}%).",
                    action_required="Consider stopping emergency charging to preserve laptop power for essential tasks.",
                    timestamp=now
                ))

        # 2. Phone thermal monitoring (when authentic temperature telemetry is accessible)
        if phone_connected and phone_temp_c is not None:
            if phone_temp_c >= PHONE_CRITICAL_TEMP_C:
                alerts.append(SafetyAlert(
                    level=AlertLevel.CRITICAL,
                    title="CRITICAL PHONE OVERHEAT",
                    message=f"Phone battery temperature is {phone_temp_c:.1f}°C (exceeds {PHONE_CRITICAL_TEMP_C}°C safe ceiling)!",
                    action_required="Unplug phone immediately. Remove phone case and allow device to cool.",
                    timestamp=now
                ))
            elif phone_temp_c >= PHONE_WARNING_TEMP_C:
                alerts.append(SafetyAlert(
                    level=AlertLevel.WARNING,
                    title="Phone Elevated Temperature",
                    message=f"Phone battery temperature is {phone_temp_c:.1f}°C (approaching thermal threshold).",
                    action_required="Keep phone on a hard flat surface. Do not use phone screen while charging.",
                    timestamp=now
                ))

        # 3. Disconnection detection
        if self._was_previously_connected and not phone_connected:
            alerts.append(SafetyAlert(
                level=AlertLevel.INFO,
                title="Phone Disconnected",
                message="Smartphone cable was detached from the laptop.",
                action_required="Emergency charge session paused. Reconnect cable to resume.",
                timestamp=now
            ))

        self._was_previously_connected = phone_connected
        return alerts
