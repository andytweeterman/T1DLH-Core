import pytest
from logic import calculate_schedule_load

def test_calculate_schedule_load_high():
    # Test boundary condition
    multiplier, message = calculate_schedule_load(7)
    assert multiplier == 1.3
    assert message == "🔴 HIGH LOAD: Schedule density is critical. Expect cortisol-driven resistance."

    # Test > 7
    multiplier, message = calculate_schedule_load(10)
    assert multiplier == 1.3
    assert message == "🔴 HIGH LOAD: Schedule density is critical. Expect cortisol-driven resistance."

def test_calculate_schedule_load_elevated():
    # Test boundary condition
    multiplier, message = calculate_schedule_load(4)
    assert multiplier == 1.15
    assert message == "🟡 ELEVATED LOAD: Moderate schedule density. Monitor baseline."

    # Test between 4 and 7
    multiplier, message = calculate_schedule_load(6)
    assert multiplier == 1.15
    assert message == "🟡 ELEVATED LOAD: Moderate schedule density. Monitor baseline."

def test_calculate_schedule_load_light():
    # Test boundary condition
    multiplier, message = calculate_schedule_load(3)
    assert multiplier == 1.0
    assert message == "🟢 LIGHT LOAD: Schedule is clear."

    # Test < 4
    multiplier, message = calculate_schedule_load(0)
    assert multiplier == 1.0
    assert message == "🟢 LIGHT LOAD: Schedule is clear."
