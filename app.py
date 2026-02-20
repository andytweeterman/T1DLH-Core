import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import styles
import logic

# 1. PAGE SETUP (MUST BE FIRST)
st.set_page_config(
    page_title="MacroEffects | Outthink the Market",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. SETUP & THEME
theme = styles.apply_theme()

# 3. DATA LOADING
full_data = None
status, color, reason = "SYSTEM BOOT", "#888888", "Initializing..."

try:
    with st.spinner("Connecting to Global Swarm..."):
        full_data = logic.fetch_health_data()

    if full_data is not None and not full_data.empty:
        gov_df, status, color, reason = logic.calc_glycemic_risk(full_data, current_context="Nominal")
    else:
        status, color, reason = "DATA ERROR", "#ff0000", "Data Feed Unavailable"
except Exception as e:
    status, color, reason = "SYSTEM ERROR", "#ff0000", "Connection Failed"

# 4. HEADER UI
c_title, c_menu = st.columns([0.90, 0.10], gap="small")
with c_title:
    img_b64 = styles.get_base64_image("shield.png")
    header_html = f"""
    <div class="header-bar">
    {'<img src="data:image/png;base64,' + img_b64 + '" style="height: 50px; width: auto; flex-shrink: 0; object-fit: contain;">' if img_b64 else ''}
    <div class="header-text-col">
    <span class="steel-text-main">MacroEffects</span>
    <span class="steel-text-sub">Outthink the Market</span>
    </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

with c_menu:
    with st.popover("☰", use_container_width=True):
        st.caption("Settings & Links")
        is_dark = st.toggle("Dark Mode", value=st.session_state.get("dark_mode", False))
        if is_dark != st.session_state.get("dark_mode", False):
            st.session_state["dark_mode"] = is_dark
            st.rerun()
        st.divider()
        st.page_link("https://sixmonthstockmarketforecast.com/home/", label="Six Month Forecast", icon="📈")
        st.link_button("User Guide", "https://github.com/andytweeterman/alpha-swarm-dashboard/blob/main/docs/USER_GUIDE.md")
        st.link_button("About Us", "https://sixmonthstockmarketforecast.com/about")

# 5. STATUS BAR
st.markdown(f"""
<div style="margin-bottom: 20px; margin-top: 5px;">
    <span style="font-family: 'Inter'; font-weight: 600; font-size: 16px; color: var(--text-secondary);">Personal ERM: Contextual Life Hub</span>
    <div class="gov-pill" style="background: linear-gradient(135deg, {color}, {color}88); border: 1px solid {color};">{status}</div>
    <div class="premium-pill">PREMIUM</div>
</div>
""", unsafe_allow_html=True)
st.divider()

# 6. MAIN CONTENT GRID
if full_data is not None:

    tab1, tab2, tab3 = st.tabs(["Metabolic State", "Logistical Risk", "Agentic Context"])

    # --- TAB 1: METABOLIC STATE ---
    with tab1:
        st.markdown('<div class="steel-sub-header"><span class="steel-text-main" style="font-size: 20px !important;">Metabolic State Grid</span></div>', unsafe_allow_html=True)

        # New 4-column layout
        cols = st.columns(4)

        # Extract metrics
        current_bg = full_data['Glucose_Value'].iloc[-1]
        prev_bg = full_data['Glucose_Value'].iloc[-2]
        bg_delta = current_bg - prev_bg
        current_trend = full_data['Trend'].iloc[-1]

        with cols[0]:
            st.metric(label="Glucose (mg/dL)", value=int(current_bg), delta=int(bg_delta))
        with cols[1]:
            st.metric(label="Trend Vector", value=str(current_trend))
        with cols[2]:
            st.metric(label="Active Insulin (IOB)", value="1.5 U", delta="-0.2 U")
        with cols[3]:
            st.metric(label="Next Event Context", value="Team Review", delta="In 45 mins", delta_color="off")

        st.divider()

        # Deep Dive Chart (Commented out for future sprint)
        # st.markdown('<div class="steel-sub-header"><span class="steel-text-main" style="font-size: 20px !important;">Swarm Deep Dive</span></div>', unsafe_allow_html=True)
        # ... (Old financial chart code removed/commented out) ...

    # --- TAB 2: LOGISTICAL RISK ---
    with tab2:
        st.info("Logistical Risk module under construction.")

    # --- TAB 3: AGENTIC CONTEXT ---
    with tab3:
        st.info("Agentic Context module under construction.")

else:
    st.error("Data connection initializing or offline. Please check network.")

st.markdown(styles.FOOTER_HTML, unsafe_allow_html=True)
