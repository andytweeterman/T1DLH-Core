import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from logic import calc_glycemic_risk

class TestGlycemicRisk(unittest.TestCase):

    def setUp(self):
        # Base DataFrame structure needed for the function
        self.base_df = pd.DataFrame({
            'Timestamp': [datetime.now()],
            'Glucose_Value': [120],
            'Trend': ['Flat']
        })

    def test_critical_risk_hypoglycemia(self):
        # bg < 70
        df = self.base_df.copy()
        df.loc[0, 'Glucose_Value'] = 65

        result_df, status, color, msg = calc_glycemic_risk(df)
        self.assertEqual(status, "DEFENSIVE MODE")
        self.assertEqual(color, "#ED8796")
        self.assertIn("Critical", msg)

    def test_critical_risk_rapid_drop(self):
        # bg < 90 and trend == 'SingleDown'
        df = self.base_df.copy()
        df.loc[0, 'Glucose_Value'] = 85
        df.loc[0, 'Trend'] = 'SingleDown'

        result_df, status, color, msg = calc_glycemic_risk(df)
        self.assertEqual(status, "DEFENSIVE MODE")
        self.assertEqual(color, "#ED8796")
        self.assertIn("Critical", msg)

    def test_critical_risk_driving(self):
        # bg < 100 and current_context == 'Driving'
        df = self.base_df.copy()
        df.loc[0, 'Glucose_Value'] = 95

        result_df, status, color, msg = calc_glycemic_risk(df, current_context='Driving')
        self.assertEqual(status, "DEFENSIVE MODE")
        self.assertEqual(color, "#ED8796")
        self.assertIn("Critical", msg)

    def test_contextual_resistance_hyperglycemia(self):
        # bg > 180
        df = self.base_df.copy()
        df.loc[0, 'Glucose_Value'] = 185

        result_df, status, color, msg = calc_glycemic_risk(df)
        self.assertEqual(status, "CAUTION")
        self.assertEqual(color, "#EED49F")
        self.assertIn("Elevated", msg)

    def test_contextual_resistance_stress_meeting(self):
        # bg > 140 and current_context == "High Stress Meeting"
        df = self.base_df.copy()
        df.loc[0, 'Glucose_Value'] = 150

        result_df, status, color, msg = calc_glycemic_risk(df, current_context="High Stress Meeting")
        self.assertEqual(status, "CAUTION")
        self.assertEqual(color, "#EED49F")
        self.assertIn("Elevated", msg)

    def test_contextual_resistance_strategy_review(self):
        # bg > 140 and current_context == "Capital One Strategy Review"
        df = self.base_df.copy()
        df.loc[0, 'Glucose_Value'] = 145

        result_df, status, color, msg = calc_glycemic_risk(df, current_context="Capital One Strategy Review")
        self.assertEqual(status, "CAUTION")
        self.assertEqual(color, "#EED49F")
        self.assertIn("Elevated", msg)

    def test_activity_watchlist(self):
        # bg < 100 and current_context == "Pinewood Derby prep with Lucas"
        df = self.base_df.copy()
        df.loc[0, 'Glucose_Value'] = 95

        result_df, status, color, msg = calc_glycemic_risk(df, current_context="Pinewood Derby prep with Lucas")
        self.assertEqual(status, "WATCHLIST")
        self.assertEqual(color, "#EED49F")
        self.assertIn("Activity Risk", msg)

    def test_nominal_comfort_zone(self):
        # Nominal case, e.g., bg = 120, trend = 'Flat'
        df = self.base_df.copy()

        result_df, status, color, msg = calc_glycemic_risk(df)
        self.assertEqual(status, "COMFORT ZONE")
        self.assertEqual(color, "#A6DA95")
        self.assertIn("Metabolic & Contextual Stability", msg)

    def test_exception_handling_empty_dataframe(self):
        # Empty dataframe will raise IndexError on iloc[-1]
        df = pd.DataFrame()

        result_df, status, color, msg = calc_glycemic_risk(df)
        self.assertEqual(status, "ERROR")
        self.assertEqual(color, "#ED8796")
        self.assertIn("Error:", msg)

    def test_exception_handling_missing_column(self):
        # Missing 'Glucose_Value' column will raise KeyError
        df = pd.DataFrame({
            'Timestamp': [datetime.now()],
            'Trend': ['Flat']
        })

        result_df, status, color, msg = calc_glycemic_risk(df)
        self.assertEqual(status, "ERROR")
        self.assertEqual(color, "#ED8796")
        self.assertIn("Error:", msg)

if __name__ == '__main__':
    unittest.main()
