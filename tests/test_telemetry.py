"""
Tests for Laptop Telemetry Monitor and Power Estimation.
"""

import unittest
from emergencycharge.core.laptop_telemetry import LaptopTelemetryMonitor
from emergencycharge.core.power_estimator import PowerEstimator


class TestLaptopTelemetry(unittest.TestCase):
    def setUp(self):
        self.monitor = LaptopTelemetryMonitor()

    def test_telemetry_fields(self):
        info = self.monitor.get_telemetry()
        self.assertIsNotNone(info)
        self.assertIsInstance(info.percent, (int, float))
        self.assertGreaterEqual(info.percent, 0.0)
        self.assertLessEqual(info.percent, 100.0)
        self.assertIsInstance(info.is_plugged, bool)
        self.assertIn("Battery", info.power_source) if not info.is_plugged else self.assertIn("AC", info.power_source)


class TestPowerEstimator(unittest.TestCase):
    def setUp(self):
        self.estimator = PowerEstimator(phone_capacity_mah=4500)

    def test_charge_estimation_cc_cv(self):
        # 4.5W port, phone at 30%
        est = self.estimator.calculate_estimate(
            phone_percent=30.0,
            measured_power_w=4.5,
            port_spec_key="USB_3_0",
            laptop_discharge_w=15.0,
            phone_screen_on=False,
            is_simulated=True
        )
        self.assertTrue(est.is_measurable)
        self.assertIsNotNone(est.time_to_80_mins)
        self.assertIsNotNone(est.time_to_100_mins)
        # Time to 100% must be strictly greater than time to 80% due to CV taper
        self.assertGreater(est.time_to_100_mins, est.time_to_80_mins)
        # Efficiency: 4.5W / 15W = 30.0%
        self.assertAlmostEqual(est.transfer_efficiency_pct, 30.0, delta=1.0)

    def test_screen_on_drain_penalty(self):
        # Compare net rate with screen on vs screen off
        est_off = self.estimator.calculate_estimate(
            phone_percent=50.0,
            measured_power_w=4.5,
            phone_screen_on=False,
            is_simulated=True
        )
        est_on = self.estimator.calculate_estimate(
            phone_percent=50.0,
            measured_power_w=4.5,
            phone_screen_on=True,
            is_simulated=True
        )
        # Screen off must charge faster
        self.assertGreater(est_off.charge_rate_pct_per_hour, est_on.charge_rate_pct_per_hour)
        self.assertLess(est_off.time_to_100_mins, est_on.time_to_100_mins)


if __name__ == "__main__":
    unittest.main()
