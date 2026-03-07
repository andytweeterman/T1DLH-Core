import pytest
from logic import calculate_schedule_load

def test_calculate_schedule_load_high():
    # Test boundary condition 7
    multiplier, status = calculate_schedule_load(7)
    assert multiplier == 1.3
    assert "🔴 HIGH LOAD" in status

    # Test greater than 7
    multiplier, status = calculate_schedule_load(10)
    assert multiplier == 1.3
    assert "🔴 HIGH LOAD" in status

def test_calculate_schedule_load_elevated():
    # Test boundary condition 4
    multiplier, status = calculate_schedule_load(4)
    assert multiplier == 1.15
    assert "🟡 ELEVATED LOAD" in status

    # Test between 4 and 7
    multiplier, status = calculate_schedule_load(5)
    assert multiplier == 1.15
    assert "🟡 ELEVATED LOAD" in status

def test_calculate_schedule_load_light():
    # Test just below 4
    multiplier, status = calculate_schedule_load(3)
    assert multiplier == 1.0
    assert "🟢 LIGHT LOAD" in status

    # Test 0
    multiplier, status = calculate_schedule_load(0)
    assert multiplier == 1.0
    assert "🟢 LIGHT LOAD" in status
