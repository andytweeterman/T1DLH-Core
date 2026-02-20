import pytest
import pandas as pd
import numpy as np
from logic import calc_cone

class TestCalcCone:

    def test_calc_cone_series_happy_path(self):
        """Test with a pandas Series input having sufficient data."""
        # Create a series with 30 data points (0 to 29)
        data = pd.Series(np.arange(30, dtype=float))

        sma, std, upper, lower = calc_cone(data)

        # Check types
        assert isinstance(sma, pd.Series)
        assert isinstance(std, pd.Series)
        assert isinstance(upper, pd.Series)
        assert isinstance(lower, pd.Series)

        # Check length
        assert len(sma) == 30

        # First 19 values should be NaN because window=20
        assert sma.iloc[:19].isna().all()
        assert std.iloc[:19].isna().all()
        assert upper.iloc[:19].isna().all()
        assert lower.iloc[:19].isna().all()

        # 20th value (index 19) should be valid
        assert not pd.isna(sma.iloc[19])

    def test_calc_cone_dataframe_input(self):
        """Test with a pandas DataFrame input."""
        # Create a DataFrame
        data = pd.DataFrame({'price': np.arange(30, dtype=float)})

        sma, std, upper, lower = calc_cone(data)

        # Should behave same as series
        assert len(sma) == 30
        assert not pd.isna(sma.iloc[19])

    def test_calc_cone_insufficient_data(self):
        """Test with fewer than 20 data points."""
        data = pd.Series(np.arange(10, dtype=float))

        sma, std, upper, lower = calc_cone(data)

        # All should be NaN
        assert sma.isna().all()
        assert std.isna().all()
        assert upper.isna().all()
        assert lower.isna().all()

    def test_calc_cone_exact_window(self):
        """Test with exactly 20 data points."""
        data = pd.Series(np.arange(20, dtype=float))

        sma, std, upper, lower = calc_cone(data)

        # Only the last point should be valid
        assert sma.iloc[:-1].isna().all()
        assert not pd.isna(sma.iloc[-1])

    def test_calc_cone_calculation_correctness(self):
        """Verify the mathematical correctness of the SMA, STD, and bands."""
        # Create a constant series. SMA should be the constant, STD should be 0.
        val = 100.0
        data = pd.Series([val] * 25)

        sma, std, upper, lower = calc_cone(data)

        # Check last value
        expected_sma = val
        expected_std = 0.0

        assert np.isclose(sma.iloc[-1], expected_sma)
        assert np.isclose(std.iloc[-1], expected_std)
        assert np.isclose(upper.iloc[-1], expected_sma + 1.28 * expected_std)
        assert np.isclose(lower.iloc[-1], expected_sma - 1.28 * expected_std)

        # Create a simple increasing series: 0, 1, 2, ...
        # For window 20 ending at 19 (0..19), mean is 9.5
        # pandas rolling std uses N-1 by default (sample standard deviation).

        data_linear = pd.Series(np.arange(25, dtype=float))
        sma, std, upper, lower = calc_cone(data_linear)

        # Let's check index 19 (values 0 to 19)
        subset = data_linear.iloc[0:20]
        expected_sma = subset.mean()
        expected_std = subset.std(ddof=1)

        assert np.isclose(sma.iloc[19], expected_sma)
        assert np.isclose(std.iloc[19], expected_std)

        # Check bands
        assert np.isclose(upper.iloc[19], expected_sma + 1.28 * expected_std)
        assert np.isclose(lower.iloc[19], expected_sma - 1.28 * expected_std)
