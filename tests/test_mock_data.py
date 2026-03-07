import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from logic import fetch_health_data

def test_get_mock_cgm_shape_and_columns():
    df = fetch_health_data()

    assert isinstance(df, pd.DataFrame)

    # 24 hours * 12 points per hour = 288 points
    assert len(df) == 288

    # Check correct columns
    expected_columns = ['Timestamp', 'Glucose_Value', 'Trend']
    assert list(df.columns) == expected_columns

def test_get_mock_cgm_timestamps():
    df = fetch_health_data()

    # Check timestamps are in chronological order
    assert df['Timestamp'].is_monotonic_increasing

    # Check timestamps are exactly 5 minutes apart
    time_diffs = df['Timestamp'].diff().dropna()
    expected_diff = timedelta(minutes=5)

    assert (time_diffs == expected_diff).all()

    # Check the last timestamp is close to current time (within 1 minute to account for processing)
    now = datetime.now()
    last_timestamp = df['Timestamp'].iloc[-1]
    assert abs((now - last_timestamp).total_seconds()) < 60

def test_get_mock_cgm_glucose_values():
    df = fetch_health_data()

    # Check all values are within the clamped boundaries
    assert df['Glucose_Value'].min() >= 65
    assert df['Glucose_Value'].max() <= 220

    # Check all values are integers (or can be represented as such, the function generates ints)
    assert pd.api.types.is_numeric_dtype(df['Glucose_Value'])

def test_get_mock_cgm_trends():
    df = fetch_health_data()

    # Reconstruct the difference to test the trend assignment logic
    diffs = df['Glucose_Value'].diff().fillna(0)

    for i, change in enumerate(diffs):
        if change > 3:
            expected_trend = 'Rising'
        elif change < -3:
            expected_trend = 'Falling'
        else:
            expected_trend = 'Steady'

        assert df['Trend'].iloc[i] == expected_trend

def test_get_mock_cgm_deterministic():
    # Because there's a lot of randomness, let's just make sure multiple calls return different data
    df1 = fetch_health_data()
    fetch_health_data.clear()
    df2 = fetch_health_data()

    # It's extremely unlikely these would be exactly the same
    assert not df1['Glucose_Value'].equals(df2['Glucose_Value'])
