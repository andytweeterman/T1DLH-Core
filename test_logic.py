import pytest
import pandas as pd
import numpy as np
import logic

def create_mock_data(days=30, overrides=None):
    """
    Creates a mock DataFrame mimicking yfinance structure.

    Args:
        days (int): Number of days of data to generate.
        overrides (dict): Dictionary of ticker -> list of values (or single value) to override defaults.
                          If list, must be of length `days`.
                          If single value, it's applied to all days.
    """
    dates = pd.date_range(end=pd.Timestamp.now(), periods=days, freq='B')
    tickers = ["SPY", "^DJI", "^IXIC", "HYG", "IEF", "^VIX", "RSP", "DX-Y.NYB", "GC=F", "CL=F"]

    # Create random base data (stable)
    data = {}
    for ticker in tickers:
        data[ticker] = np.full(days, 100.0) # Default constant 100

    # Apply defaults for specific tickers to be realistic
    data["^VIX"] = np.full(days, 15.0)
    data["DX-Y.NYB"] = np.full(days, 100.0)

    # Apply overrides
    if overrides:
        for ticker, values in overrides.items():
            if isinstance(values, list) or isinstance(values, np.ndarray):
                if len(values) != days:
                    # Pad or trim
                    if len(values) < days:
                         # Pad with the first value at the beginning
                         pad = [values[0]] * (days - len(values))
                         values = pad + list(values)
                    else:
                        values = values[-days:]
                data[ticker] = values
            else:
                data[ticker] = np.full(days, values)

    # Create DataFrame
    df = pd.DataFrame(data, index=dates)

    # Create MultiIndex columns with 'Close' at level 0
    # yfinance structure:
    #       Close
    #       HYG  IEF ...

    df.columns = pd.MultiIndex.from_product([['Close'], df.columns])

    return df

def test_calc_governance_green_status():
    """Test Happy Path: All indicators nominal."""
    mock_data = create_mock_data(days=40)

    # Calculate governance
    gov_df, status, color, reason = logic.calc_governance(mock_data)

    assert status == "COMFORT ZONE"
    assert color == "#00d26a"
    assert reason == "System Integrity Nominal"

def test_calc_governance_red_status():
    """
    Test RED Status: Requires Stress + VIX Panic.
    Stress: Credit Delta < -0.015 OR DXY Delta > 0.02
    VIX: > 25
    """
    days = 40

    # 1. Trigger VIX Panic
    # Last value > 25
    vix_values = np.full(days, 15.0)
    vix_values[-1] = 26.0

    # 2. Trigger Credit Stress
    # Credit Ratio = HYG / IEF
    # Credit Delta = Ratio.pct_change(10)
    # We want Delta < -0.015
    # Let's keep IEF constant at 100.
    # HYG starts at 100.
    # At index -1 (current), HYG drops.
    # Ratio_old (10 days ago) = 100/100 = 1.0
    # Ratio_new = HYG_new / 100
    # Delta = (Ratio_new / Ratio_old) - 1 = Ratio_new - 1
    # We want Ratio_new - 1 < -0.015 => Ratio_new < 0.985
    # So HYG_new < 98.5

    hyg_values = np.full(days, 100.0)
    hyg_values[-1] = 98.0 # 2% drop

    overrides = {
        "^VIX": vix_values,
        "HYG": hyg_values,
        "IEF": 100.0
    }

    mock_data = create_mock_data(days=days, overrides=overrides)

    # Calculate governance
    gov_df, status, color, reason = logic.calc_governance(mock_data)

    # Verify Stress Signal logic
    # Credit Ratio check
    credit_ratio = mock_data['Close']['HYG'] / mock_data['Close']['IEF']
    credit_delta = credit_ratio.pct_change(10)
    # The last value should be < -0.015
    assert credit_delta.iloc[-1] < -0.015, f"Credit Delta was {credit_delta.iloc[-1]}"

    # Verify VIX Signal logic
    assert mock_data['Close']['^VIX'].iloc[-1] > 25.0

    # Verify Result
    assert status == "DEFENSIVE MODE"
    assert color == "#f93e3e"
    assert reason == "Structural Failure Confirmed"
