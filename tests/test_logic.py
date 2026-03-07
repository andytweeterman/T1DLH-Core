import unittest
import sys
import os
import pandas as pd
import numpy as np

# Add parent directory to path to import logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch
from logic import calculate_schedule_load, calc_glycemic_risk, fetch_health_data

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

    @patch('logic.is_weekend_window')
    @patch('logic.get_whoop_risk_modifier')
    def test_calc_glycemic_risk_schedule_load_elevated(self, mock_whoop, mock_weekend):
        # Ensure it's not a weekend so schedule load logic applies
        mock_weekend.return_value = False
        # Ensure whoop modifier doesn't trigger caution
        mock_whoop.return_value = (1.0, "🟢 FULLY CHARGED")

        # Mock df with nominal values to pass safety thresholds
        # Using "Normal" context
        df = pd.DataFrame({
            'Glucose_Value': [100.0, 100.0, 110.0],
            'Trend': ['Steady', 'Steady', 'Steady']
        })

        # Set meeting_count to 4 to trigger ELEVATED LOAD (1.15) which is <= 1.2
        # Therefore, LOAD ALERT should not be triggered in calc_glycemic_risk
        with patch('logic.apply_context_modifiers', return_value=df):
            processed_df, status, color, message = calc_glycemic_risk(
                df, context="Normal", meeting_count=4
            )

        self.assertNotEqual(status, "🟡 LOAD ALERT")
        self.assertIn("System nominal", message)

    @patch('logic.is_weekend_window')
    @patch('logic.get_whoop_risk_modifier')
    def test_calc_glycemic_risk_schedule_load_high_triggers_alert(self, mock_whoop, mock_weekend):
        # mock weekend to False and whoop modifier to 1.0
        mock_weekend.return_value = False
        mock_whoop.return_value = (1.0, "🟢 FULLY CHARGED")

        # Nominal glucose and steady trend to avoid other alerts
        df = pd.DataFrame({
            'Timestamp': [pd.Timestamp('2023-01-01 10:00:00'), pd.Timestamp('2023-01-01 10:05:00')],
            'Glucose_Value': [120.0, 120.0],
            'Trend': ['Steady', 'Steady']
        })

        # Test with HIGH LOAD (meeting_count = 7)
        # sched_modifier = 1.3 (> 1.2)
        with patch('logic.apply_context_modifiers', return_value=df):
            processed_df, status, color, message = calc_glycemic_risk(
                df, context="Normal", meeting_count=7
            )

        self.assertEqual(status, "🟡 LOAD ALERT")
        self.assertEqual(color, "#EED49F")
        self.assertIn("🔴 HIGH LOAD", message)

    @patch('logic.is_weekend_window')
    @patch('logic.get_whoop_risk_modifier')
    def test_calc_glycemic_risk_schedule_load_high_weekend_suppressed(self, mock_whoop, mock_weekend):
        # mock weekend to True so schedule load alert is suppressed
        mock_weekend.return_value = True
        mock_whoop.return_value = (1.0, "🟢 FULLY CHARGED")

        df = pd.DataFrame({
            'Timestamp': [pd.Timestamp('2023-01-01 10:00:00'), pd.Timestamp('2023-01-01 10:05:00')],
            'Glucose_Value': [120.0, 120.0],
            'Trend': ['Steady', 'Steady']
        })

        with patch('logic.apply_context_modifiers', return_value=df):
            processed_df, status, color, message = calc_glycemic_risk(
                df, context="Normal", meeting_count=7
            )

        # Alert should not be triggered because weekend is active
        self.assertNotEqual(status, "🟡 LOAD ALERT")
        self.assertIn("🌴 WEEKEND MODE ACTIVE", message)


if __name__ == '__main__':
    unittest.main()
