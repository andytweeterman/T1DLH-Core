import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_mock_cgm():
    """
    Generates synthetic CGM data for the last 24 hours.
    Returns a DataFrame with 'Timestamp', 'Glucose_Value', and 'Trend'.
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='5T')

    # Generate synthetic glucose values (sine wave + noise)
    x = np.linspace(0, 4 * np.pi, len(timestamps))
    base_glucose = 120
    amplitude = 40
    noise = np.random.normal(0, 5, len(timestamps))
    glucose_values = base_glucose + amplitude * np.sin(x) + noise

    # Ensure no negative values and realistic range
    glucose_values = np.clip(glucose_values, 40, 400)

    # Generate trends (random)
    trends = np.random.choice(['Flat', 'Up', 'Down', 'DoubleUp', 'DoubleDown'], len(timestamps))

    return pd.DataFrame({
        'Timestamp': timestamps,
        'Glucose_Value': glucose_values,
        'Trend': trends
    })
