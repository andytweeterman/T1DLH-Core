import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add the parent directory to sys.path to import logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logic

def test_calc_ppo_constant():
    # Create a constant price series
    prices = pd.Series([100.0] * 50)

    # Calculate PPO
    ppo, signal, hist = logic.calc_ppo(prices)

    # Verify types
    assert isinstance(ppo, pd.Series)
    assert isinstance(signal, pd.Series)
    assert isinstance(hist, pd.Series)

    # Verify values are close to 0 (EMA(100) = 100, PPO = 0)
    assert np.allclose(ppo, 0.0)
    assert np.allclose(signal, 0.0)
    assert np.allclose(hist, 0.0)

def test_calc_ppo_dataframe_input():
    # Create a DataFrame with a constant price column
    df = pd.DataFrame({'Close': [100.0] * 50})

    # Calculate PPO passing the DataFrame
    ppo, signal, hist = logic.calc_ppo(df)

    # Verify types - calc_ppo logic takes iloc[:, 0] so it returns Series
    assert isinstance(ppo, pd.Series)
    assert isinstance(signal, pd.Series)
    assert isinstance(hist, pd.Series)

    # Verify values
    assert np.allclose(ppo, 0.0)

def test_calc_ppo_trend():
    # Create an increasing price series
    # Using float to ensure precision
    prices = pd.Series(np.linspace(100.0, 200.0, 50))

    # Calculate PPO
    ppo, signal, hist = logic.calc_ppo(prices)

    # In an uptrend, EMA12 should be > EMA26 generally, so PPO > 0
    # The first value starts at 0 difference because of adjust=False initialization
    # checking from index 1 onwards
    assert (ppo.iloc[1:] > 0).all()

def test_calc_ppo_empty():
    # Create an empty series
    prices = pd.Series([], dtype=float)

    # Calculate PPO
    ppo, signal, hist = logic.calc_ppo(prices)

    # Verify empty output
    assert ppo.empty
    assert signal.empty
    assert hist.empty

def test_calc_ppo_with_nans():
    # Create a series with NaNs
    prices = pd.Series([100.0, np.nan, 100.0, 100.0, 100.0])

    # Calculate PPO
    ppo, signal, hist = logic.calc_ppo(prices)

    # Verify types
    assert isinstance(ppo, pd.Series)

    # Check that NaNs are handled (propagated or ignored depending on implementation)
    # With adjust=False, a NaN in input usually results in NaN in output for that step
    # and subsequent steps might be affected if not ignored.
    # Actually pandas ewm ignores NaNs by default during calculation but keeps them in result?
    # Let's see. If the implementation doesn't explicitly handle NaNs, we just want to ensure it doesn't crash.
    assert len(ppo) == len(prices)

    # Check specifically if it crashes or returns series
    assert not ppo.empty
