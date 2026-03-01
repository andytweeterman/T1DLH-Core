import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def fetch_health_data():
    """Generates 24 hours of mock CGM data."""
    now = datetime.now()
    times = pd.date_range(end=now, periods=288, freq='5min')
    
    # Create a realistic glucose curve
    base = 120 + 30 * np.sin(np.linspace(0, 3*np.pi, 288))
    noise = np.random.normal(0, 4, 288)
    glucose = np.clip(base + noise, 65, 220).astype(int)
    
    df = pd.DataFrame({'Timestamp': times, 'Glucose_Value': glucose})
    df['Trend'] = 'Steady'
    df.loc[df['Glucose_Value'].diff() > 3, 'Trend'] = 'Rising'
    df.loc[df['Glucose_Value'].diff() < -3, 'Trend'] = 'Falling'
    
    return df

def calc_glycemic_risk(df, current_context="Nominal"):
    """Applies ERM logic to biological data."""
    try:
        latest = df.iloc[-1]
        bg = latest['Glucose_Value']
        trend = latest['Trend']
        
        # Logic Gate 1 (Critical Risk)
        if bg < 70 or (bg < 90 and trend == 'Falling') or (bg < 100 and current_context == 'Driving'):
            return df, "NEEDS ATTENTION", "#ED8796", "Low blood sugar or transit risk"
        
        # Logic Gate 2 (Contextual Resistance)
        elif bg > 180 or (bg > 140 and current_context in ["High Stress Meeting", "Capital One Strategy Review"]):
            return df, "CAUTION", "#EED49F", "Elevated due to activity or high blood sugar"
        
        # Logic Gate 3 (Activity Watchlist)
        elif current_context == "Pinewood Derby prep with Lucas" and bg < 100:
            return df, "WATCHLIST", "#EED49F", "Activity ahead: Consider a snack"
            
        # Logic Gate 4 (Nominal)
        else:
            return df, "STABLE", "#A6DA95", "Blood sugar and activity are stable"
            
    except Exception as e:
        return df, "ERROR", "#ED8796", f"Error: {e}"