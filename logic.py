import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. BIOMETRIC SIMULATOR
# -----------------------------------------------------------------------------
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

def get_whoop_risk_modifier(recovery_score):
    """Translates Whoop Recovery into a physiological risk score."""
    if recovery_score < 34:
        return 1.5, "WHOOP: RED RECOVERY."
    elif recovery_score < 67:
        return 1.2, "WHOOP: YELLOW RECOVERY."
    return 1.0, "WHOOP: GREEN RECOVERY."

def is_weekend_window():
    """Checks if the current time falls between Fri 5PM and Mon 8AM."""
    now = datetime.now()
    weekday = now.weekday() # 4=Fri, 5=Sat, 6=Sun, 0=Mon
    hour = now.hour
    
    if weekday == 4 and hour >= 17: return True # Friday after 5PM
    if weekday in [5, 6]: return True           # All day Sat/Sun
    if weekday == 0 and hour < 8: return True   # Monday before 8AM
    return False

def generate_travel_advisory(offset_hours=6):
    """
    Generates a phased pump time-shift protocol to prevent basal stacking.
    Defaults to a +6 hour shift.
    """
    shift = offset_hours / 3
    return (
        f"✈️ TRAVEL PROTOCOL (+{offset_hours}h Shift): "
        f"1️⃣ Today: Shift pump +{int(shift)}h. "
        f"2️⃣ Tomorrow: Shift +{int(shift)}h. "
        f"3️⃣ Day 3: Final +{int(shift)}h shift to local time. "
        "🛡️ Low gates raised to 100 mg/dL for walking."
    )
# -----------------------------------------------------------------------------
# 3. THE UNIFIED ERM ENGINE
# -----------------------------------------------------------------------------
def calc_glycemic_risk(df, context, whoop_data=None, meeting_count=0, speaker_mode=False):
    """Correlates all data streams to provide a unified Risk Status."""
    # Apply latest user-selected context
    df = apply_context_modifiers(df, context)
    
    latest_glucose = df['Glucose_Value'].iloc[-1]
    latest_trend = df['Trend'].iloc[-1]
    
    # Process Secondary Streams
    whoop_modifier, whoop_status = 1.0, ""
    if whoop_data:
        score = whoop_data.get('score', {}).get('recovery_score', 100)
        whoop_modifier, whoop_status = get_whoop_risk_modifier(score)
    
    sched_modifier, sched_status = calculate_schedule_load(meeting_count)
    weekend_active = is_weekend_window()

    # A. Safety First: Thresholds & Jules Guardrails
    high_threshold = 150 if speaker_mode else 180
    
    if latest_glucose > high_threshold:
        if speaker_mode:
            return df, "🔴 SPEAKER ALERT", "#ED8796", "High-stakes event detected. Sensitivity increased."
        if latest_trend == "Falling":
            return df, "🟡 MONITORING", "#EED49F", "Glucose high but falling. Preventing stacking."
        return df, "🔴 NEEDS ATTENTION", "#ED8796", "Blood sugar is high."
    elif latest_glucose < 70:
        return df, "🔴 NEEDS ATTENTION", "#ED8796", "Blood sugar is low."

    # B. Contextual Escalation (Biometric + Schedule Alignment)
    if whoop_modifier >= 1.5:
        return df, "🔴 CAUTION", "#ED8796", f"{whoop_status} High physiological strain."
        
    # Ignore schedule density alerts if Weekend Mode is active
    if not weekend_active and sched_modifier > 1.2:
        return df, "🟡 LOAD ALERT", "#EED49F", f"{sched_status}"

# C. Standard Contextual analysis
    if context == "Travel":
        advisory = generate_travel_advisory(offset_hours=6)
        
        # 1. Jetlag Cortisol Check (Tightened High Threshold)
        if latest_glucose > 160:
            return df, "🟡 JETLAG ALERT", "#EED49F", f"{advisory} | High glucose detected. Likely travel stress/cortisol."
        
        # 2. Touring/Walking Check (Raised Low Threshold to 100)
        elif latest_glucose < 100:
            if latest_trend == "Falling":
                return df, "🔴 TOUR LOW", "#ED8796", f"{advisory} | Active drop during travel. Treat immediately."
            return df, "🟡 CAUTION", "#EED49F", f"{advisory} | Glucose dipping. Grab a snack."
            
        # 3. Stable Travel State
        return df, "🟢 TRAVELING", "#A6DA95", advisory

    if context == "Project" and latest_glucose < 110:
        if latest_trend == "Falling":
            return df, "🟡 CAUTION", "#EED49F", "Sustained labor dropping glucose. Carb up."

    if context == "Exercise" and latest_glucose < 100:
        return df, "🟡 CAUTION", "#EED49F", "Glucose dropping during activity."
        
    if context == "Stressed" and latest_glucose > 150:
        return df, "🟡 ELEVATED", "#EED49F", "Stress affecting glycemic baseline."
        
    if context == "Sick":
        return df, "🟠 MONITORING", "#F5A97F", "Baseline instability due to illness."

    # D. Recovery Debt
    if whoop_modifier > 1.0:
         return df, "🟡 MONITORING", "#EED49F", f"{whoop_status} Lowered resilience."

    # E. Final Output with Weekend Indicator
    final_reason = f"{whoop_status} System nominal."
    if weekend_active:
        final_reason = f"🌴 WEEKEND MODE ACTIVE | {final_reason}"

    return df, "🟢 STABLE", "#A6DA95", final_reason