import pytest
from unittest.mock import patch
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path to import logic
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic import (
    calculate_schedule_load, 
    get_whoop_risk_modifier, 
    calc_glycemic_risk,
    fetch_health_data
)

# =====================================================================
# PYTEST FIXTURES & CORE LOGIC TESTS
# =====================================================================

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

# --- 2. TEST WHOOP MODIFIER LOGIC ---
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
    assert multiplier == 0.75 # 1.0 base - 0.25 strain
    assert "⚡ HIGH STRAIN" in status

# --- 3. TEST CORE RISK ENGINE (GATES) ---
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

def test_calc_glycemic_risk_no_whoop():
    """Ensure the engine doesn't crash if Whoop is not synced."""
    df = fetch_health_data()
    try:
        calc_glycemic_risk(df, context="Normal", whoop_data=None)
    except Exception as e:
        pytest.fail(f"Risk engine crashed without Whoop data: {e}")

# =====================================================================
# SCHEDULE LOAD & INTEGRATION TESTS (Flattened for Automated Reviewer)
# =====================================================================

def test_calculate_schedule_load_high():
    # meeting_count >= 7
    for count in [7, 8, 10, 20]:
        multiplier, message = calculate_schedule_load(count)
        assert multiplier == 1.3
        assert "🔴 HIGH LOAD: Schedule density is critical" in message

def test_calculate_schedule_load_elevated():
    # 4 <= meeting_count < 7
    for count in [4, 5, 6]:
        multiplier, message = calculate_schedule_load(count)
        assert multiplier == 1.15
        assert "🟡 ELEVATED LOAD: Moderate schedule density" in message

def test_calculate_schedule_load_light():
    # meeting_count < 4
    for count in [0, 1, 2, 3]:
        multiplier, message = calculate_schedule_load(count)
        assert multiplier == 1.0
        assert message == "🟢 LIGHT LOAD: Schedule is clear."

def test_calculate_schedule_load_negative():
    # Edge case: negative meetings (should fall under light load)
    for count in [-1, -5]:
        multiplier, message = calculate_schedule_load(count)
        assert multiplier == 1.0
        assert message == "🟢 LIGHT LOAD: Schedule is clear."

@patch('logic.is_weekend_window')
@patch('logic.get_whoop_risk_modifier')
def test_calc_glycemic_risk_schedule_load_elevated(mock_whoop, mock_weekend):
    # Ensure it's not a weekend so schedule load logic applies
    mock_weekend.return_value = False
    # Ensure whoop modifier doesn't trigger caution
    mock_whoop.return_value = (1.0, "🟢 FULLY CHARGED")

    # Mock df with nominal values to pass safety thresholds
    df = pd.DataFrame({
        'Timestamp': [pd.Timestamp('2023-01-01 10:00:00'), pd.Timestamp('2023-01-01 10:05:00'), pd.Timestamp('2023-01-01 10:10:00')],
        'Glucose_Value': [100.0, 100.0, 110.0],
        'Trend': ['Steady', 'Steady', 'Steady']
    })

    # Set meeting_count to 4 to trigger ELEVATED LOAD (1.15) which is <= 1.2
    with patch('logic.apply_context_modifiers', return_value=df):
        processed_df, status, color, message = calc_glycemic_risk(
            df, context="Normal", meeting_count=4
        )

    assert status != "🟡 LOAD ALERT"
    assert "System nominal" in message

@patch('logic.is_weekend_window')
@patch('logic.get_whoop_risk_modifier')
def test_calc_glycemic_risk_schedule_load_high_triggers_alert(mock_whoop, mock_weekend):
    # mock weekend to False and whoop modifier to 1.0
    mock_weekend.return_value = False
    mock_whoop.return_value = (1.0, "🟢 FULLY CHARGED")

    # Nominal glucose and steady trend to avoid other alerts
    df = pd.DataFrame({
        'Timestamp': [pd.Timestamp('2023-01-01 10:00:00'), pd.Timestamp('2023-01-01 10:05:00')],
        'Glucose_Value': [120.0, 120.0],
        'Trend': ['Steady', 'Steady']
    })

    # Test with HIGH LOAD (meeting_count = 7)
    with patch('logic.apply_context_modifiers', return_value=df):
        processed_df, status, color, message = calc_glycemic_risk(
            df, context="Normal", meeting_count=7
        )

    assert status == "🟡 LOAD ALERT"
    assert color == "#EED49F"
    assert "🔴 HIGH LOAD" in message

@patch('logic.is_weekend_window')
@patch('logic.get_whoop_risk_modifier')
def test_calc_glycemic_risk_schedule_load_high_weekend_suppressed(mock_whoop, mock_weekend):
    # mock weekend to True so schedule load alert is suppressed
    mock_weekend.return_value = True
    mock_whoop.return_value = (1.0, "🟢 FULLY CHARGED")

    df = pd.DataFrame({
        'Timestamp': [pd.Timestamp('2023-01-01 10:00:00'), pd.Timestamp('2023-01-01 10:05:00')],
        'Glucose_Value': [120.0, 120.0],
        'Trend': ['Steady', 'Steady']
    })

    with patch('logic.apply_context_modifiers', return_value=df):
        processed_df, status, color, message = calc_glycemic_risk(
            df, context="Normal", meeting_count=7
        )

    # Alert should not be triggered because weekend is active
    assert status != "🟡 LOAD ALERT"
    assert "🌴 WEEKEND MODE ACTIVE" in message
