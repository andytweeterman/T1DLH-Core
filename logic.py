import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import os
import streamlit as st

@st.cache_data(ttl=3600)
def fetch_market_data():
    """Fetches data from Yahoo Finance and cleans it immediately."""
    try:
        tickers = ["SPY", "^DJI", "^IXIC", "HYG", "IEF", "^VIX", "RSP", "DX-Y.NYB", "GC=F", "CL=F"]
        start = (datetime.now() - timedelta(days=1825)).strftime('%Y-%m-%d')
        data = yf.download(tickers, start=start, progress=False)
        
        if data is None or data.empty:
            return None

        # Fix the "Sunday Gap" by carrying forward Friday's data
        data = data.ffill()
        
        return data
    except Exception:
        return None

def calc_governance(data):
    """Calculates the 'Traffic Light' safety status with smoothed logic."""
    try:
        closes = data['Close']
        df = pd.DataFrame(index=closes.index)
        
        # --- CALCULATE METRICS ---
        df['Credit_Ratio'] = closes["HYG"] / closes["IEF"]
        df['Credit_Delta'] = df['Credit_Ratio'].pct_change(10)
        
        if "^VIX" in closes.columns:
            df['VIX'] = closes["^VIX"]
        else:
            df['VIX'] = 0.0

        df['Breadth_Ratio'] = closes["RSP"] / closes["SPY"]
        df['Breadth_Delta'] = df['Breadth_Ratio'].pct_change(20)
        df['DXY_Delta'] = closes["DX-Y.NYB"].pct_change(5)
        
        # --- DEFINE TRIGGERS ---
        CREDIT_TRIG = -0.015  # -1.5% widening
        VIX_PANIC = 25.0      # Increased from 24 to 25 for stability
        BREADTH_TRIG = -0.025
        DXY_SPIKE = 0.02
        
        # --- LOGIC GATES ---
        # 1. Structural Stress (Credit or Dollar)
        stress_signal = ((df['Credit_Delta'] < CREDIT_TRIG) | (df['DXY_Delta'] > DXY_SPIKE)).fillna(False)
        
        # 2. VIX Panic
        vix_signal = (df['VIX'] > VIX_PANIC).fillna(False)
        
        # 3. Breadth Breakdown
        breadth_signal = (df['Breadth_Delta'] < BREADTH_TRIG).fillna(False)
        
        if not df.empty:
            latest = df.iloc[-1]
            l_stress = stress_signal.iloc[-1]
            l_vix = vix_signal.iloc[-1]
            l_breadth = breadth_signal.iloc[-1]
        else:
            return df, "SYSTEM BOOT", "#888888", "Initializing..."

        # --- DETERMINE STATUS (The Tuned Logic) ---
        
        # RED: Requires Stress + VIX Panic (The Confirmation Rule)
        if l_stress and l_vix:
             return df, "DEFENSIVE MODE", "#f93e3e", "Structural Failure Confirmed"
             
        # OR RED: If VIX is simply massive (>30)
        elif latest['VIX'] > 30:
             return df, "DEFENSIVE MODE", "#f93e3e", "Extreme Volatility"

        # YELLOW: Stress Detected (but VIX < 25) OR Breadth Warning
        elif l_stress:
             return df, "CAUTION", "#ffaa00", "Credit/Currency Stress"
        elif l_vix:
             return df, "CAUTION", "#ffaa00", "Elevated Volatility"
        elif l_breadth:
             return df, "WATCHLIST", "#f1c40f", "Market Breadth Narrowing"
             
        # GREEN: All Clear
        else: 
            return df, "COMFORT ZONE", "#00d26a", "System Integrity Nominal"
            
    except Exception:
        safe_df = pd.DataFrame()
        return safe_df, "DATA ERROR", "#888888", "Feed Disconnected"

# --- STANDARD MATH FUNCTIONS ---
def calc_ppo(price):
    if isinstance(price, pd.DataFrame): price = price.iloc[:, 0]
    ema12 = price.ewm(span=12, adjust=False).mean()
    ema26 = price.ewm(span=26, adjust=False).mean()
    ppo_line = ((ema12 - ema26) / ema26) * 100
    signal_line = ppo_line.ewm(span=9, adjust=False).mean()
    hist = ppo_line - signal_line
    return ppo_line, signal_line, hist

@st.cache_data
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