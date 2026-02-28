import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from mock_data import get_mock_cgm

def test_get_mock_cgm_shape_and_columns():
    df = get_mock_cgm()

    assert isinstance(df, pd.DataFrame)

    # 24 hours * 12 points per hour = 288 points
    assert len(df) == 288

    # Check correct columns
    expected_columns = ['Timestamp', 'Glucose_Value', 'Trend']
    assert list(df.columns) == expected_columns

def test_get_mock_cgm_timestamps():
    df = get_mock_cgm()

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
    df = get_mock_cgm()

    # Check all values are within the clamped boundaries
    assert df['Glucose_Value'].min() >= 70
    assert df['Glucose_Value'].max() <= 220

    # Check all values are integers (or can be represented as such, the function generates ints)
    assert pd.api.types.is_numeric_dtype(df['Glucose_Value'])

def test_get_mock_cgm_trends():
    df = get_mock_cgm()

    # Reconstruct the difference to test the trend assignment logic
    diffs = df['Glucose_Value'].diff().fillna(0)

    for i, change in enumerate(diffs):
        expected_trend = ''
        if change > 15:
            expected_trend = 'DoubleUp'
        elif 10 < change <= 15:
            expected_trend = 'SingleUp'
        elif 5 < change <= 10:
            expected_trend = 'FortyFiveUp'
        elif -5 <= change <= 5:
            expected_trend = 'Flat'
        elif -10 <= change < -5:
            expected_trend = 'FortyFiveDown'
        elif -15 <= change < -10:
            expected_trend = 'SingleDown'
        else: # change < -15
            expected_trend = 'DoubleDown'

        assert df['Trend'].iloc[i] == expected_trend

def test_get_mock_cgm_deterministic():
    # Because there's a lot of randomness, let's just make sure multiple calls return different data
    df1 = get_mock_cgm()
    df2 = get_mock_cgm()

    # It's extremely unlikely these would be exactly the same
    assert not df1['Glucose_Value'].equals(df2['Glucose_Value'])
