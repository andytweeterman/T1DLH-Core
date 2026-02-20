import sys
import os
import pandas as pd
import numpy as np
import pytest

# Add parent directory to path to import logic.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logic

def test_calc_governance_yellow_stress_vix_low():
    """
    Test the 'YELLOW: Stress Detected (but VIX < 25)' branch.
    Scenario:
    - VIX is low (20.0).
    - Stress is detected via DXY spike (Currency Stress).
    - Credit stress is not present.
    - Breadth is stable.
    Expected Result: "CAUTION", "#ffaa00", "Credit/Currency Stress"
    """
    # Construct a mock DataFrame
    # Need enough history for pct_change(20) for Breadth
    dates = pd.date_range(end=pd.Timestamp.now(), periods=30)

    tickers = ["SPY", "^DJI", "^IXIC", "HYG", "IEF", "^VIX", "RSP", "DX-Y.NYB", "GC=F", "CL=F"]

    # Create the 'Close' DataFrame
    close_data = pd.DataFrame(index=dates, columns=tickers)

    # Initialize with stable values
    close_data["SPY"] = 100.0
    close_data["^DJI"] = 30000.0
    close_data["^IXIC"] = 10000.0
    close_data["HYG"] = 100.0
    close_data["IEF"] = 100.0 # Ratio 1.0
    close_data["^VIX"] = 20.0 # Low VIX (< 25)
    close_data["RSP"] = 100.0 # Ratio 1.0
    close_data["DX-Y.NYB"] = 100.0
    close_data["GC=F"] = 1000.0
    close_data["CL=F"] = 70.0

    # Introduce Stress Trigger: DXY Spike > 2% (0.02) over 5 days.
    # We want the last row to trigger this.
    # DXY_Delta = close_data["DX-Y.NYB"].pct_change(5)
    # We need the value at -1 (last) vs -6 (5 days ago) to be > 2%.
    # 5 days ago (index -6) is 100.0.
    # Target index -1: 100.0 * 1.03 = 103.0 (3% increase).
    close_data.iloc[-1, close_data.columns.get_loc("DX-Y.NYB")] = 103.0

    # Ensure other triggers are NOT met.
    # Credit_Delta (10 days): HYG/IEF ratio. 100/100 = 1.0 constant. pct_change is 0.
    # Breadth_Delta (20 days): RSP/SPY ratio. 100/100 = 1.0 constant. pct_change is 0.

    # Construct the full 'data' object.
    # logic.calc_governance accesses data['Close']
    data = {'Close': close_data}

    # Run the function
    df_result, status, color, message = logic.calc_governance(data)

    # Assertions
    # Check intermediate calculations in the returned df
    latest = df_result.iloc[-1]
    assert latest['DXY_Delta'] > 0.02, f"DXY_Delta should be > 0.02, got {latest['DXY_Delta']}"
    assert latest['VIX'] <= 25.0, f"VIX should be <= 25.0, got {latest['VIX']}"

    # Check final status
    assert status == "CAUTION", f"Expected status 'CAUTION', got '{status}'"
    assert color == "#ffaa00", f"Expected color '#ffaa00', got '{color}'"
    assert message == "Credit/Currency Stress", f"Expected message 'Credit/Currency Stress', got '{message}'"
