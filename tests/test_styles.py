import sys
from unittest.mock import MagicMock
import os

# Mock dependencies before importing styles
sys.modules["streamlit"] = MagicMock()
sys.modules["plotly"] = MagicMock()
sys.modules["plotly.graph_objects"] = MagicMock()

# Add root directory to path to allow importing styles
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from styles import render_market_card

def test_render_market_card_positive_delta():
    """Test market card rendering with positive price change."""
    name = "AAPL"
    price = 150.00
    delta = 5.00
    pct = 3.45

    html = render_market_card(name, price, delta, pct)

    # Check content
    assert name in html
    assert "150.00" in html
    assert "+5.00" in html
    assert "+3.45%" in html

    # Check styling for positive delta
    assert "var(--delta-up)" in html
    assert "var(--delta-down)" not in html

    # Check accessibility label
    assert 'aria-label="AAPL: 150.00, up 5.00 (+3.45%)"' in html

def test_render_market_card_negative_delta():
    """Test market card rendering with negative price change."""
    name = "GOOG"
    price = 2800.50
    delta = -12.30
    pct = -0.44

    html = render_market_card(name, price, delta, pct)

    # Check content
    assert name in html
    assert "2,800.50" in html # Check comma formatting for price
    assert "-12.30" in html
    assert "-0.44%" in html

    # Check styling for negative delta
    assert "var(--delta-down)" in html
    assert "var(--delta-up)" not in html

    # Check accessibility label
    assert 'aria-label="GOOG: 2,800.50, down 12.30 (-0.44%)"' in html

def test_render_market_card_zero_delta():
    """Test market card rendering with zero price change."""
    name = "STABLE"
    price = 100.00
    delta = 0.00
    pct = 0.00

    html = render_market_card(name, price, delta, pct)

    # Check content
    assert name in html
    assert "100.00" in html
    assert "+0.00" in html
    assert "+0.00%" in html

    # Check styling for zero delta (defaults to up/green)
    assert "var(--delta-up)" in html

    # Check accessibility label
    assert 'aria-label="STABLE: 100.00, up 0.00 (+0.00%)"' in html

def test_render_market_card_formatting():
    """Test number formatting in market card."""
    name = "BIG"
    price = 1234567.89
    delta = 1000.50
    pct = 0.08

    html = render_market_card(name, price, delta, pct)

    # Check price comma formatting
    assert "1,234,567.89" in html

    # Check delta formatting (no comma based on current implementation)
    assert "+1000.50" in html
    assert "+0.08%" in html
