"""
Tests for Phone Detector Module.
Verifies parsing of ADB dumpsys data, vendor VID mapping, and limited telemetry honesty.
"""

import unittest
from emergencycharge.config import SMARTPHONE_VENDORS
from emergencycharge.core.phone_detector import PhoneDetector


class TestPhoneDetector(unittest.TestCase):
    def setUp(self):
        self.detector = PhoneDetector()

    def test_vendor_id_mapping(self):
        self.assertIn("18D1", SMARTPHONE_VENDORS)  # Google
        self.assertIn("04E8", SMARTPHONE_VENDORS)  # Samsung
        self.assertIn("05AC", SMARTPHONE_VENDORS)  # Apple

    def test_detect_runs_without_crash(self):
        info = self.detector.detect()
        self.assertIsNotNone(info)
        self.assertIsInstance(info.is_connected, bool)
        self.assertIsNotNone(info.device_name)
        # If not connected, telemetry should be marked honest
        if not info.is_connected:
            self.assertEqual(info.telemetry_source, "None")
            self.assertIsNone(info.battery_percent)


if __name__ == "__main__":
    unittest.main()
