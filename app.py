import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import styles
import logic

# 1. PAGE SETUP (MUST BE FIRST)
st.set_page_config(
    page_title="T1D Contextual Risk | Bio-Telemetry",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. SETUP & THEME
theme = styles.apply_theme()

# 3. CONTEXT SELECTION (Sidebar)
with st.sidebar:
    st.header("Context Settings")
    current_context = st.selectbox(
        "Current Activity / Context",
        ["Nominal", "Driving", "High Stress Meeting", "Capital One Strategy Review", "Pinewood Derby prep with Lucas"],
        index=0
    )
    st.info(f"Active Context: **{current_context}**")

# 4. DATA LOADING
full_data = None
status, color, reason = "SYSTEM BOOT", "#A5ADCB", "Initializing..."

try:
    with st.spinner("Connecting to Bio-Telemetry..."):
        full_data = logic.fetch_health_data()

    if full_data is not None and not full_data.empty:
        # Calculate Risk
        _, status, color, reason = logic.calc_glycemic_risk(full_data, current_context)
        latest_row = full_data.iloc[-1]
    else:
        status, color, reason = "DATA ERROR", "#ED8796", "Data Feed Unavailable"
except Exception as e:
    status, color, reason = "SYSTEM ERROR", "#ED8796", f"Connection Failed: {e}"

# 5. HEADER UI
c_title, c_menu = st.columns([0.90, 0.10], gap="small")
with c_title:
    # Use existing shield.png or similar if available, or just text
    header_html = f"""
    <div class="header-bar">
    <div class="header-text-col">
    <span class="steel-text-main">T1D Contextual Risk</span>
    <span class="steel-text-sub">Bio-Telemetry Dashboard</span>
    </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

with c_menu:
    with st.popover("☰", use_container_width=True):
        st.caption("Settings")
        is_dark = st.toggle("Dark Mode", value=st.session_state.get("dark_mode", False))
        if is_dark != st.session_state.get("dark_mode", False):
            st.session_state["dark_mode"] = is_dark
            st.rerun()

# 6. STATUS BAR
st.markdown(f"""
<div style="margin-bottom: 20px; margin-top: 5px;">
    <span style="font-family: 'Inter'; font-weight: 600; font-size: 16px; color: var(--text-secondary);">Real-Time Risk Assessment</span>
    <div class="gov-pill" style="background: linear-gradient(135deg, {color}, {color}88); border: 1px solid {color};">{status}</div>
    <div class="premium-pill">LIVE</div>
</div>
""", unsafe_allow_html=True)

if reason:
    st.caption(f"**Analysis:** {reason}")

st.divider()

# 7. MAIN CONTENT
if full_data is not None and not full_data.empty:

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Glucose Trend")
        # Simple Line Chart
        st.line_chart(full_data['glucose'])

    with col2:
        st.subheader("Current Metrics")
        current_glucose = latest_row['glucose']
        trend = latest_row['trend']

        st.metric("Glucose", f"{current_glucose} mg/dL", delta=trend)
        st.metric("Context", current_context)

else:
    st.error("Data connection initializing or offline. Please check network.")

st.markdown(styles.FOOTER_HTML, unsafe_allow_html=True)
