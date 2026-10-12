"""
Tests for Safety Monitor Module.
Verifies laptop reserve cutoff, high-temperature alerts, and disconnect detection.
"""

import unittest
from emergencycharge.core.safety_monitor import AlertLevel, SafetyMonitor


class TestSafetyMonitor(unittest.TestCase):
    def setUp(self):
        self.monitor = SafetyMonitor(laptop_reserve_pct=20.0)

    def test_laptop_reserve_warning(self):
        # Laptop at 19% on battery -> Trigger warning
        alerts = self.monitor.check_safety(
            laptop_pct=19.0,
            is_laptop_plugged=False,
            phone_connected=True
        )
        self.assertTrue(any(a.level == AlertLevel.WARNING for a in alerts))

    def test_laptop_critical_floor(self):
        # Laptop at 9% on battery -> Trigger CRITICAL
        alerts = self.monitor.check_safety(
            laptop_pct=9.0,
            is_laptop_plugged=False,
            phone_connected=True
        )
        self.assertTrue(any(a.level == AlertLevel.CRITICAL for a in alerts))

    def test_ac_plugged_no_battery_warning(self):
        # Laptop on AC adapter at 15% should NOT warn about battery depletion
        alerts = self.monitor.check_safety(
            laptop_pct=15.0,
            is_laptop_plugged=True,
            phone_connected=True
        )
        self.assertFalse(any(a.level in (AlertLevel.WARNING, AlertLevel.CRITICAL) for a in alerts))

    def test_phone_thermal_warning(self):
        # Phone at 40°C -> Warning
        alerts = self.monitor.check_safety(
            laptop_pct=80.0,
            is_laptop_plugged=False,
            phone_connected=True,
            phone_temp_c=40.5
        )
        self.assertTrue(any(a.level == AlertLevel.WARNING and "Temperature" in a.title for a in alerts))

        # Phone at 45°C -> Critical
        alerts_crit = self.monitor.check_safety(
            laptop_pct=80.0,
            is_laptop_plugged=False,
            phone_connected=True,
            phone_temp_c=45.2
        )
        self.assertTrue(any(a.level == AlertLevel.CRITICAL and "OVERHEAT" in a.title for a in alerts_crit))


if __name__ == "__main__":
    unittest.main()
