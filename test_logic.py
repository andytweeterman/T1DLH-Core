import pytest
from unittest.mock import patch, MagicMock
import logic
import pandas as pd

def test_fetch_market_data_masks_exception():
    with patch('logic.yf.download') as mock_download:
        mock_download.side_effect = Exception("Simulated network error")

        # New behavior: exception propagates
        with pytest.raises(Exception) as excinfo:
            logic.fetch_market_data()

        assert "Simulated network error" in str(excinfo.value)

def test_fetch_market_data_returns_none_on_empty():
    with patch('logic.yf.download') as mock_download:
        mock_download.return_value = pd.DataFrame() # Empty

        result = logic.fetch_market_data()
        assert result is None
