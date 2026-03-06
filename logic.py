import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

def fetch_health_data():
    """
    Simulates fetching 24 hours of Dexcom/Whoop data.
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=5 * 287)
    timestamps = [start_time + timedelta(minutes=5 * i) for i in range(288)]
    
    base_glucose = 130 + 30 * np.sin(np.linspace(0, 4 * np.pi, len(timestamps)))
    
    df = pd.DataFrame({
        'Timestamp': timestamps,
        'Glucose_Value': base_glucose,
        'Trend': 'Flat' 
    })
    
    context = "Normal"
    df = apply_context_modifiers(df, context)

    return df

def apply_context_modifiers(df, context):
    """
    Takes the perfect sine wave and ruins it with 'Real Life'.
    """
    noise = np.random.normal(0, 3, len(df)) 
    
    if context == "Stressed":
        drift = np.linspace(0, 40, len(df)) 
        stress_noise = np.random.normal(0, 8, len(df)) 
        df['Glucose_Value'] = df['Glucose_Value'] + drift + stress_noise
        
    elif context == "Sick":
        baseline_shift = 50 
        fever_spikes = np.random.normal(0, 12, len(df)) 
        df['Glucose_Value'] = df['Glucose_Value'] + baseline_shift + fever_spikes

    elif context == "Exercise":
        crash_curve = np.zeros(len(df))
        crash_curve[-24:] = np.linspace(0, -60, 24) 
        df['Glucose_Value'] = df['Glucose_Value'] + crash_curve + noise

    elif context == "Travel":
        spikes = np.zeros(len(df))
        indices = np.random.choice(range(len(df)), size=3, replace=False)
        for idx in indices:
            x = np.arange(len(df))
            spikes += 60 * np.exp(-0.5 * ((x - idx) / 6)**2) 
        df['Glucose_Value'] = df['Glucose_Value'] + spikes + noise
        
    else:
        df['Glucose_Value'] = df['Glucose_Value'] + noise

    # Recalculate Trend based on the new chaotic end-values
    diffs = df['Glucose_Value'].diff().fillna(0)
    df['Trend'] = np.where(diffs > 3, "Rising", np.where(diffs < -3, "Falling", "Steady"))

    df['Glucose_Value'] = np.clip(df['Glucose_Value'], 65, 220)

    return df

# ---------------------------------------------------------
# RISK & CONTEXT ENGINES
# ---------------------------------------------------------

def calculate_schedule_load(meeting_count):
    """
    Translates calendar density into an ERM risk multiplier.
    """
    if meeting_count >= 7:
        return 1.3, "🔴 HIGH LOAD: Schedule density is critical. Expect cortisol-driven resistance."
    elif meeting_count >= 4:
        return 1.15, "🟡 ELEVATED LOAD: Moderate schedule density. Monitor baseline."
    return 1.0, "🟢 LIGHT LOAD: Schedule is clear."

def get_whoop_risk_modifier(recovery_score):
    """
    Translates Whoop Recovery (0-100) into an ERM Risk Modifier.
    """
    if recovery_score < 34:
        return 1.5, "🔴 RED RECOVERY."
    elif recovery_score < 67:
        return 1.2, "🟡 YELLOW RECOVERY."
    else:
        return 1.0, "🟢 GREEN RECOVERY."

def calc_glycemic_risk(df, context, whoop_data=None, meeting_count=0):
    """
    The ERM Engine. Calculates Risk Score based on Chaos Data, real-time biometrics, and schedule density.
    Includes Jules's physiological trend guardrails.
    """
    df = apply_context_modifiers(df, context)
    
    latest_glucose = df['Glucose_Value'].iloc[-1]
    latest_trend = df['Trend'].iloc[-1]
    
    # 1. BASELINE GATES (Safety First - Jules PR included)
    if latest_glucose > 180:
        if latest_trend == "Falling":
            return df, "🟡 MONITORING", "#EED49F", "Blood sugar is high but falling. Monitoring to prevent insulin stacking."
        else:
            return df, "🔴 NEEDS ATTENTION", "#ED879