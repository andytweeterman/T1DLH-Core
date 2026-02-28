import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

# Mock streamlit before importing logic to bypass cache decorators
class MockStreamlit:
    def cache_data(self, **kwargs):
        def decorator(func):
            return func
        return decorator
sys.modules['streamlit'] = MockStreamlit()

import logic

class TestLogic(unittest.TestCase):
    def test_fetch_health_data(self):
        """Test that fetch_health_data generates correct DataFrame structure and values."""
        df = logic.fetch_health_data()

        # Check structure
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 288)
        self.assertListEqual(list(df.columns), ['Timestamp', 'Glucose_Value', 'Trend'])

        # Check data types
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df['Timestamp']))
        self.assertTrue(pd.api.types.is_integer_dtype(df['Glucose_Value']))
        self.assertTrue(pd.api.types.is_object_dtype(df['Trend']))

        # Check value ranges
        self.assertTrue((df['Glucose_Value'] >= 65).all())
        self.assertTrue((df['Glucose_Value'] <= 220).all())

        valid_trends = {'Flat', 'SingleUp', 'SingleDown'}
        self.assertTrue(set(df['Trend'].unique()).issubset(valid_trends))

        # Check timestamp intervals
        time_diffs = df['Timestamp'].diff().dropna()
        self.assertTrue((time_diffs == pd.Timedelta(minutes=5)).all())

        # Check if latest value is close to current time
        latest_time = df['Timestamp'].iloc[-1]
        self.assertTrue((datetime.now() - latest_time).total_seconds() < 60) # Allow some execution delay margin

if __name__ == '__main__':
    unittest.main()
