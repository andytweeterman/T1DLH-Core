import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import os
import sys

# Capture original exists before mocking to prevent recursion
ORIGINAL_EXISTS = os.path.exists

# Add parent directory to path to import logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logic

class TestLoadStrategistData(unittest.TestCase):

    def setUp(self):
        # Clear cache before each test to ensure isolation
        if hasattr(logic.load_strategist_data, 'clear'):
            logic.load_strategist_data.clear()

    @patch('logic.os.path.exists')
    @patch('logic.pd.read_csv')
    def test_load_strategist_data_gspc_exists(self, mock_read_csv, mock_exists):
        # Setup
        # Use side_effect to only mock specific paths, fallback to real exists otherwise
        def exists_side_effect(path):
            if str(path).endswith('^GSPC.csv'):
                return True
            if str(path).endswith('strategist_forecast.csv'):
                return False
            return ORIGINAL_EXISTS(path)
        mock_exists.side_effect = exists_side_effect

        expected_df = pd.DataFrame({
            'Date': ['2023-01-01'],
            'Tstk_Adj': [1.0],
            'FP1': [1.0],
            'FP3': [1.0],
            'FP6': [1.0]
        })
        mock_read_csv.return_value = expected_df

        # Execute
        result = logic.load_strategist_data()

        # Verify
        self.assertIsNotNone(result)
        self.assertIn('Date', result.columns)
        pd.testing.assert_frame_equal(result, expected_df)
        mock_read_csv.assert_called()

    @patch('logic.os.path.exists')
    @patch('logic.pd.read_csv')
    def test_load_strategist_data_fallback_exists(self, mock_read_csv, mock_exists):
        # Setup: ^GSPC.csv does not exist, but strategist_forecast.csv does
        def exists_side_effect(path):
            if str(path).endswith('^GSPC.csv'):
                return False
            if str(path).endswith('strategist_forecast.csv'):
                return True
            return ORIGINAL_EXISTS(path)
        mock_exists.side_effect = exists_side_effect

        expected_df = pd.DataFrame({
            'Date': ['2023-01-01'],
            'Tstk_Adj': [1.0],
            'FP1': [1.0],
            'FP3': [1.0],
            'FP6': [1.0]
        })
        mock_read_csv.return_value = expected_df

        # Execute
        result = logic.load_strategist_data()

        # Verify
        self.assertIsNotNone(result)
        pd.testing.assert_frame_equal(result, expected_df)

    @patch('logic.os.path.exists')
    def test_load_strategist_data_no_files(self, mock_exists):
        # Setup: No files exist
        def exists_side_effect(path):
            if str(path).endswith('^GSPC.csv'):
                return False
            if str(path).endswith('strategist_forecast.csv'):
                return False
            return ORIGINAL_EXISTS(path)
        mock_exists.side_effect = exists_side_effect

        # Execute
        result = logic.load_strategist_data()

        # Verify
        self.assertIsNone(result)

    @patch('logic.os.path.exists')
    @patch('logic.pd.read_csv')
    def test_load_strategist_data_missing_columns(self, mock_read_csv, mock_exists):
        # Setup: File exists but missing columns
        def exists_side_effect(path):
            if str(path).endswith('^GSPC.csv'):
                return True
            return ORIGINAL_EXISTS(path)
        mock_exists.side_effect = exists_side_effect

        # Missing 'FP6'
        invalid_df = pd.DataFrame({
            'Date': ['2023-01-01'],
            'Tstk_Adj': [1.0],
            'FP1': [1.0],
            'FP3': [1.0]
        })
        mock_read_csv.return_value = invalid_df

        # Execute
        result = logic.load_strategist_data()

        # Verify
        self.assertIsNone(result)

    @patch('logic.os.path.exists')
    @patch('logic.pd.read_csv')
    def test_load_strategist_data_exception(self, mock_read_csv, mock_exists):
        # Setup: read_csv raises exception
        def exists_side_effect(path):
            if str(path).endswith('^GSPC.csv'):
                return True
            return ORIGINAL_EXISTS(path)
        mock_exists.side_effect = exists_side_effect

        mock_read_csv.side_effect = Exception("Read error")

        # Execute
        result = logic.load_strategist_data()

        # Verify
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
