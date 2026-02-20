import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path to allow importing logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock streamlit before importing logic
mock_st = MagicMock()
# Mock cache_data to be a pass-through decorator
def mock_cache_data(**kwargs):
    def decorator(func):
        return func
    return decorator
mock_st.cache_data = mock_cache_data
sys.modules["streamlit"] = mock_st

# Now import logic
import logic

class TestLogic(unittest.TestCase):

    @patch('yfinance.download')
    def test_fetch_market_data_exception(self, mock_yf_download):
        """Test that fetch_market_data returns None when yfinance raises an exception."""
        # Setup the mock to raise an exception
        mock_yf_download.side_effect = Exception("API Connection Error")

        # Call the function
        result = logic.fetch_market_data()

        # Assertions
        self.assertIsNone(result)
        mock_yf_download.assert_called_once()

    @patch('yfinance.download')
    def test_fetch_market_data_success(self, mock_yf_download):
        """Test that fetch_market_data returns data when yfinance succeeds."""
        # Create a dummy DataFrame
        dates = pd.date_range(start='2020-01-01', periods=5)
        data = pd.DataFrame(np.random.randn(5, 4), index=dates, columns=['Open', 'High', 'Low', 'Close'])
        mock_yf_download.return_value = data

        # Call the function
        result = logic.fetch_market_data()

        # Assertions
        pd.testing.assert_frame_equal(result, data)
        mock_yf_download.assert_called_once()

    @patch('yfinance.download')
    def test_fetch_market_data_none(self, mock_yf_download):
        """Test that fetch_market_data returns None when yfinance returns None."""
        mock_yf_download.return_value = None

        # Call the function
        result = logic.fetch_market_data()

        # Assertions
        self.assertIsNone(result)
        mock_yf_download.assert_called_once()

    @patch('yfinance.download')
    def test_fetch_market_data_empty(self, mock_yf_download):
        """Test that fetch_market_data returns None when yfinance returns empty DataFrame."""
        mock_yf_download.return_value = pd.DataFrame()

        # Call the function
        result = logic.fetch_market_data()

        # Assertions
        self.assertIsNone(result)
        mock_yf_download.assert_called_once()

if __name__ == '__main__':
    unittest.main()
