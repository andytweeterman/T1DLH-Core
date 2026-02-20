import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def fetch_health_data():
    """Generates mock CGM data for the last 24 hours."""
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='5min')

    # Generate mock glucose values
    # Random walk with bounds
    values = []
    current_bg = 110

    # Create a smoother curve
    for i in range(len(timestamps)):
        if i == 0:
             values.append(current_bg)
             continue

        # Random change but with momentum-like behavior
        change = random.gauss(0, 2)
        current_bg += change

        # Enforce realistic bounds
        current_bg = max(50, min(300, current_bg))
        values.append(int(current_bg))

    df = pd.DataFrame({'Timestamp': timestamps, 'Glucose': values})
    df.set_index('Timestamp', inplace=True)

    # Calculate Trend
    df['Delta'] = df['Glucose'].diff()

    def get_trend_arrow(delta):
        if pd.isna(delta): return "→"
        if delta > 3: return "↑"
        if delta > 1: return "↗"
        if delta < -3: return "↓"
        if delta < -1: return "↘"
        return "→"

    df['Trend'] = df['Delta'].apply(get_trend_arrow)

    return df

def get_active_insulin():
    """Returns mock Active Insulin (IOB)."""
    return round(random.uniform(0.5, 3.5), 2)

def get_schedule():
    """Returns mock schedule data."""
    events = [
        "Capital One Strategy Review",
        "Driving to Airport",
        "Lunch with Team",
        "Deep Work Block",
        "Gym Session",
        "Client Meeting",
        "Sleep"
    ]
    return random.choice(events)

def calc_glycemic_risk(data, current_context):
    """
    Evaluates glycemic risk based on glucose and context.
    Returns: (data, status, color, reason)
    """
    if data is None or data.empty:
        return data, "DATA ERROR", "#888888", "No Data Available"

    current_bg = data['Glucose'].iloc[-1]
    trend = data['Trend'].iloc[-1]

    status = "COMFORT ZONE"
    color = "#00d26a"
    reason = "Stable Glycemia"

    # Contextual Modifiers
    if "Driving" in current_context:
        if current_bg < 100:
            status = "DEFENSIVE MODE"
            color = "#f93e3e"
            reason = "Hypo Risk while Driving"
        elif current_bg > 250:
             status = "CAUTION"
             color = "#ffaa00"
             reason = "Hyperglycemia while Driving"
        else:
             status = "WATCHLIST"
             color = "#f1c40f"
             reason = "Monitor Closely while Driving"

    elif "Gym" in current_context or "Workout" in current_context:
         if current_bg < 120:
            status = "CAUTION"
            color = "#ffaa00"
            reason = "Pre-Workout Carb Load Needed"
         else:
            status = "COMFORT ZONE"
            color = "#00d26a"
            reason = "Ready for Activity"

    else: # Standard Logic
        if current_bg < 70:
            status = "DEFENSIVE MODE"
            color = "#f93e3e"
            reason = "Hypoglycemia Detected"
        elif current_bg > 250:
            status = "DEFENSIVE MODE"
            color = "#f93e3e"
            reason = "Severe Hyperglycemia"
        elif current_bg > 180:
            status = "WATCHLIST"
            color = "#f1c40f"
            reason = "Hyperglycemia Detected"
        elif trend in ['↓', '↘'] and current_bg < 100:
             status = "CAUTION"
             color = "#ffaa00"
             reason = "Dropping Fast"
        elif trend in ['↑', '↗'] and current_bg > 160:
             status = "WATCHLIST"
             color = "#f1c40f"
             reason = "Rising Rapidly"

    return data, status, color, reason
