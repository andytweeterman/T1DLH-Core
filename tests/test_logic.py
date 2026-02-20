import pytest
import pandas as pd
import numpy as np
from logic import calc_governance

# Helper to create mock data
def mock_market_data(rows=30,
                     credit_spread=1.0,
                     vix=20.0,
                     breadth_ratio=1.0,
                     dxy=100.0):

    dates = pd.date_range(end=pd.Timestamp.now(), periods=rows, freq='D')

    # We need to construct data such that:
    # Credit_Ratio = HYG / IEF
    # Breadth_Ratio = RSP / SPY

    # Let's fix denominators to 100 for simplicity
    ief = 100.0
    spy = 100.0

    # HYG = credit_spread * IEF
    hyg = credit_spread * ief

    # RSP = breadth_ratio * SPY
    rsp = breadth_ratio * spy

    # Create dictionary of Series
    data_dict = {
        "HYG": [hyg] * rows,
        "IEF": [ief] * rows,
        "^VIX": [vix] * rows,
        "RSP": [rsp] * rows,
        "SPY": [spy] * rows,
        "DX-Y.NYB": [dxy] * rows
    }

    # Create DataFrame
    df_close = pd.DataFrame(data_dict, index=dates)

    # calc_governance expects data['Close'] to return this DataFrame
    return {'Close': df_close}

def test_calc_governance_system_boot():
    """Test with empty data returns SYSTEM BOOT."""
    # Must have columns so it doesn't trigger KeyError (DATA ERROR)
    columns = ["HYG", "IEF", "^VIX", "RSP", "SPY", "DX-Y.NYB"]
    empty_data = {'Close': pd.DataFrame(columns=columns)}
    df, status, color, desc = calc_governance(empty_data)
    assert status == "SYSTEM BOOT"
    assert color == "#888888"
    assert desc == "Initializing..."

def test_calc_governance_comfort_zone():
    """Test with stable data returns COMFORT ZONE."""
    data = mock_market_data()
    df, status, color, desc = calc_governance(data)
    assert status == "COMFORT ZONE"
    assert color == "#00d26a"

def test_calc_governance_caution_stress():
    """Test Credit/Currency Stress: Credit_Delta < -0.015."""
    # We need Credit_Ratio to drop by > 1.5% over 10 days
    # Initial Credit_Ratio = 1.0. Final needs to be < 0.985

    rows = 30
    dates = pd.date_range(end=pd.Timestamp.now(), periods=rows, freq='D')

    # Start high, end low
    # pct_change(10).
    hyg_values = np.ones(rows) * 100.0
    # Last 10 days drop significantly
    hyg_values[-1] = 98.0 # 2% drop from 10 days ago (which was 100)

    df_close = pd.DataFrame({
        "HYG": hyg_values,
        "IEF": [100.0] * rows,
        "^VIX": [20.0] * rows,
        "RSP": [100.0] * rows,
        "SPY": [100.0] * rows,
        "DX-Y.NYB": [100.0] * rows
    }, index=dates)

    data = {'Close': df_close}

    df, status, color, desc = calc_governance(data)

    assert status == "CAUTION"
    assert desc == "Credit/Currency Stress"

def test_calc_governance_caution_volatility():
    """Test Elevated Volatility: VIX > 25."""
    data = mock_market_data(vix=26.0)
    df, status, color, desc = calc_governance(data)
    assert status == "CAUTION"
    assert desc == "Elevated Volatility"

def test_calc_governance_watchlist_breadth():
    """Test Market Breadth Narrowing: Breadth_Delta < -0.025."""
    rows = 30
    dates = pd.date_range(end=pd.Timestamp.now(), periods=rows, freq='D')

    # Breadth Ratio = RSP/SPY. needs to drop > 2.5% over 20 days.
    rsp_values = np.ones(rows) * 100.0
    rsp_values[-1] = 97.0 # 3% drop

    df_close = pd.DataFrame({
        "HYG": [100.0] * rows,
        "IEF": [100.0] * rows,
        "^VIX": [20.0] * rows,
        "RSP": rsp_values,
        "SPY": [100.0] * rows,
        "DX-Y.NYB": [100.0] * rows
    }, index=dates)

    data = {'Close': df_close}
    df, status, color, desc = calc_governance(data)

    assert status == "WATCHLIST"
    assert desc == "Market Breadth Narrowing"

def test_calc_governance_defensive_confirmed():
    """Test Defensive Mode: Stress AND VIX > 25."""
    rows = 30
    dates = pd.date_range(end=pd.Timestamp.now(), periods=rows, freq='D')

    # Stress: HYG drop
    hyg_values = np.ones(rows) * 100.0
    hyg_values[-1] = 98.0 # Stress

    # VIX > 25
    vix_values = [26.0] * rows

    df_close = pd.DataFrame({
        "HYG": hyg_values,
        "IEF": [100.0] * rows,
        "^VIX": vix_values,
        "RSP": [100.0] * rows,
        "SPY": [100.0] * rows,
        "DX-Y.NYB": [100.0] * rows
    }, index=dates)

    data = {'Close': df_close}
    df, status, color, desc = calc_governance(data)

    assert status == "DEFENSIVE MODE"
    assert desc == "Structural Failure Confirmed"

def test_calc_governance_defensive_extreme():
    """Test Defensive Mode: VIX > 30."""
    data = mock_market_data(vix=31.0)
    df, status, color, desc = calc_governance(data)
    assert status == "DEFENSIVE MODE"
    assert desc == "Extreme Volatility"

def test_calc_governance_missing_vix():
    """Test robustness when ^VIX column is missing."""
    rows = 30
    dates = pd.date_range(end=pd.Timestamp.now(), periods=rows, freq='D')

    df_close = pd.DataFrame({
        "HYG": [100.0] * rows,
        "IEF": [100.0] * rows,
        # No VIX
        "RSP": [100.0] * rows,
        "SPY": [100.0] * rows,
        "DX-Y.NYB": [100.0] * rows
    }, index=dates)

    data = {'Close': df_close}

    # Should default VIX to 0.0 and return COMFORT ZONE if no other stress
    df, status, color, desc = calc_governance(data)

    assert "VIX" in df.columns
    assert df['VIX'].iloc[-1] == 0.0
    assert status == "COMFORT ZONE"

def test_calc_governance_data_error():
    """Test invalid data input."""
    # Passing None should trigger the try/except block
    # calc_governance(None) -> None['Close'] raises TypeError -> caught

    df, status, color, desc = calc_governance(None)
    assert status == "DATA ERROR"
    assert desc == "Feed Disconnected"
