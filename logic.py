import pandas as pd
import numpy as np
from datetime import datetime, timedelta
<<<<<<< t1dlh-rewrite-18443275941457154469
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
=======
import os
import streamlit as st
from mock_data import get_mock_cgm

@st.cache_data(ttl=3600)
def fetch_health_data():
    """Fetches mock CGM data."""
    return get_mock_cgm()

def calc_glycemic_risk(data, current_context="Nominal"):
    """
    Analyzes the latest row in the CGM data and applies ERM style rules.
    """
    try:
        if data is None or data.empty:
            return data, "SYSTEM BOOT", "#A5ADCB", "Initializing..."

        latest = data.iloc[-1]
        current_glucose = latest['glucose']
        trend = latest['trend']

        # Logic Gate 1 (Severe Hypo / Transit Risk - RED)
        if (current_glucose < 70) or \
           (current_glucose < 90 and trend in ['DoubleDown', 'SingleDown']) or \
           (current_glucose < 100 and current_context == "Driving"):
            return data, "DEFENSIVE MODE", "#ED8796", "Critical: Hypoglycemic or Transit Risk"

        # Logic Gate 2 (Stress / Hyperglycemia - YELLOW)
        elif (current_glucose > 180) or \
             (current_glucose > 140 and current_context in ["High Stress Meeting", "Capital One Strategy Review"]):
            return data, "CAUTION", "#EED49F", "Elevated: Contextual Resistance or Hyperglycemia"

        # Logic Gate 3 (Logistical Watchlist - YELLOW)
        elif (current_context == "Pinewood Derby prep with Lucas" and current_glucose < 100):
            return data, "WATCHLIST", "#EED49F", "Activity Risk: Pre-empt with carbs"

        # Logic Gate 4 (Nominal - GREEN)
        else:
            return data, "COMFORT ZONE", "#A6DA95", "Metabolic & Contextual Stability"

    except Exception as e:
        # In case of error, return safe default or error state
        return data, "DATA ERROR", "#A5ADCB", f"Error: {str(e)}"

# --- STANDARD MATH FUNCTIONS ---
def calc_ppo(price):
    if isinstance(price, pd.DataFrame): price = price.iloc[:, 0]
    ema12 = price.ewm(span=12, adjust=False).mean()
    ema26 = price.ewm(span=26, adjust=False).mean()
    ppo_line = ((ema12 - ema26) / ema26) * 100
    signal_line = ppo_line.ewm(span=9, adjust=False).mean()
    hist = ppo_line - signal_line
    return ppo_line, signal_line, hist

def calc_cone(price):
    if isinstance(price, pd.DataFrame): price = price.iloc[:, 0]
    window = 20
    sma = price.rolling(window=window).mean()
    std = price.rolling(window=window).std()
    upper_band = sma + (1.28 * std)
    lower_band = sma - (1.28 * std)
    return sma, std, upper_band, lower_band

def generate_forecast(start_date, last_price, last_std, days=30):
    future_dates = [start_date + timedelta(days=i) for i in range(1, days + 1)]
    drift = 0.0003
    i_values = np.arange(1, days + 1)
    future_mean = last_price * ((1 + drift) ** i_values)
    time_factor = np.sqrt(i_values)
    width = (1.28 * last_std) + (last_std * 0.1 * time_factor)
    future_upper = future_mean + width
    future_lower = future_mean - width
    return future_dates, future_mean.tolist(), future_upper.tolist(), future_lower.tolist()

@st.cache_data(ttl=3600)
def load_strategist_data():
    try:
        root_dir = os.path.dirname(os.path.abspath(__file__))
        root_file = os.path.join(root_dir, "^GSPC.csv")
        if os.path.exists(root_file):
            df = pd.read_csv(root_file)
        else:
            filename = os.path.join("data", "strategist_forecast.csv")
            if not os.path.exists(filename): return None
            df = pd.read_csv(filename)
        required_cols = ['Date', 'Tstk_Adj', 'FP1', 'FP3', 'FP6']
        if not all(col in df.columns for col in required_cols): return None
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception: return None

def get_strategist_update():
    try:
        sheet_url = os.environ.get("STRATEGIST_SHEET_URL")
        if not sheet_url and "STRATEGIST_SHEET_URL" in st.secrets:
            sheet_url = st.secrets["STRATEGIST_SHEET_URL"]
        if sheet_url and "INSERT_YOUR" not in sheet_url:
            return pd.read_csv(sheet_url)
        local_path = os.path.join("data", "update.csv")
        if os.path.exists(local_path): return pd.read_csv(local_path)
        return None
    except Exception: return None
>>>>>>> main
