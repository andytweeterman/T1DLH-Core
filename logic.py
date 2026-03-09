import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. LIVE DATA INTEGRATION (NIGHTSCOUT)
# -----------------------------------------------------------------------------
def fetch_nightscout_data(url, token, count=288):
    """Fetches real-time CGM data from a user's Nightscout REST API."""
    # Clean the URL to ensure it formats the API endpoint correctly
    base_url = url.strip().rstrip('/')
    if not base_url.startswith('http'):
        base_url = 'https://' + base_url
        
    endpoint = f"{base_url}/api/v1/entries.json?count={count}"
    if token:
        endpoint += f"&token={token}"
        
    try:
        response = requests.get(endpoint, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            return None
            
        df = pd.DataFrame(data)
        
        # Standardize timestamps
        if 'date' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['date'], unit='ms')
        elif 'dateString' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['dateString'])
        else:
            return None
            
        # Safely cast glucose values
        df['Glucose_Value'] = pd.to_numeric(df.get('sgv'), errors='coerce')
        df = df.dropna(subset=['Glucose_Value'])
        
        # Map Nightscout's specific direction terminology to our UI
        trend_map = {
            "DoubleUp": "Rising Fast", "SingleUp": "Rising", "FortyFiveUp": "Rising Slowly",
            "Flat": "Steady",
            "FortyFiveDown": "Falling Slowly", "SingleDown": "Falling", "DoubleDown": "Falling Fast",
            "NONE": "Unknown", "NOT COMPUTABLE": "Unknown", "RATE OUT OF RANGE": "Unknown"
        }
        df['Trend'] = df.get('direction', 'Flat').map(trend_map).fillna('Steady')
        
        # Clean dataframe and sort chronologically (oldest to newest)
        df = df[['Timestamp', 'Glucose_Value', 'Trend']]
        df = df.sort_values(by='Timestamp').reset_index(drop=True)
        return df
        
    except Exception as e:
        print(f"Nightscout Fetch Error: {e}")
        return None

# -----------------------------------------------------------------------------
# 2. BIOMETRIC SIMULATOR (FALLBACK)
# -----------------------------------------------------------------------------
def fetch_health_data():
    """Generates 24 hours of Dexcom/Whoop data (Fallback Mock)."""
    now = datetime.now()
    times = pd.date_range(end=now, periods=288, freq='5min')
    
    base = 120 + 30 * np.sin(np.linspace(0, 3*np.pi, 288))
    noise = np.random.normal(0, 4, 288)
    glucose = np.clip(base + noise, 65, 220).astype(int)
    
    df = pd.DataFrame({'Timestamp': times, 'Glucose_Value': glucose})
    return df

def apply_context_modifiers(df, context):
    """Injects real-life chaos into the base simulated telemetry."""
    noise = np.random.normal(0, 3, len(df)) 
    
    if context == "Stressed":
        df['Glucose_Value'] += np.linspace(0, 40, len(df)) + np.random.normal(0, 8, len(df))
    elif context == "Sick":
        df['Glucose_Value'] += 50 + np.random.normal(0, 12, len(df))
    elif context == "Exercise":
        crash = np.zeros(len(df))
        crash[-24:] = np.linspace(0, -60, 24) 
        df['Glucose_Value'] += crash + noise
    elif context == "Project":
        df['Glucose_Value'] += np.linspace(0, -40, len(df)) + noise
    elif context == "Travel":
        spikes = np.zeros(len(df))
        indices = np.random.choice(range(len(df)), size=3, replace=False)
        x = np.arange(len(df))
        for idx in indices:
            spikes += 60 * np.exp(-0.5 * ((x - idx) / 6)**2) 
        df['Glucose_Value'] += spikes + noise
    else:
        df['Glucose_Value'] += noise

    diffs = df['Glucose_Value'].diff().fillna(0)
    df['Trend'] = np.where(diffs > 3, "Rising", np.where(diffs < -3, "Falling", "Steady"))
    df['Glucose_Value'] = np.clip(df['Glucose_Value'], 65, 220)
    return df

# -----------------------------------------------------------------------------
# 3. RISK ANALYSIS HELPERS
# -----------------------------------------------------------------------------
def calculate_schedule_load(meeting_count):
    if meeting_count >= 7: return 1.3, "🔴 HIGH LOAD"
    elif meeting_count >= 4: return 1.15, "🟡 ELEVATED LOAD"
    return 1.0, "🟢 LIGHT LOAD"

def get_whoop_risk_modifier(whoop_metrics):
    if not whoop_metrics: return 1.0, "No Sync"
    score = whoop_metrics.get('score', {})
    recovery = score.get('recovery_score', 100)
    strain = score.get('day_strain', 0.0)
    sleep = score.get('sleep_performance_percentage', 100)

    multiplier = 1.0
    tags = []
    if recovery < 34: multiplier += 0.3; tags.append("🔴 RED RECOVERY")
    if sleep < 70: multiplier += 0.2; tags.append("💤 SLEEP DEBT")
    if strain > 14.0: multiplier -= 0.25; tags.append("⚡ HIGH STRAIN")
    
    return multiplier, " | ".join(tags) if tags else "🟢 NOMINAL"

def is_weekend_window():
    now = datetime.now()
    if now.weekday() == 4 and now.hour >= 17: return True 
    if now.weekday() in [5, 6]: return True 
    if now.weekday() == 0 and now.hour < 8: return True 
    return False

def generate_travel_advisory(offset_hours=6):
    shift = offset_hours / 3
    return f"✈️ TRAVEL PROTOCOL: Today: Shift +{int(shift)}h. Tomorrow: +{int(shift)}h. Day 3: Final +{int(shift)}h."

def fetch_environmental_load(lat=38.9847, lon=-77.0947, api_key=""):
    """Fetches real-time weather data to assess environmental metabolic stress."""
    if not api_key:
        return 1.0, "☁️ WEATHER OFFLINE"

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        temp_c = data.get("main", {}).get("temp", 20)
        weather_id = data.get("weather", [{}])[0].get("id", 800)
        
        multiplier = 1.0
        status_tags = []
        
        if temp_c > 32:
            multiplier -= 0.15
            status_tags.append("🔥 HEAT WARNING (Rapid Absorption Risk)")
        elif temp_c < 0:
            multiplier += 0.15
            status_tags.append("❄️ EXTREME COLD (High Resistance Risk)")
            
        if 200 <= weather_id <= 299:
            multiplier += 0.10
            status_tags.append("⛈️ SEVERE WEATHER")
            
        final_status = " | ".join(status_tags) if status_tags else "☁️ BENIGN ENVIRONMENT"
        return multiplier, final_status
        
    except requests.exceptions.RequestException as e:
        return 1.0, "☁️ WEATHER SYNC UNAVAILABLE"

# -----------------------------------------------------------------------------
# 4. THE UNIFIED ERM ENGINE
# -----------------------------------------------------------------------------
def calc_glycemic_risk(df, context, whoop_data=None, meeting_count=0, speaker_mode=False, owm_api_key="", is_real_data=False):
    # Only apply chaos simulators if the data isn't a live feed
    if not is_real_data:
        df = apply_context_modifiers(df, context)
        
    latest_glucose = df['Glucose_Value'].iloc[-1]
    latest_trend = df['Trend'].iloc[-1]
    
    whoop_multiplier, whoop_status = get_whoop_risk_modifier(whoop_data)
    sched_multiplier, sched_status = calculate_schedule_load(meeting_count)
    env_multiplier, env_status = fetch_environmental_load(api_key=owm_api_key)
    
    final_reason = f"{whoop_status} | {sched_status} | {env_status}"
    
    low_threshold = 85 if env_multiplier < 1.0 else 70
    high_threshold = 150 if speaker_mode else 180

    if latest_glucose > high_threshold:
        return df, "🔴 HIGH ALERT", "#ED8796", f"Hyperglycemic risk detected. ({final_reason})"
    elif latest_glucose < low_threshold:
        return df, "🔴 LOW ALERT", "#ED8796", f"Hypoglycemic risk detected. ({final_reason})"

    if env_multiplier > 1.0 and (whoop_multiplier + env_multiplier - 1.0) >= 1.5:
        return df, "🔴 CAUTION", "#EED49F", f"Compounded Strain Detected! {final_reason}"

    if context == "Travel":
        return df, "✈️ TRAVELING", "#8B5CF6", f"{generate_travel_advisory()} ({final_reason})"

    return df, "🟢 STABLE", "#A6DA95", f"{final_reason} | System nominal."