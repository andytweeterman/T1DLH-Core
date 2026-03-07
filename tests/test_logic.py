import unittest
import sys
import os
import pandas as pd
import numpy as np

# Add parent directory to path to import logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic import calculate_schedule_load

class TestLogicCalculateScheduleLoad(unittest.TestCase):
    def test_calculate_schedule_load_high(self):
        # meeting_count >= 7
        for count in [7, 8, 10, 20]:
            multiplier, message = calculate_schedule_load(count)
            self.assertEqual(multiplier, 1.3)
            self.assertIn("🔴 HIGH LOAD: Schedule density is critical", message)

    def test_calculate_schedule_load_elevated(self):
        # 4 <= meeting_count < 7
        for count in [4, 5, 6]:
            multiplier, message = calculate_schedule_load(count)
            self.assertEqual(multiplier, 1.15)
            self.assertIn("🟡 ELEVATED LOAD: Moderate schedule density", message)

    def test_calculate_schedule_load_light(self):
        # meeting_count < 4
        for count in [0, 1, 2, 3]:
            multiplier, message = calculate_schedule_load(count)
            self.assertEqual(multiplier, 1.0)
            self.assertEqual(message, "🟢 LIGHT LOAD: Schedule is clear.")

    def test_calculate_schedule_load_negative(self):
        # Edge case: negative meetings (should fall under light load)
        for count in [-1, -5]:
            multiplier, message = calculate_schedule_load(count)
            self.assertEqual(multiplier, 1.0)
            self.assertEqual(message, "🟢 LIGHT LOAD: Schedule is clear.")

if __name__ == '__main__':
    unittest.main()
