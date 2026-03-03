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
    start_time = end_time - timedelta(hours=24)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='5min')
    
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
    
    return df

def apply_context_modifiers(df, context):
    """
    Takes the perfect sine wave and ruins it with 'Real Life'.
    """
    # Create a noise generator
    np.random.seed(42) # Seed for consistency in demo, remove for true chaos
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
    last_val = df['Glucose_Value'].iloc[-1]
    prev_val = df['Glucose_Value'].iloc[-2]
    delta = last_val - prev_val
    
    if delta > 3: df['Trend'] = "Rising Fast ⬆️"
    elif delta > 1: df['Trend'] = "Rising ↗️"
    elif delta < -3: df['Trend'] = "Falling Fast ⬇️"
    elif delta < -1: df['Trend'] = "Falling ↘️"
    else: df['Trend'] = "Stable ➡️"

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

def calc_glycemic_risk(df, context):
    """
    The ERM Engine. Calculates Risk Score based on Chaos Data.
    """
    # Apply the chaos modifiers FIRST, so the risk calc sees the 'Real' data
    df = apply_context_modifiers(df, context)
    
    latest_glucose = df['Glucose_Value'].iloc[-1]
    
    # 1. BASELINE GATES
    if latest_glucose > 180:
        return df, "🔴 HIGH RISK", "Hyperglycemic event detected."
    elif latest_glucose < 70:
        return df, "🔴 CRITICAL", "Hypoglycemic event imminent."
        
    # 2. CONTEXT GATES (The AI Value Add)
    if context == "Exercise" and latest_glucose < 100:
        return df, "🟡 CAUTION", "Glucose dropping during exertion. Carb load recommended."
        
    if context == "Stressed" and latest_glucose > 150:
        return df, "🟡 ELEVATED", "Cortisol-induced resistance likely. Monitor trend."
        
    if context == "Sick":
        return df, "🟠 MONITORING", "Illness protocol active. Basal increase may be required."

    return df, "🟢 NOMINAL", "System within normal operating parameters."