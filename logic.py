import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from streamlit import cache_data

# -----------------------------------------------------------------------------
# 1. BIOMETRIC SIMULATOR
# -----------------------------------------------------------------------------
@cache_data(ttl=300) # Cache simulation for 5 minutes
def fetch_health_data():
    """Simulates 24 hours of Dexcom/Whoop data."""
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=5 * 287)
    timestamps = [start_time + timedelta(minutes=5 * i) for i in range(288)]
    
    # Base Sine Wave (130 mg/dL center)
    base_glucose = 130 + 30 * np.sin(np.linspace(0, 4 * np.pi, len(timestamps)))
    
    df = pd.DataFrame({
        'Timestamp': timestamps,
        'Glucose_Value': base_glucose,
        'Trend': 'Flat' 
    })
    
    # We apply the default 'Normal' biological noise here
    return apply_context_modifiers(df, "Normal")

def apply_context_modifiers(df, context):
    """Injects real-life chaos into the base telemetry."""
    noise = np.random.normal(0, 3, len(df)) 
    
    if context == "Stressed":
        drift = np.linspace(0, 40, len(df)) 
        df['Glucose_Value'] = df['Glucose_Value'] + drift + np.random.normal(0, 8, len(df))
    elif context == "Sick":
        df['Glucose_Value'] = df['Glucose_Value'] + 50 + np.random.normal(0, 12, len(df))
    elif context == "Exercise":
        crash = np.zeros(len(df))
        crash[-24:] = np.linspace(0, -60, 24) 
        df['Glucose_Value'] = df['Glucose_Value'] + crash + noise
    elif context == "Project":
        # Sustained, slow drain on glucose over hours of manual labor
        drain = np.linspace(0, -40, len(df))
        df['Glucose_Value'] = df['Glucose_Value'] + drain + noise
    elif context == "Travel":
        spikes = np.zeros(len(df))
        indices = np.random.choice(range(len(df)), size=3, replace=False)
        for idx in indices:
            x = np.arange(len(df))
            spikes += 60 * np.exp(-0.5 * ((x - idx) / 6)**2) 
        df['Glucose_Value'] = df['Glucose_Value'] + spikes + noise
    else:
        df['Glucose_Value'] = df['Glucose_Value'] + noise

    # Recalculate Trend Velocity
    diffs = df['Glucose_Value'].diff().fillna(0)
    df['Trend'] = np.where(diffs > 3, "Rising", np.where(diffs < -3, "Falling", "Steady"))
    df['Glucose_Value'] = np.clip(df['Glucose_Value'], 65, 220)
    return df

# -----------------------------------------------------------------------------
# 2. RISK ANALYSIS HELPERS
# -----------------------------------------------------------------------------
def calculate_schedule_load(meeting_count):
    """Translates calendar density into an ERM risk multiplier."""
    if meeting_count >= 7:
        return 1.3, "🔴 HIGH LOAD: Schedule density is critical."
    elif meeting_count >= 4:
        return 1.15, "🟡 ELEVATED LOAD: Moderate schedule density."
    return 1.0, "🟢 LIGHT LOAD: Schedule is clear."

def get_whoop_risk_modifier(whoop_metrics):
    """
    Translates Whoop Recovery, Strain, and Sleep into physiological risk vectors.
    Returns (multiplier, status_string)
    """
    if not whoop_metrics:
        return 1.0, "No Sync"

    # Extract the deep metrics safely from the V2 dictionary
    score_obj = whoop_metrics.get('score', {})
    recovery = score_obj.get('recovery_score', 100)
    strain = score_obj.get('day_strain', 0.0)
    sleep_perf = score_obj.get('sleep_performance_percentage', 100)

    multiplier = 1.0
    status_tags = []

    # 1. Recovery Gates (Systemic Readiness)
    if recovery < 34:
        multiplier += 0.3
        status_tags.append("🔴 RED RECOVERY")
    elif recovery < 67:
        multiplier += 0.1
        status_tags.append("🟡 YELLOW RECOVERY")

    # 2. Sleep Performance (Insulin Resistance Vector)
    if sleep_perf < 70:
        multiplier += 0.2
        status_tags.append("💤 SLEEP DEBT")

    # 3. Day Strain (Insulin Sensitivity Vector)
    if strain > 14.0:
        multiplier -= 0.25 
        status_tags.append("⚡ HIGH STRAIN")

    final_status = " | ".join(status_tags) if status_tags else "🟢 FULLY CHARGED"
    return multiplier, final_status

def is_weekend_window():
    """Checks if the current time falls between Fri 5PM and Mon 8AM."""
    now = datetime.now()
    weekday = now.weekday() # 4=Fri, 5=Sat, 6=Sun, 0=Mon
    hour = now.hour
    
    if weekday == 4 and hour >= 17: return True 
    if weekday in [5, 6]: return True 
    if weekday == 0 and hour < 8: return True 
    return False

def generate_travel_advisory(offset_hours=6):
    """Generates phased pump protocol for time-zone transitions."""
    shift = offset_hours / 3
    return (
        f"✈️ TRAVEL PROTOCOL (+{offset_hours}h Shift): "
        f"1️⃣ Today: Shift pump +{int(shift)}h. "
        f"2️⃣ Tomorrow: Shift +{int(shift)}h. "
        f"3️⃣ Day 3: Final +{int(shift)}h. "
        "🛡️ Low gates raised to 100 mg/dL."
    )

# -----------------------------------------------------------------------------
# 3. THE UNIFIED ERM ENGINE
# -----------------------------------------------------------------------------
@cache_data(ttl=60) # Cache risk state for 1 minute
def calc_glycemic_risk(df, context, whoop_data=None, meeting_count=0, speaker_mode=False):
    """Correlates all data streams to provide a unified Risk Status."""
    df = apply_context_modifiers(df, context)
    
    latest_glucose = df['Glucose_Value'].iloc[-1]
    latest_trend = df['Trend'].iloc[-1]
    
    whoop_modifier, whoop_status = get_whoop_risk_modifier(whoop_data)
    sched_modifier, sched_status = calculate_schedule_load(meeting_count)
    weekend_active = is_weekend_window()

    # A. Safety Thresholds
    high_threshold = 150 if speaker_mode else 180
    
    if latest_glucose > high_threshold:
        if speaker_mode:
            return df, "🔴 SPEAKER ALERT", "#ED8796", "High-stakes event detected. Sensitivity increased."
        if latest_trend == "Falling":
            return df, "🟡 MONITORING", "#EED49F", "Glucose high but falling. Preventing stacking."
        return df, "🔴 NEEDS ATTENTION", "#ED8796", "Blood sugar is high."
    elif latest_glucose < 70:
        return df, "🔴 NEEDS ATTENTION", "#ED8796", "Blood sugar is low."

    # B. Contextual Escalation
    if whoop_modifier >= 1.5:
        return df, "🔴 CAUTION", "#ED8796", f"{whoop_status} High physiological strain."
        
    if not weekend_active and sched_modifier > 1.2:
        return df, "🟡 LOAD ALERT", "#EED49F", f"{sched_status}"

    # C. Contextual analysis
    if context == "Travel":
        advisory = generate_travel_advisory(offset_hours=6)
        if latest_glucose > 160:
            return df, "🟡 JETLAG ALERT", "#EED49F", f"{advisory} | High cortisol likely."
        elif latest_glucose < 100:
            if latest_trend == "Falling":
                return df, "🔴 TOUR LOW", "#ED8796", f"{advisory} | Active drop. Treat now."
            return df, "🟡 CAUTION", "#EED49F", f"{advisory} | Glucose dipping."
        return df, "🟢 TRAVELING", "#A6DA95", advisory

    if context == "Project" and latest_glucose < 110:
        if latest_trend == "Falling":
            return df, "🟡 CAUTION", "#EED49F", "Sustained labor dropping glucose. Carb up."

    if context == "Exercise" and latest_glucose < 100:
        return df, "🟡 CAUTION", "#EED49F", "Glucose dropping during activity."
        
    if context == "Stressed" and latest_glucose > 150:
        return df, "🟡 ELEVATED", "#EED49F", "Stress affecting baseline."
        
    if context == "Sick":
        return df, "🟠 MONITORING", "#F5A97F", "Baseline instability due to illness."

    if whoop_modifier > 1.0:
         return df, "🟡 MONITORING", "#EED49F", f"{whoop_status} Lowered resilience."

    # Final Output
    final_reason = f"{whoop_status} System nominal."
    if weekend_active:
        final_reason = f"🌴 WEEKEND MODE ACTIVE | {final_reason}"

    return df, "🟢 STABLE", "#A6DA95", final_reason