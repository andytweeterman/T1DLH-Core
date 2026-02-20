import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import styles
import logic

# 1. PAGE SETUP (MUST BE FIRST)
st.set_page_config(
    page_title="T1DLH | Contextual Life Hub", 
    page_icon="🩸", 
    layout="wide",
    initial_sidebar_state="collapsed"
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
        _, status, color, reason = logic.calc_glycemic_risk(full_data, current_context=current_context)
    else:
        status, color, reason = "DATA ERROR", "#ED8796", "Data Feed Unavailable"
except Exception as e:
    status, color, reason = "SYSTEM ERROR", "#ED8796", f"Connection Failed: {e}"

# 5. HEADER UI
c_title, c_menu = st.columns([0.90, 0.10], gap="small")
with c_title:
    header_html = f"""
    <div class="header-bar">
        <div class="header-text-col">
            <span class="steel-text-main" style="font-size: 28px; color: {theme.get('TEXT_PRIMARY', '#CAD3F5')};">Personal ERM: Contextual Life Hub</span><br>
            <span class="steel-text-sub" style="color: {theme.get('TEXT_SECONDARY', '#A5ADCB')};">Cognitive Offloading & Risk Governance</span>
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
    <span style="font-family: 'Inter'; font-weight: 600; font-size: 16px; color: var(--text-secondary);">System Status</span>
    <div class="gov-pill" style="background: linear-gradient(135deg, {color}, {color}88); border: 1px solid {color};">{status}</div>
</div>
""", unsafe_allow_html=True)

if reason:
    st.caption(f"**Analysis:** {reason}")

st.divider()

# 7. MAIN DASHBOARD TABS
if full_data is not None and not full_data.empty:
    
    tab1, tab2, tab3 = st.tabs(["Metabolic State", "Logistical Risk", "Agentic Context"])
    
    # --- TAB 1: METABOLIC STATE ---
    with tab1:
        st.markdown('### Metabolic State Grid')
        
        # Grid Data
        latest_row = full_data.iloc[-1]
        prev_row = full_data.iloc[-2] if len(full_data) > 1 else latest_row
        
        # Handle dynamic column names from Jules's mock data generator
        bg_col = 'glucose' if 'glucose' in full_data.columns else 'Glucose_Value'
        trend_col = 'trend' if 'trend' in full_data.columns else 'Trend'
        time_col = 'Timestamp' if 'Timestamp' in full_data.columns else full_data.columns[0]
        
        current_bg = latest_row[bg_col]
        bg_delta = current_bg - prev_row[bg_col]
        current_trend = latest_row[trend_col]
        
        cols = st.columns(4)
        with cols[0]: st.metric(label="Glucose (mg/dL)", value=int(current_bg), delta=int(bg_delta))
        with cols[1]: st.metric(label="Trend Vector", value=str(current_trend))
        with cols[2]: st.metric(label="Active Insulin (IOB)", value="1.5 U", delta="-0.2 U")
        with cols[3]: st.metric(label="Next Event Context", value=current_context, delta="In 45 mins", delta_color="off")
        
        st.markdown("---")
        st.markdown('### Continuous Glucose Monitoring (24H)')
        
        # High-Fidelity Plotly Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=full_data[time_col] if time_col in full_data.columns else full_data.index, 
            y=full_data[bg_col], 
            mode='lines', 
            line=dict(color="#8AADF4", width=3), # Macchiato Blue
            name="Glucose"
        ))
        
        # Target Range Cone
        fig.add_hrect(y0=70, y1=180, line_width=0, fillcolor="rgba(166, 218, 149, 0.15)", opacity=0.5) # Macchiato Green
        fig.add_hline(y=70, line_dash="dash", line_color="#ED8796", annotation_text="Hypo Threshold") # Macchiato Red
        
        fig.update_layout(
            template=theme.get("CHART_TEMPLATE", "plotly_dark"),
            height=400,
            margin=dict(l=0, r=0, t=30, b=0),
            yaxis_title="mg/dL"
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 2: LOGISTICAL RISK ---
    with tab2:
        st.markdown('### Logistical Risk & Executive Function')
        
        h1, h2, h3 = st.columns(3)
        with h1: 
            st.info("**1 HOUR (Immediate/Transit)**")
            if current_context == "Driving" and current_bg < 100:
                st.error("🔴 **TRANSIT RISK** - Glucose dropping before commute. Consume 15g carbs.")
            else:
                st.success("🟢 **SAFE** - Glucose stable, no immediate transit risk.")
                
        with h2: 
            st.info("**4 HOURS (Upcoming Events)**")
            if "Meeting" in current_context or "Strategy" in current_context:
                st.warning(f"🟡 **CAUTION** - {current_context} approaching. Anticipate adrenaline spike. Delay bolus.")
            else:
                st.success("🟢 **NOMINAL** - No high-stress events on schedule.")
                
        with h3: 
            st.info("**24 HOURS (Overnight Logistics)**")
            st.success("🟢 **NOMINAL** - Sensor expires in 3 days. No action required.")

    # --- TAB 3: AGENTIC CONTEXT ---
    with tab3:
        st.markdown('### Agentic Context Synthesis')
        
        with st.expander("AI Risk Assessment: Next 12 Hours", expanded=True):
            st.markdown(f"""
            **Synthesis:** Your glucose is currently at {int(current_bg)} mg/dL. 
            I am tracking your upcoming context: **{current_context}**. 
            
            **Recommendation:** Maintain current basal rate. If transitioning to a high-stress environment, consider silencing non-critical alerts to prevent alarm fatigue.
            """)
            
        st.info("💡 **Agent Status:** Continuous monitoring active. Ready to connect to local LM Studio endpoint.")
        
        # Frictionless Capture Bar
        user_input = st.chat_input("Log an event, meal, or unstructured thought...")
        if user_input:
            st.success(f"Context logged and structured: {user_input}")
            # Note: This will be piped to LM Studio in the next step!

else:
    st.error("Data connection initializing or offline. Please check network.")

st.markdown(styles.FOOTER_HTML, unsafe_allow_html=True)