import sys
import os
import pandas as pd
import numpy as np

# Add parent directory to path to import logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic import calculate_schedule_load

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
        assert "🟢 LIGHT LOAD: Schedule is clear" in message

def test_calculate_schedule_load_negative():
    # Edge case: negative meetings (should fall under light load)
    for count in [-1, -5]:
        multiplier, message = calculate_schedule_load(count)
        assert multiplier == 1.0
        assert "🟢 LIGHT LOAD: Schedule is clear" in message
