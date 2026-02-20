import streamlit as st
import plotly.graph_objects as go
import os
import base64
from css import get_main_css

def get_base64_image(image_path):
    try:
        # Enforce path security
        base_dir = os.path.dirname(os.path.abspath(__file__))
        requested_path = os.path.abspath(os.path.join(base_dir, image_path))
        if not requested_path.startswith(base_dir):
            return None

        if not os.path.exists(requested_path):
            return None

        with open(requested_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return None

def apply_theme():
    # Ensure session state is initialized
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = False

    # Define Theme Palettes
    if st.session_state["dark_mode"]:
        theme = {
            "BG_COLOR": "#0e1117",
            "CARD_BG": "rgba(22, 27, 34, 0.7)",
            "TEXT_PRIMARY": "#FFFFFF",
            "TEXT_SECONDARY": "#E0E0E0",
            "CHART_TEMPLATE": "plotly_dark",
            "CHART_FONT": "#E6E6E6",
            "ACCENT_GOLD": "#C6A87C",
            "DELTA_UP": "#00d26a",
            "DELTA_DOWN": "#f93e3e"
        }
    else:
        theme = {
            "BG_COLOR": "#ffffff",
            "CARD_BG": "rgba(255, 255, 255, 0.9)",
            "TEXT_PRIMARY": "#000000",
            "TEXT_SECONDARY": "#444444",
            "CHART_TEMPLATE": "plotly_white",
            "CHART_FONT": "#111111",
            "ACCENT_GOLD": "#C6A87C",
            "DELTA_UP": "#007a3d",
            "DELTA_DOWN": "#d92b2b"
        }

    # Inject CSS
    st.markdown(get_main_css(theme), unsafe_allow_html=True)

    return theme

def render_market_card(name, price, delta, pct):
    delta_color_var = "var(--delta-up)" if delta >= 0 else "var(--delta-down)"
    direction = "up" if delta >= 0 else "down"

    # Accessible label: "S&P 500: 4,500.00, up 10.00 (0.25%)"
    aria_label = f"{name}: {price:,.2f}, {direction} {abs(delta):.2f} ({pct:+.2f}%)"

    return f"""
    <div class="market-card" role="group" aria-label="{aria_label}">
        <div class="market-ticker" aria-hidden="true">{name}</div>
        <div class="market-price" aria-hidden="true">{price:,.2f}</div>
        <div class="market-delta" style="color: {delta_color_var};" aria-hidden="true">{delta:+.2f} ({pct:+.2f}%)</div>
    </div>
    """

def render_sparkline(data, line_color):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data, mode='lines', line=dict(color=line_color, width=2), hoverinfo='skip'))
    fig.update_layout(height=40, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(visible=False), yaxis=dict(visible=False), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    return fig

FOOTER_HTML = """
<div style="font-family: 'Fira Code', monospace; font-size: 10px; color: #888; text-align: center; margin-top: 50px; border-top: 1px solid #30363d; padding-top: 20px; text-transform: uppercase;">
MACROEFFECTS | ALPHA SWARM PROTOCOL | INSTITUTIONAL RISK GOVERNANCE<br>
Disclaimer: This tool provides market analysis for informational purposes only. Not financial advice.<br>
<strong>Institutional Access:</strong> <a href="mailto:institutional@macroeffects.com" style="color: inherit; text-decoration: none; font-weight: bold;">institutional@macroeffects.com</a>
</div>
"""