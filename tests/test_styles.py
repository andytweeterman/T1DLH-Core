import pytest
import sys
import os
from unittest.mock import patch

# Mock streamlit before importing styles
sys.modules['streamlit'] = type('MockStreamlit', (), {'markdown': lambda *args, **kwargs: None, 'error': lambda *args, **kwargs: None})

# Add parent directory to path to import styles
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from styles import get_driver_pill_html

def test_get_driver_pill_html_red_bg():
    # Test all variations that trigger red
    for t in ["🔴 ALERT", "🔥 FIRE", "❄️ COLD", "🤒 SICK"]:
        html = get_driver_pill_html(t)
        assert "#FFD1D9" in html
        assert "#8A001A" in html
        assert "#FFB3C1" in html

def test_get_driver_pill_html_yellow_bg():
    # Test all variations that trigger yellow
    for t in ["🟡 WARNING", "⚡ LIGHTNING", "💤 SLEEP", "🧘‍♂️ YOGA", "🏃‍♂️ RUN"]:
        html = get_driver_pill_html(t)
        assert "#FFEDB3" in html
        assert "#805500" in html
        assert "#FFDF80" in html

def test_get_driver_pill_html_blue_bg():
    # Test all variations that trigger blue
    for t in ["🔋 BATTERY", "something RECOVERY something", "RESTORE MODE"]:
        html = get_driver_pill_html(t)
        assert "#C2E0FF" in html
        assert "#004085" in html
        assert "#99CCFF" in html

    # Also test case insensitivity for RECOVERY and RESTORE
    assert "#C2E0FF" in get_driver_pill_html("recovery mode")
    assert "#C2E0FF" in get_driver_pill_html("restore mode")

def test_get_driver_pill_html_green_bg():
    # Test all variations that trigger green
    for t in ["🟢 GOOD", "☁️ CLOUD"]:
        html = get_driver_pill_html(t)
        assert "#D1F4D9" in html
        assert "#00591A" in html
        assert "#A3E9B3" in html

def test_get_driver_pill_html_default_bg():
    # Test default case
    html = get_driver_pill_html("UNKNOWN STATE")
    assert "#E1D4FA" in html
    assert "#330099" in html
    assert "#C4B5F5" in html

def test_get_driver_pill_html_replacements():
    # BENIGN ENVIRONMENT -> CLEAR WEATHER -> Clear Weather
    assert "Clear Weather" in get_driver_pill_html("BENIGN ENVIRONMENT")

    # LOAD -> CALENDAR LOAD -> Calendar Load
    assert "Calendar Load" in get_driver_pill_html("HEAVY LOAD")

    # NOMINAL -> BIOMETRICS NOMINAL -> Biometrics Nominal
    assert "Biometrics Nominal" in get_driver_pill_html("ALL NOMINAL")

def test_get_driver_pill_html_formatting_cleanup():
    # 12H -> 12h
    assert "12h" in get_driver_pill_html("12H")

    # Bg -> BG (after title casing "bg" becomes "Bg", then replaced with "BG")
    assert "BG" in get_driver_pill_html("My bg Is Good")

    # Mode -> MODE (after title casing "mode" becomes "Mode", then replaced with "MODE")
    assert "MODE" in get_driver_pill_html("Test mode")

    # Regex \d+H -> \1h
    assert "10h" in get_driver_pill_html("Wait 10H")
    assert "24h" in get_driver_pill_html("24H")

    # Regex \d+M -> \1m
    assert "5m" in get_driver_pill_html("Wait 5M")
    assert "45m" in get_driver_pill_html("45M")

    # Left) -> left)
    assert " left)" in get_driver_pill_html("(5M Left)")

def test_get_driver_pill_html_title_casing():
    # It should apply .title()
    html = get_driver_pill_html("hello world")
    assert "Hello World" in html
