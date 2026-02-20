import pytest
import pandas as pd
import numpy as np
import logic

def clear_cache():
    """Helper to clear Streamlit cache if present."""
    if hasattr(logic.fetch_market_data, 'clear'):
        logic.fetch_market_data.clear()

def test_fetch_market_data_success(mocker):
    """Test successful data fetch and cleaning."""
    # Create sample DataFrame with some NaNs to test ffill
    dates = pd.date_range(start='2023-01-01', periods=5)

    # Create MultiIndex for columns: Level 0 = Price, Level 1 = Ticker
    iterables = [['Close'], ['SPY', '^DJI']]
    columns = pd.MultiIndex.from_product(iterables, names=['Price', 'Ticker'])

    # Data with NaNs
    data_values = np.array([
        [400.0, 33000.0],
        [np.nan, 33100.0], # SPY missing at index 1
        [402.0, np.nan],   # DJI missing at index 2
        [403.0, 33300.0],
        [404.0, 33400.0]
    ])

    df = pd.DataFrame(data_values, index=dates, columns=columns)

    # Mock yfinance.download
    mock_download = mocker.patch('yfinance.download', return_value=df)

    # Clear cache before call
    clear_cache()

    result = logic.fetch_market_data()

    assert result is not None

    # Verify ffill
    # Access 'Close' level
    closes = result['Close']

    # SPY at index 1 should be filled from index 0
    assert closes['SPY'].iloc[1] == 400.0

    # DJI at index 2 should be filled from index 1 (33100.0)
    assert closes['^DJI'].iloc[2] == 33100.0

    mock_download.assert_called_once()

def test_fetch_market_data_empty(mocker):
    """Test handling of empty data."""
    # Case 1: yfinance returns None
    mocker.patch('yfinance.download', return_value=None)
    clear_cache()
    assert logic.fetch_market_data() is None

    # Case 2: yfinance returns empty DataFrame
    mocker.patch('yfinance.download', return_value=pd.DataFrame())
    clear_cache()
    assert logic.fetch_market_data() is None

def test_fetch_market_data_exception(mocker):
    """Test handling of exceptions during download."""
    mocker.patch('yfinance.download', side_effect=Exception("API Error"))
    clear_cache()
    assert logic.fetch_market_data() is None
