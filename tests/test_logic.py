import pytest
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to sys.path to resolve 'logic' and 'whoop' imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic import (
    calculate_schedule_load, 
    get_whoop_risk_modifier, 
    calc_glycemic_risk,
    fetch_health_data
)

# --- 1. TEST DATA GENERATION ---
def test_fetch_health_data_structure():
    """Verify the simulator returns the correct DataFrame shape and columns."""
    df = fetch_health_data()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 288  # 24 hours of 5-min data
    assert "Glucose_Value" in df.columns
    assert "Trend" in df.columns
    assert df["Glucose_Value"].min() >= 65
    assert df["Glucose_Value"].max() <= 220

# --- 2. TEST SCHEDULE LOAD LOGIC ---
@pytest.mark.parametrize("meetings, expected_mult, label", [
    (10, 1.3, "🔴 HIGH LOAD"),
    (5, 1.15, "🟡 ELEVATED LOAD"),
    (2, 1.0, "🟢 LIGHT LOAD"),
])
def test_schedule_load_calculation(meetings, expected_mult, label):
    multiplier, status = calculate_schedule_load(meetings)
    assert multiplier == expected_mult
    assert label in status

# --- 3. TEST WHOOP MODIFIER LOGIC ---
def test_whoop_modifier_red_recovery():
    """Test that a red recovery score increases the risk multiplier."""
    mock_whoop = {
        "score": {
            "recovery_score": 20, # Red
            "day_strain": 5.0,
            "sleep_performance_percentage": 90
        }
    }
    multiplier, status = get_whoop_risk_modifier(mock_whoop)
    assert multiplier == 1.3 # 1.0 base + 0.3 red recovery
    assert "🔴 RED RECOVERY" in status

def test_whoop_modifier_high_strain():
    """Test that high strain reduces the multiplier (increased insulin sensitivity)."""
    mock_whoop = {
        "score": {
            "recovery_score": 90,
            "day_strain": 18.0, # High strain
            "sleep_performance_percentage": 95
        }
    }
    multiplier, status = get_whoop_risk_modifier(mock_whoop)
    # 1.0 base - 0.25 strain
    assert multiplier == 0.75
    assert "⚡ HIGH STRAIN" in status

# --- 4. TEST CORE RISK ENGINE (GATES) ---
def test_calc_glycemic_risk_critical_low():
    """Verify that glucose < 70 always triggers NEEDS ATTENTION."""
    # Create mock data ending in a low value
    df = fetch_health_data()
    df.iloc[-1, df.columns.get_loc("Glucose_Value")] = 65
    
    _, status, color, _ = calc_glycemic_risk(df, context="Normal")
    assert status == "🔴 NEEDS ATTENTION"
    assert color == "#ED8796"

def test_calc_glycemic_risk_project_context():
    """Verify 'Project' context triggers caution at a higher threshold (110)."""
    df = fetch_health_data()
    
    # We set index -2 high and -1 lower to force a 'Falling' trend 
    # despite the internal recalculation in calc_glycemic_risk.
    # 145 - 40 = 105 (the target value below 110 gate).
    # 160 - 40 = 120. Diff = -15, which triggers Trend="Falling".
    df.iloc[-2, df.columns.get_loc("Glucose_Value")] = 160
    df.iloc[-1, df.columns.get_loc("Glucose_Value")] = 145
    
    _, status, color, reason = calc_glycemic_risk(df, context="Project")
    assert status == "🟡 CAUTION"
    assert "Sustained labor" in reason

def test_calc_glycemic_risk_speaker_mode():
    """Verify Speaker Mode tightens the high threshold to 150."""
    df = fetch_health_data()
    df.iloc[-1, df.columns.get_loc("Glucose_Value")] = 160
    
    # Normal mode would be STABLE/NOMINAL at 160
    _, status_normal, _, _ = calc_glycemic_risk(df, context="Normal", speaker_mode=False)
    # Speaker mode should be ALERT
    _, status_speaker, color, _ = calc_glycemic_risk(df, context="Normal", speaker_mode=True)
    
    assert status_speaker == "🔴 SPEAKER ALERT"
    assert color == "#ED8796"

# --- 5. TEST RESILIENCE TO MISSING DATA ---
def test_calc_glycemic_risk_no_whoop():
    """Ensure the engine doesn't crash if Whoop is not synced."""
    df = fetch_health_data()
    try:
        calc_glycemic_risk(df, context="Normal", whoop_data=None)
    except Exception as e:
        pytest.fail(f"Risk engine crashed without Whoop data: {e}")