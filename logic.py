def calc_glycemic_risk(df, context, whoop_data=None, meeting_count=0, speaker_mode=False):
    """
    The Unified ERM Engine. 
    Correlates Glucose, Whoop Recovery, Schedule Density, and Speaker Mode.
    """
    # 1. Apply environmental context (Stress/Exercise/etc)
    df = apply_context_modifiers(df, context)
    
    # Define variables from the dataframe
    latest_glucose = df['Glucose_Value'].iloc[-1]
    latest_trend = df['Trend'].iloc[-1]
    
    # 2. RUN SECONDARY MODIFIERS (Whoop & Schedule)
    whoop_modifier, whoop_status = 1.0, ""
    if whoop_data:
        score = whoop_data.get('score', {}).get('recovery_score', 100)
        whoop_modifier, whoop_status = get_whoop_risk_modifier(score)
    
    sched_modifier, sched_status = calculate_schedule_load(meeting_count)

    # 3. BASELINE GATES (Safety & Speaker Sensitivity)
    # Tighten the high threshold if in Speaker Mode
    high_threshold = 150 if speaker_mode else 180
    
    if latest_glucose > high_threshold:
        if speaker_mode:
            return df, "🔴 SPEAKER ALERT", "#ED8796", "High-stakes event detected. Sensitivity increased for cortisol monitoring."
        
        # Safety Trend Guardrail (Jules PR)
        if latest_trend == "Falling":
            return df, "🟡 MONITORING", "#EED49F", "Blood sugar is high but falling. Monitoring to prevent insulin stacking."
        return df, "🔴 NEEDS ATTENTION", "#ED8796", "Blood sugar is high."
            
    elif latest_glucose < 70:
        return df, "🔴 NEEDS ATTENTION", "#ED8796", "Blood sugar is low."

    # 4. AGENTIC CONTEXT GATES (The "Intelligence" Layer)
    # Escalate if multi-stream risks align (e.g. Red Recovery + Busy Schedule)
    if whoop_modifier >= 1.5:
        return df, "🔴 CAUTION", "#ED8796", f"{whoop_status} High physiological strain detected."
    
    if sched_modifier > 1.2:
        return df, "🟡 LOAD ALERT", "#EED49F", f"{sched_status}"

    if context == "Exercise" and latest_glucose < 100:
        return df, "🟡 CAUTION", "#EED49F", "Blood sugar dropping. Consider a snack."
        
    if context == "Stressed" and latest_glucose > 150:
        return df, "🟡 ELEVATED", "#EED49F", "Stress may be affecting blood sugar."
        
    if context == "Sick":
        return df, "🟠 MONITORING", "#F5A97F", "Illness may affect physiological baseline."

    # 5. RESILIENCE CHECK
    if whoop_modifier > 1.0:
         return df, "🟡 MONITORING", "#EED49F", f"{whoop_status} Baseline resilience is lowered."

    return df, "🟢 STABLE", "#A6DA95", f"{whoop_status} Everything looks good."