import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

def fetch_health_data():
    """
    Simulates fetching 24 hours of Dexcom/Whoop data.
    In MVP, this generates a base sine wave (Dexcom Sandbox style)
    and then injects 'Life Chaos' based on the user's context.
    """
    # 1. Create Time Index (Last 24 hours, 5-min intervals)
    end_time = datetime.now()
    # If we generate 288 points at 5-minute intervals starting from start_time,
    # the last point will be at start_time + 287 * 5 mins.
    # We want the last point to be exactly end_time, so start_time should be:
    start_time = end_time - timedelta(minutes=5 * 287)
    # Generate 288 points exactly
    timestamps = [start_time + timedelta(minutes=5 * i) for i in range(288)]
    
    # 2. Generate Base "Perfect" Sine Wave (The Dexcom Sandbox Artifact)
    # A smooth curve oscillating between 100 and 160
    base_glucose = 130 + 30 * np.sin(np.linspace(0, 4 * np.pi, len(timestamps)))
    
    df = pd.DataFrame({
        'Timestamp': timestamps,
        'Glucose_Value': base_glucose,
        'Trend': 'Flat' # Placeholder
    })
    
    # 3. INJECT BIOLOGICAL CHAOS (The "Real Life" Simulator)
    # We grab the context from Streamlit Session State if it exists
    context = "Normal"
    # This is a hack to read the sidebar widget value from logic.py
    # In a real app, pass context as an argument.
    # For MVP speed, we assume 'Normal' if not found.
    
    # Tests expect `fetch_health_data()` to return chaotic data directly.
    # We'll apply the default 'Normal' modifiers so trends and noise are included.
    df = apply_context_modifiers(df, context)

    return df

def apply_context_modifiers(df, context):
    """
    Takes the perfect sine wave and ruins it with 'Real Life'.
    """
    # Create a noise generator
    # We do NOT seed np.random here to allow for non-deterministic results between calls,
    # satisfying `test_get_mock_cgm_deterministic`.
    noise = np.random.normal(0, 3, len(df)) # Standard background noise (±3 mg/dL)
    
    # MODIFIER: CORTISOL (Stress/Sick) -> Raises baseline & variance
    if context == "Stressed":
        drift = np.linspace(0, 40, len(df)) # Gradual rise of +40 mg/dL over 24h
        stress_noise = np.random.normal(0, 8, len(df)) # High variance
        df['Glucose_Value'] = df['Glucose_Value'] + drift + stress_noise
        
    elif context == "Sick":
        baseline_shift = 50 # Immediate +50 mg/dL jump
        fever_spikes = np.random.normal(0, 12, len(df)) # Extreme variance
        df['Glucose_Value'] = df['Glucose_Value'] + baseline_shift + fever_spikes

    # MODIFIER: ADRENALINE / UPTAKE (Exercise) -> Drops baseline
    elif context == "Exercise":
        # Simulate a crash in the last 2 hours
        crash_curve = np.zeros(len(df))
        crash_curve[-24:] = np.linspace(0, -60, 24) # Drop 60 mg/dL in last 2 hours
        df['Glucose_Value'] = df['Glucose_Value'] + crash_curve + noise

    # MODIFIER: TRAVEL -> Irregular meal spikes
    elif context == "Travel":
        # Add random meal spikes
        spikes = np.zeros(len(df))
        indices = np.random.choice(range(len(df)), size=3, replace=False)
        for idx in indices:
            # Create a localized spike (Gaussian) around this index
            x = np.arange(len(df))
            spikes += 60 * np.exp(-0.5 * ((x - idx) / 6)**2) 
        df['Glucose_Value'] = df['Glucose_Value'] + spikes + noise
        
    else:
        # Normal -> Just add basic biological noise
        df['Glucose_Value'] = df['Glucose_Value'] + noise

    # Recalculate Trend based on the new chaotic end-values
    diffs = df['Glucose_Value'].diff().fillna(0)
    df['Trend'] = np.where(diffs > 3, "Rising", np.where(diffs < -3, "Falling", "Steady"))

    # Restrict generated mock glucose values between 65 and 220 using np.clip
    df['Glucose_Value'] = np.clip(df['Glucose_Value'], 65, 220)

    return df

# ---------------------------------------------------------
# WRAPPER TO COMBINE FETCH & MODIFY
# ---------------------------------------------------------
# This is what app.py actually calls. 
# We had to split it to get the 'context' variable passed in properly.
# But since app.py calls `fetch_health_data()` without args in your current code,
# let's adapt app.py slightly or handle it here.
#
# BETTER APPROACH FOR MVP:
# We will modify `fetch_health_data` to just return the base, 
# and let app.py call the modifier.
# ---------------------------------------------------------

def calc_glycemic_risk(df, context, whoop_data=None):
    """
    The ERM Engine. Calculates Risk Score based on Chaos Data and real-time biometrics.
    """
    # Apply the chaos modifiers FIRST, so the risk calc sees the 'Real' data
    df = apply_context_modifiers(df, context)
    
    latest_glucose = df['Glucose_Value'].iloc[-1]
    latest_trend = df['Trend'].iloc[-1]
    
    # 1. BASELINE GATES (Safety First)
    if latest_glucose > 180:
        if latest_trend == "Falling":
            return df, "🟡 MONITORING", "#EED49F", "Blood sugar is high but falling. Monitoring to prevent insulin stacking."
        else:
            return df, "🔴 NEEDS ATTENTION", "#ED8796", "Blood sugar is high."
    elif latest_glucose < 70:
        return df, "🔴 NEEDS ATTENTION", "#ED8796", "Blood sugar is low."

    # 2. WHOOP BIOMETRIC ANALYSIS (Leading Indicators)
    whoop_status = ""
    whoop_modifier = 1.0
    
    if whoop_data:
        # Extract the recovery score from the Whoop API response object
        # Note: The Whoop API returns recovery_score as an integer 0-100
        score = whoop_data.get('score', {}).get('recovery_score', 100)
        whoop_modifier, whoop_status = get_whoop_risk_modifier(score)
        
    # 3. CONTEXT GATES (The AI Value Add)
    # If Whoop is in the Red, we escalate "Normal" or "Stressed" states to Caution
    if whoop_modifier >= 1.4:
        return df, "🔴 CAUTION", "#ED8796", f"{whoop_status} High physiological risk detected."

    if context == "Exercise" and latest_glucose < 100:
        return df, "🟡 CAUTION", "#EED49F", "Blood sugar dropping. Consider a snack."
        
    if context == "Stressed" and latest_glucose > 150:
        return df, "🟡 ELEVATED", "#EED49F", "Stress may be affecting blood sugar. Keep an eye on it."
        
    if context == "Sick":
        return df, "🟠 MONITORING", "#F5A97F", "Illness may affect physiological baseline."

    # 4. FINAL RESILIENCE CHECK
    # Even if glucose is "Normal", if Whoop is Yellow, we provide a proactive heads-up
    if whoop_modifier > 1.0:
         return df, "🟡 MONITORING", "#EED49F", f"{whoop_status} Baseline resilience is lowered."

    return df, "🟢 STABLE", "#A6DA95", f"{whoop_status} Everything looks good."

def get_whoop_risk_modifier(recovery_score):
    """
    Translates Whoop Recovery (0-100) into an ERM Risk Modifier.
    RED (0-33): Severe strain/Reduced sensitivity.
    YELLOW (34-66): Moderate strain/Baseline noise.
    GREEN (67-100): High resilience.
    """
    if recovery_score < 34:
        return 1.5, "WHOOP: RED RECOVERY."
    elif recovery_score < 67:
        return 1.2, "WHOOP: YELLOW RECOVERY."
    else:
        return 1.0, "WHOOP: GREEN RECOVERY."