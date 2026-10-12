"""
Tests for AI Advisor Engine.
Verifies bottleneck detection, physics disclaimers, and interactive queries.
"""

import unittest
from emergencycharge.ai.rule_engine import AIAdvisorEngine
from emergencycharge.core.laptop_telemetry import LaptopBatteryInfo
from emergencycharge.core.phone_detector import PhoneConnectionInfo
from emergencycharge.core.power_estimator import ChargingEstimate


class TestAIAdvisor(unittest.TestCase):
    def setUp(self):
        self.engine = AIAdvisorEngine()

    def test_bottleneck_detection_usb2(self):
        laptop_info = LaptopBatteryInfo(
            percent=70.0, is_plugged=False, power_source="Battery",
            secs_left=5000, discharge_rate_w=16.0, voltage_v=15.5,
            remaining_mwh=40000, full_capacity_mwh=50000, health_percent=90,
            status_text="Discharging"
        )
        phone_info = PhoneConnectionInfo(
            is_connected=True, connection_mode="ADB Debugging",
            device_name="Test Phone", battery_percent=40.0,
            battery_status="Charging", battery_voltage_v=4.0,
            charging_current_ma=480.0, charging_power_w=1.92,
            battery_temp_c=31.0
        )
        estimate = ChargingEstimate(
            is_measurable=True, phone_power_w=1.92, laptop_discharge_w=16.0,
            transfer_efficiency_pct=12.0, time_to_80_mins=180, time_to_100_mins=240,
            charge_rate_pct_per_hour=10.0, estimation_notes=""
        )

        report = self.engine.analyze(laptop_info, phone_info, estimate)
        self.assertTrue(any("USB 2.0" in b for b in report.bottlenecks))
        self.assertTrue(any(a.category == "Port Selection" for a in report.actions))
        self.assertIn("PHYSICALLY ENFORCED", report.physics_disclosure.upper())

    def test_qna_hardware_override_refusal(self):
        report = self.engine.analyze(
            LaptopBatteryInfo(100, True, "AC", None, 0, 16, 50000, 50000, 100, "AC"),
            PhoneConnectionInfo(True, "ADB", "Phone"),
            ChargingEstimate(True, 4.5, 0, 0, 60, 90, 20, "")
        )
        answer = self.engine.answer_query("Can software override USB hardware power limits to charge faster?", report)
        self.assertIn("No", answer)
        self.assertIn("polyfuses", answer.lower())


if __name__ == "__main__":
    unittest.main()
