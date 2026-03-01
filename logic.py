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

def calc_glycemic_risk(df, current_context="Normal"):
    """Applies ERM logic mapped to the streamlined context variables."""
    try:
        latest = df.iloc[-1]
        bg = latest['Glucose_Value']
        trend = latest['Trend']
        
        # Logic Gate 1 (Critical Risk / Exercise Burn)
        if bg < 70 or (bg < 90 and trend == 'Falling') or (bg < 100 and current_context == 'Exercise'):
            return df, "NEEDS ATTENTION", "Low blood sugar or exercise crash risk"
        
        # Logic Gate 2 (Resistance / Stress / Illness)
        elif bg > 180 or (bg > 140 and current_context in ["Stressed", "Sick"]):
            return df, "CAUTION", "Elevated due to stress or illness resistance"
        
        # Logic Gate 3 (Travel / Logistics)
        elif current_context == "Travel":
            return df, "WATCHLIST", "Travel mode active: Monitor logistics and transit"
            
        # Logic Gate 4 (Nominal)
        else:
            return df, "STABLE", "Blood sugar and activity are stable"
            
    except Exception as e:
        return df, "ERROR", f"Error: {e}"