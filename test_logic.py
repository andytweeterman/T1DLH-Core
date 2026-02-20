import pandas as pd
import numpy as np
import pytest
import logic

def create_mock_data(days=50):
    dates = pd.date_range(end=pd.Timestamp.now(), periods=days, freq='B')
    tickers = ["SPY", "^DJI", "^IXIC", "HYG", "IEF", "^VIX", "RSP", "DX-Y.NYB", "GC=F", "CL=F"]

    # Create MultiIndex columns
    # We only really need 'Close' for logic.calc_governance
    columns = pd.MultiIndex.from_product([['Close'], tickers], names=['Attribute', 'Ticker'])

    df = pd.DataFrame(index=dates, columns=columns)

    # Initialize with some default values to avoid NaNs
    # Default: Stable market
    # HYG/IEF ratio = 1.0 (constant)
    # VIX = 15.0
    # RSP/SPY ratio = 1.0
    # DXY = 100.0

    for ticker in tickers:
        df[('Close', ticker)] = 100.0

    df[('Close', '^VIX')] = 15.0

    # Ensure types are float
    df = df.astype(float)

    return df

def test_calc_governance_red_status():
    """
    Test for RED status: "DEFENSIVE MODE", "#f93e3e", "Structural Failure Confirmed"
    Requires:
    1. Stress Signal: (Credit Delta < -0.015) OR (DXY Delta > 0.02)
    2. VIX Signal: VIX > 25.0
    """
    data = create_mock_data(days=50)

    # --- Trigger VIX Signal ---
    # Set VIX to 26.0 for the last row
    data.loc[data.index[-1], ('Close', '^VIX')] = 26.0

    # --- Trigger Stress Signal (Credit Delta < -0.015) ---
    # Credit_Ratio = HYG / IEF
    # Credit_Delta = Credit_Ratio.pct_change(10)
    # We need Credit_Ratio to drop by > 1.5% over last 10 days.

    # Let's keep IEF constant at 100.0
    # Let's drop HYG.
    # Day -10: HYG = 100.0 -> Ratio = 1.0
    # Day 0: HYG = 98.0 -> Ratio = 0.98
    # Delta = (0.98 - 1.0) / 1.0 = -0.02 (-2.0%)
    # This is < -0.015.

    # Set HYG to 100.0 for all days except the last one
    data.loc[:, ('Close', 'HYG')] = 100.0
    data.loc[:, ('Close', 'IEF')] = 100.0

    # Drop HYG at the end
    data.loc[data.index[-1], ('Close', 'HYG')] = 98.0

    # Ensure DXY doesn't trigger anything conflicting (though OR condition means we just need one)
    # DXY_Delta = pct_change(5). Keep DXY constant.
    data.loc[:, ('Close', 'DX-Y.NYB')] = 100.0

    # Ensure Breadth doesn't interfere (Breadth Breakdown is used for YELLOW)
    # But if we have RED conditions, they should take precedence.
    # RED check is first: `if l_stress and l_vix:`

    gov_df, status, color, reason = logic.calc_governance(data)

    assert status == "DEFENSIVE MODE"
    assert color == "#f93e3e"
    assert reason == "Structural Failure Confirmed"

def test_calc_governance_green_status():
    """
    Test for GREEN status: "COMFORT ZONE", "#00d26a", "System Integrity Nominal"
    """
    data = create_mock_data(days=50)

    # Stable market
    # VIX = 15.0 (< 25)
    # Credit Delta ~ 0.0 (> -0.015)
    # DXY Delta ~ 0.0 (< 0.02)
    # Breadth Delta ~ 0.0 (> -0.025)

    gov_df, status, color, reason = logic.calc_governance(data)

    assert status == "COMFORT ZONE"
    assert color == "#00d26a"
    assert reason == "System Integrity Nominal"
