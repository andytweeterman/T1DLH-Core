import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_mock_cgm():
    """
    Generates a mock Continuous Glucose Monitor (CGM) data feed.
    Returns a pandas DataFrame with 24 hours of data, with a new row every 5 minutes.
    Columns: Timestamp, Glucose_Value, Trend.
    """
    # Number of data points: 24 hours * 12 points per hour = 288 points
    num_points = 24 * 12
    end_time = datetime.now()
    # Create timestamps: every 5 minutes ending at end_time
    # We generate points going backwards from now, then reverse to be chronological
    timestamps = [end_time - timedelta(minutes=5 * i) for i in range(num_points)]
    timestamps.reverse()

    # Generate random walk for glucose values with momentum
    glucose_values = []
    # Start with a random value within a reasonable range (e.g., 90-150)
    current_value = np.random.randint(90, 150)
    glucose_values.append(current_value)

    # Momentum factor to create smooth curves
    current_trend_val = 0

    for _ in range(num_points - 1):
        # Update trend value slightly to simulate changing metabolic conditions
        # Bias the trend update to keep it somewhat stable but changing
        trend_delta = np.random.randint(-2, 3) # -2 to 2
        current_trend_val += trend_delta

        # Dampen the trend if it gets too high to avoid runaway values
        if abs(current_trend_val) > 8:
            current_trend_val = int(current_trend_val * 0.8)

        # Add some noise
        noise = np.random.randint(-2, 3)
        change = current_trend_val + noise

        current_value += change

        # Clamp value between 70 and 220 and reset trend if hitting bounds
        if current_value < 70:
            current_value = 70
            current_trend_val = abs(current_trend_val) // 2 + 1 # Bounce up
        elif current_value > 220:
            current_value = 220
            current_trend_val = -(abs(current_trend_val) // 2 + 1) # Bounce down

        glucose_values.append(current_value)

    # Create DataFrame
    df = pd.DataFrame({
        'Timestamp': timestamps,
        'Glucose_Value': glucose_values
    })

    # Generate Trend column based on rate of change
    # Calculate difference
    df['diff'] = df['Glucose_Value'].diff().fillna(0)

    def get_trend(change):
        if change > 15:
            return 'DoubleUp'
        elif 10 < change <= 15:
            return 'SingleUp'
        elif 5 < change <= 10:
            return 'FortyFiveUp'
        elif -5 <= change <= 5:
            return 'Flat'
        elif -10 <= change < -5:
            return 'FortyFiveDown'
        elif -15 <= change < -10:
            return 'SingleDown'
        else: # change < -15
            return 'DoubleDown'

    df['Trend'] = df['diff'].apply(get_trend)

    # Drop the diff column as it's not requested in the final output
    df = df.drop(columns=['diff'])

    return df

if __name__ == "__main__":
    df = get_mock_cgm()
    print("DataFrame Head:")
    print(df.head())
    print("\nDataFrame Tail:")
    print(df.tail())
    print("\nDataFrame Info:")
    print(df.info())
    print("\nTrend Counts:")
    print(df['Trend'].value_counts())
