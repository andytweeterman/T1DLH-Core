import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from unittest.mock import MagicMock

# Mock streamlit to bypass caching decorators before importing logic
sys.modules['streamlit'] = MagicMock()

import logic

class TestContextModifiers(unittest.TestCase):
    def setUp(self):
        # Create a deterministic base dataframe for testing
        np.random.seed(42) # Ensure reproducibility

        # 288 points = 24 hours at 5 min intervals
        self.num_points = 288
        base_time = datetime(2023, 1, 1, 0, 0)
        self.timestamps = [base_time + timedelta(minutes=5*i) for i in range(self.num_points)]

        # Start with a constant baseline of 100 to easily see effects
        self.base_df = pd.DataFrame({
            'Timestamp': self.timestamps,
            'Glucose_Value': np.full(self.num_points, 100.0),
            'Trend': ['Steady'] * self.num_points
        })

    def test_apply_context_modifiers_normal(self):
        # Reset seed for predictable noise
        np.random.seed(42)
        df = self.base_df.copy()

        # apply_context_modifiers normal
        result_df = logic.apply_context_modifiers(df, "Normal")

        # Baseline is 100, noise is normal(0, 3)
        # Expected max value should be around 100 + 3*3 = 109, min around 91
        # The values should not have drifted far from 100
        mean_val = result_df['Glucose_Value'].mean()
        self.assertAlmostEqual(mean_val, 100.0, delta=1.0) # Mean shouldn't shift significantly

        # Verify length stays the same
        self.assertEqual(len(result_df), self.num_points)

    def test_apply_context_modifiers_stressed(self):
        np.random.seed(42)
        df = self.base_df.copy()

        # apply_context_modifiers stressed
        result_df = logic.apply_context_modifiers(df, "Stressed")

        # "Stressed" adds:
        # 1. drift = np.linspace(0, 40, len(df))
        # 2. stress_noise = np.random.normal(0, 8, len(df))
        # So it should end significantly higher than it started

        start_mean = result_df['Glucose_Value'].iloc[:10].mean()
        end_mean = result_df['Glucose_Value'].iloc[-10:].mean()

        # End should be ~40 higher than start due to linspace
        self.assertGreater(end_mean, start_mean + 30)
        self.assertLess(end_mean, start_mean + 50)

        # Total variance should be larger due to the N(0, 8) noise instead of N(0, 3)
        self.assertGreater(result_df['Glucose_Value'].std(), 8.0)

    def test_apply_context_modifiers_sick(self):
        np.random.seed(42)
        df = self.base_df.copy()

        # apply_context_modifiers sick
        result_df = logic.apply_context_modifiers(df, "Sick")

        # "Sick" adds:
        # 1. +50 baseline shift
        # 2. np.random.normal(0, 12, len(df))

        mean_val = result_df['Glucose_Value'].mean()
        # Should be around 150 (100 base + 50)
        self.assertAlmostEqual(mean_val, 150.0, delta=3.0)

        # Standard deviation should reflect the larger noise (12)
        self.assertGreater(result_df['Glucose_Value'].std(), 10.0)

    def test_apply_context_modifiers_exercise(self):
        np.random.seed(42)
        df = self.base_df.copy()

        # apply_context_modifiers exercise
        result_df = logic.apply_context_modifiers(df, "Exercise")

        # "Exercise" adds:
        # 1. crash = np.zeros(len(df))
        # 2. crash[-24:] = np.linspace(0, -60, 24)
        # 3. crash + normal(0, 3) noise

        # The beginning should be relatively stable
        start_mean = result_df['Glucose_Value'].iloc[:100].mean()
        self.assertAlmostEqual(start_mean, 100.0, delta=1.0)

        # The end should be significantly lower due to the crash
        # Base 100 - 60 = 40, but bounded to min 65 by np.clip later in function
        end_mean = result_df['Glucose_Value'].iloc[-5:].mean()

        # Make sure it's much lower than the start, hitting the clip floor
        self.assertLess(end_mean, start_mean - 20)
        self.assertAlmostEqual(end_mean, 65.0, delta=5.0) # Bounded by np.clip

    def test_apply_context_modifiers_project(self):
        np.random.seed(42)
        df = self.base_df.copy()

        # apply_context_modifiers project
        result_df = logic.apply_context_modifiers(df, "Project")

        # "Project" adds:
        # 1. drain = np.linspace(0, -40, len(df))
        # 2. drain + normal(0, 3) noise

        start_mean = result_df['Glucose_Value'].iloc[:10].mean()
        end_mean = result_df['Glucose_Value'].iloc[-10:].mean()

        # End should be ~40 lower than start due to linspace drain
        # Start ~ 100, End ~ 60 (clipped to 65)
        self.assertLess(end_mean, start_mean - 30)

    def test_apply_context_modifiers_travel(self):
        np.random.seed(42)
        df = self.base_df.copy()

        # apply_context_modifiers travel
        result_df = logic.apply_context_modifiers(df, "Travel")

        # "Travel" adds:
        # 3 random spikes generated using a gaussian envelope + noise

        # Verify spikes exist: max value should be noticeably higher than normal baseline+noise
        max_val = result_df['Glucose_Value'].max()

        # 100 base + 60 spike amplitude = 160 max (minus any noise/overlap offset)
        self.assertGreater(max_val, 140.0)

    def test_apply_context_modifiers_clip(self):
        np.random.seed(42)
        df = self.base_df.copy()

        # Set first half to 0, second half to 300
        # These are extreme values that should trigger the clipping logic
        half = self.num_points // 2
        df.loc[:half-1, 'Glucose_Value'] = 0.0
        df.loc[half:, 'Glucose_Value'] = 300.0

        result_df = logic.apply_context_modifiers(df, "Normal")

        # Validate that values are properly bounded
        # Note: normal noise could push extreme values slightly, but the clip
        # is the absolute last step. Thus max should be exactly 220, min exactly 65

        self.assertEqual(result_df['Glucose_Value'].min(), 65.0)
        self.assertEqual(result_df['Glucose_Value'].max(), 220.0)

    def test_apply_context_modifiers_trend(self):
        np.random.seed(42)
        df = self.base_df.copy()

        # Set up exact known increments that bypass noise
        # This will ensure the specific condition works

        # By providing huge gaps, even with random normal(0, 3) noise,
        # diff will be > 3 or < -3

        df.loc[0, 'Glucose_Value'] = 100
        df.loc[1, 'Glucose_Value'] = 110 # +10 -> Rising
        df.loc[2, 'Glucose_Value'] = 110 #  +0 -> Steady
        df.loc[3, 'Glucose_Value'] = 90  # -20 -> Falling

        # Need to ensure normal noise doesn't overwrite these huge diffs
        # Actually, let's just assert on the first 4 elements

        result_df = logic.apply_context_modifiers(df, "Normal")

        # result_df['Trend'] should be Rising for idx=1, Steady for idx=2, Falling for idx=3
        # We need to account for noise.
        # noise is normal(0, 3).
        # Diff between 100 -> 110 is +10. Even with worst case noise (+3 and -3), diff is +4.
        # Thus, idx 1 should always be Rising.
        # Diff between 110 -> 90 is -20. Always Falling.

        # It's better to verify the condition by examining the values directly:
        diffs = result_df['Glucose_Value'].diff().fillna(0)

        for i in range(1, 4):
            if diffs.iloc[i] > 3:
                self.assertEqual(result_df['Trend'].iloc[i], "Rising")
            elif diffs.iloc[i] < -3:
                self.assertEqual(result_df['Trend'].iloc[i], "Falling")
            else:
                self.assertEqual(result_df['Trend'].iloc[i], "Steady")

        # Check that it generated at least one of each expected type across the whole frame
        trends = result_df['Trend'].unique()
        self.assertIn("Rising", trends)
        self.assertIn("Falling", trends)

if __name__ == '__main__':
    unittest.main()
