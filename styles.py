import streamlit as st
import plotly.graph_objects as go
import os
import base64

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
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Fira+Code:wght@300;500;700&display=swap');

    :root {{
        --bg-color: {theme['BG_COLOR']};
        --card-bg: {theme['CARD_BG']};
        --text-primary: {theme['TEXT_PRIMARY']};
        --text-secondary: {theme['TEXT_SECONDARY']};
        --accent-gold: {theme['ACCENT_GOLD']};
        --delta-up: {theme['DELTA_UP']};
        --delta-down: {theme['DELTA_DOWN']};
    }}

    .stApp {{ background-color: var(--bg-color) !important; font-family: 'Inter', sans-serif; }}

    /* FIX FOR PC LAYOUT: Maximize Screen Usage */
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }}

    /* --- TABS (Restored in v56.2) --- */
    button[data-baseweb="tab"] {{
        background: linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(0,0,0,0.05) 100%) !important;
        border: 1px solid rgba(128,128,128,0.2) !important;
        border-radius: 6px 6px 0 0 !important;
        color: var(--text-secondary) !important;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 14px;
        text-transform: uppercase;
        padding: 10px 10px;
        margin-right: 2px;
        flex-grow: 1;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        background: linear-gradient(180deg, #2d343f 0%, #1a1f26 100%) !important;
        border-top: 2px solid var(--accent-gold) !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] p {{ color: #FFFFFF !important; }}

    /* --- MENU BUTTON STYLING (Restored in v56.3) --- */
    [data-testid="stPopover"] button {{
        border: 1px solid #333333;
        background: #000000;
        color: #C6A87C;
        font-size: 28px !important;
        font-weight: bold;
        height: 70px;
        width: 100%;
        margin-top: 0px;
        border-radius: 0 8px 8px 0;
        border-left: 1px solid #333333;
        box-shadow: 0 4px 6px rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 100;
    }}
    [data-testid="stPopover"] button:hover {{ border-color: #C6A87C; color: #FFFFFF; }}

    /* --- TEXT ENFORCERS --- */
    .stMarkdown p, .stMarkdown span, .stMarkdown li {{ color: var(--text-primary) !important; }}
    h3 {{ color: var(--text-secondary) !important; font-weight: 600 !important; }}

    /* --- HEADER CONTAINER (Seamless Black) --- */
    .header-bar {{
        background: #000000;
        height: 70px;
        display: flex;
        flex-direction: row;
        align-items: center;
        padding-left: 15px;
        padding-right: 15px;
        border: 1px solid #333333;
        border-right: none;
        border-radius: 8px 0 0 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.5);
        overflow: hidden;
    }}

    .header-text-col {{
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-left: 12px;
        line-height: 1.1;
    }}

    .steel-text-main {{
        background: linear-gradient(180deg, #FFFFFF 0%, #E0E0E0 40%, #A0A0A0 55%, #FFFFFF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 24px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .steel-text-sub {{
        background: linear-gradient(180deg, #E0E0E0 0%, #A0A0A0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 2px;
        white-space: nowrap;
    }}

    /* MOBILE ADJUSTMENT */
    @media (max-width: 400px) {{
        .steel-text-sub {{ font-size: 9px; white-space: normal; }}
        .block-container {{ padding-left: 0.5rem !important; padding-right: 0.5rem !important; }}
    }}

    /* COMPONENTS */
    .gov-pill {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-family: 'Fira Code', monospace; font-size: 11px; font-weight: bold; color: white; box-shadow: 0 2px 5px rgba(0,0,0,0.2); margin-left: 10px; vertical-align: middle; text-transform: uppercase; }}
    .premium-pill {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 800; color: #3b2c00; background: linear-gradient(135deg, #bf953f 0%, #fcf6ba 100%); box-shadow: 0 2px 5px rgba(0,0,0,0.2); margin-left: 5px; vertical-align: middle; letter-spacing: 1px; }}
    .steel-sub-header {{ background: linear-gradient(145deg, #1a1f26, #2d343f); padding: 8px 15px; border-radius: 6px; border: 1px solid #4a4f58; box-shadow: 0 2px 4px rgba(0,0,0,0.3); margin-bottom: 15px; }}
    .market-card {{ background: var(--card-bg); border: 1px solid rgba(128,128,128,0.2); border-radius: 6px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; margin-bottom: 10px; }}
    .market-ticker {{ color: var(--text-secondary); font-size: 11px; margin-bottom: 2px; }}
    .market-price {{ color: var(--text-primary); font-family: 'Fira Code', monospace; font-size: 22px; font-weight: 700; margin: 2px 0; }}
    .market-delta {{ font-family: 'Fira Code', monospace; font-size: 13px; font-weight: 600; }}

    div[data-testid="stMetricLabel"] {{ color: var(--text-secondary) !important; font-size: 14px !important; font-weight: 500 !important; }}
    div[data-testid="stMetricValue"] {{ color: var(--text-primary) !important; }}
    header[data-testid="stHeader"] {{ visibility: hidden; }}
    #MainMenu, footer {{ visibility: hidden; }}
    div[data-testid="column"] {{ padding: 0px !important; }}
    div[data-testid="stHorizontalBlock"] {{ gap: 0rem !important; }}
    </style>
    """, unsafe_allow_html=True)

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

def render_sub_header(text):
    return f'<div class="steel-sub-header"><span class="steel-text-main" style="font-size: 20px !important;">{text}</span></div>'

FOOTER_HTML = """
<div style="font-family: 'Fira Code', monospace; font-size: 10px; color: #888; text-align: center; margin-top: 50px; border-top: 1px solid #30363d; padding-top: 20px; text-transform: uppercase;">
MACROEFFECTS | ALPHA SWARM PROTOCOL | INSTITUTIONAL RISK GOVERNANCE<br>
Disclaimer: This tool provides market analysis for informational purposes only. Not financial advice.<br>
<strong>Institutional Access:</strong> <a href="mailto:institutional@macroeffects.com" style="color: inherit; text-decoration: none; font-weight: bold;">institutional@macroeffects.com</a>
</div>
"""