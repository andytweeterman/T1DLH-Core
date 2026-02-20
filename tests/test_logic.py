import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add the parent directory to sys.path to import logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logic

class TestLogic(unittest.TestCase):
    def test_calc_ppo_with_series(self):
        # Create a sample series with enough data points for PPO
        # PPO uses EMA 12 and 26, so we need at least 26 points to get non-NaN results?
        # Actually EMA uses adjust=False, so it starts calculating from the beginning with the first value.

        # Generate some dummy price data
        dates = pd.date_range(start='2023-01-01', periods=50)
        prices = pd.Series(np.linspace(100, 150, 50), index=dates)

        ppo, sig, hist = logic.calc_ppo(prices)

        # Check types
        self.assertIsInstance(ppo, pd.Series)
        self.assertIsInstance(sig, pd.Series)
        self.assertIsInstance(hist, pd.Series)

        # Check lengths
        self.assertEqual(len(ppo), 50)
        self.assertEqual(len(sig), 50)
        self.assertEqual(len(hist), 50)

        # Check values are not all NaN (adjust=False means no initial NaNs usually, except maybe first few)
        # Actually pandas ewm with adjust=False starts immediately.
        self.assertFalse(ppo.isnull().all())
        self.assertFalse(sig.isnull().all())
        self.assertFalse(hist.isnull().all())

    def test_calc_ppo_with_dataframe(self):
        # Test the logic that handles DataFrame input
        dates = pd.date_range(start='2023-01-01', periods=50)
        df = pd.DataFrame({'Close': np.linspace(100, 150, 50)}, index=dates)

        ppo, sig, hist = logic.calc_ppo(df)

        self.assertIsInstance(ppo, pd.Series)
        self.assertEqual(len(ppo), 50)

if __name__ == '__main__':
    unittest.main()
