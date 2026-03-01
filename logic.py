import pandas as pd
import numpy as np
import requests
import streamlit as st
from datetime import datetime, timedelta

def fetch_health_data():
    """Fetches real data from Dexcom API, with a graceful fallback to mock data."""
    
    # 1. ATTEMPT TO FETCH REAL API DATA
    dexcom_token = st.secrets.get("DEXCOM_ACCESS_TOKEN", None)
    
    if dexcom_token:
        try:
            # Dexcom V3 API requires a time range (last 24 hours)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            
            url = "https://sandbox-api.dexcom.com/v3/users/self/egvs"
            headers = {
                "Authorization": f"Bearer {dexcom_token}"
            }
            params = {
                "startDate": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "endDate": end_time.strftime("%Y-%m-%dT%H:%M:%S")
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('records', [])
                
                if records:
                    df = pd.DataFrame(records)
                    
                    # Map Dexcom's JSON to our expected DataFrame format
                    df['Timestamp'] = pd.to_datetime(df['systemTime'])
                    df['Glucose_Value'] = df['value']
                    
                    # Sort chronologically (oldest to newest)
                    df = df.sort_values('Timestamp').reset_index(drop=True)
                    
                    # Map Dexcom's official trend arrows, with a fallback calculation
                    if 'trend' in df.columns:
                        df['Trend'] = df['trend'].str.replace('([A-Z])', r' \1', regex=True).str.title()
                    else:
                        df['Trend'] = 'Steady'
                        df.loc[df['Glucose_Value'].diff() > 3, 'Trend'] = 'Rising'
                        df.loc[df['Glucose_Value'].diff() < -3, 'Trend'] = 'Falling'
                    
                    return df[['Timestamp', 'Glucose_Value', 'Trend']]
                    
        except Exception as e:
            # If the API call fails, we log it and silently fall back to mock data
            print(f"API Integration Error: {e}")

    # 2. GRACEFUL FALLBACK (Mock Data)
    now = datetime.now()
    times = pd.date_range(end=now, periods=288, freq='5min')
    
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
        if bg < 70 or (bg < 90 and trend in ['Falling', 'Single Down', 'Double Down']) or (bg < 100 and current_context == 'Exercise'):
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