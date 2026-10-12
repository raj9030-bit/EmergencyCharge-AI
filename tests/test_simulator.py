"""
Tests for Hardware Simulator Module.
Ensures all simulation scenarios produce valid, non-crashing telemetry objects.
"""

import unittest
from emergencycharge.core.simulator import HardwareSimulator, SCENARIOS


class TestSimulator(unittest.TestCase):
    def setUp(self):
        self.sim = HardwareSimulator()

    def test_all_scenarios_valid(self):
        for sc_id in SCENARIOS.keys():
            self.sim.set_scenario(sc_id)
            laptop_info = self.sim.get_laptop_telemetry()
            phone_info = self.sim.get_phone_info()

            self.assertTrue(0 <= laptop_info.percent <= 100)
            self.assertTrue(phone_info.is_connected)
            self.assertIn("Simulated", phone_info.device_name)
            self.assertIn("DEMO SIMULATOR", phone_info.telemetry_source)


if __name__ == "__main__":
    unittest.main()
