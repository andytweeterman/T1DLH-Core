import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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
            return data, "SYSTEM BOOT", "#888888", "Initializing..."

        latest = data.iloc[-1]
        current_glucose = latest['glucose']
        trend = latest['trend']

        # Logic Gate 1 (Severe Hypo / Transit Risk - RED)
        if (current_glucose < 70) or \
           (current_glucose < 90 and trend in ['DoubleDown', 'SingleDown']) or \
           (current_glucose < 100 and current_context == "Driving"):
            return data, "DEFENSIVE MODE", "#f93e3e", "Critical: Hypoglycemic or Transit Risk"

        # Logic Gate 2 (Stress / Hyperglycemia - YELLOW)
        elif (current_glucose > 180) or \
             (current_glucose > 140 and current_context in ["High Stress Meeting", "Capital One Strategy Review"]):
            return data, "CAUTION", "#ffaa00", "Elevated: Contextual Resistance or Hyperglycemia"

        # Logic Gate 3 (Logistical Watchlist - YELLOW)
        elif (current_context == "Pinewood Derby prep with Lucas" and current_glucose < 100):
            return data, "WATCHLIST", "#f1c40f", "Activity Risk: Pre-empt with carbs"

        # Logic Gate 4 (Nominal - GREEN)
        else:
            return data, "COMFORT ZONE", "#00d26a", "Metabolic & Contextual Stability"

    except Exception as e:
        # In case of error, return safe default or error state
        return data, "DATA ERROR", "#888888", f"Error: {str(e)}"

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
