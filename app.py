import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from openai import OpenAI
import styles
import logic

# 1. PAGE SETUP (MUST BE FIRST)
st.set_page_config(
    page_title="T1DLH | Life Hub",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. SETUP & THEME
theme = styles.apply_theme()

# Initialize Local LLM Client
llm_client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

# 3. DATA LOADING
try:
    with st.spinner("Connecting to Bio-Telemetry..."):
        cgm_data = logic.fetch_health_data()
        iob = logic.get_active_insulin()
        next_event = logic.get_schedule()

    if cgm_data is not None and not cgm_data.empty:
        # Calculate Risk
        cgm_data, status, color, reason = logic.calc_glycemic_risk(cgm_data, next_event)
        current_bg = cgm_data['Glucose'].iloc[-1]
        current_trend = cgm_data['Trend'].iloc[-1]
    else:
        status, color, reason = "DATA ERROR", "#ff0000", "Sensor Disconnected"
        current_bg = 0
        current_trend = "—"
        iob = 0.0
        next_event = "Unknown"
except Exception as e:
    status, color, reason = "SYSTEM ERROR", "#ff0000", f"Connection Failed: {str(e)}"
    cgm_data = None
    current_bg = 0
    current_trend = "—"
    iob = 0.0
    next_event = "Unknown"

# 4. HEADER UI
c_title, c_menu = st.columns([0.90, 0.10], gap="small")
with c_title:
    # Use existing shield.png if available, or just skip image if it fails
    img_b64 = styles.get_base64_image("shield.png")
    header_html = f"""
    <div class="header-bar">
    {'<img src="data:image/png;base64,' + img_b64 + '" style="height: 50px; width: auto; flex-shrink: 0; object-fit: contain;">' if img_b64 else ''}
    <div class="header-text-col">
    <span class="steel-text-main">Personal ERM</span>
    <span class="steel-text-sub">Contextual Life Hub</span>
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
        st.divider()
        st.link_button("Documentation", "https://github.com/andytweeterman/T1DLH-Core")

# 5. STATUS BAR
st.markdown(f"""
<div style="margin-bottom: 20px; margin-top: 5px;">
    <span style="font-family: 'Inter'; font-weight: 600; font-size: 16px; color: var(--text-secondary);">Metabolic Intelligence: Real-Time Risk Governance</span>
    <div class="gov-pill" style="background: linear-gradient(135deg, {color}, {color}88); border: 1px solid {color};">{status}</div>
    <div class="premium-pill">LIVE</div>
</div>
""", unsafe_allow_html=True)
st.divider()

# 6. HELPER FUNCTIONS
def get_agentic_briefing(glucose, trend, IOB, upcoming_event):
    """Fetches a risk synthesis from the local LLM."""
    try:
        system_prompt = (
            "You are an Enterprise Risk Manager acting as a Context Engine for a Type 1 Diabetic. "
            "Analyze the current telemetry and schedule, and provide a concise, 3-sentence risk synthesis "
            "and a specific mitigation recommendation."
        )

        user_prompt = f"Current Glucose: {glucose} ({trend}). Active Insulin: {IOB}. Upcoming Event: {upcoming_event}."

        response = llm_client.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LM Studio server offline or error: {str(e)}"

# 7. MAIN CONTENT GRID
if cgm_data is not None:
    tab1, tab2, tab3 = st.tabs(["Metabolic State", "Logistical Risk", "Agentic Context"])

    # --- TAB 1: METABOLIC STATE ---
    with tab1:
        st.markdown('<div class="steel-sub-header"><span class="steel-text-main" style="font-size: 20px !important;">Real-Time Telemetry</span></div>', unsafe_allow_html=True)

        # 1. METRIC GRID
        cols = st.columns(4)
        with cols[0]:
            st.markdown(styles.render_metric_card("Current Glucose", f"{current_bg}", f"{current_trend}", color), unsafe_allow_html=True)
        with cols[1]:
            st.markdown(styles.render_metric_card("Trend Vector", current_trend, "Stable" if current_trend == "→" else "Changing"), unsafe_allow_html=True)
        with cols[2]:
            st.markdown(styles.render_metric_card("Active Insulin (IOB)", f"{iob} U", "On Board"), unsafe_allow_html=True)
        with cols[3]:
            st.markdown(styles.render_metric_card("Next Event Context", next_event, "Upcoming"), unsafe_allow_html=True)

        st.divider()

        # 2. CGM CHART
        st.markdown('<div class="steel-sub-header"><span class="steel-text-main" style="font-size: 20px !important;">24-Hour Glucose Architecture</span></div>', unsafe_allow_html=True)

        fig = go.Figure()

        # Target Range Zone (70-180)
        fig.add_hrect(y0=70, y1=180, fillcolor="rgba(0, 255, 0, 0.05)", layer="below", line_width=0)

        # Main Line
        fig.add_trace(go.Scatter(
            x=cgm_data.index,
            y=cgm_data['Glucose'],
            mode='lines',
            name='Glucose',
            line=dict(color=theme["CHART_FONT"], width=3)
        ))

        # Add Threshold Lines
        fig.add_hline(y=70, line_dash="dot", line_color="#f93e3e", annotation_text="Hypo Limit")
        fig.add_hline(y=180, line_dash="dot", line_color="#f1c40f", annotation_text="Hyper Limit")

        fig.update_layout(
            height=400,
            template=theme["CHART_TEMPLATE"],
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=theme["CHART_FONT"]),
            xaxis_title="Time",
            yaxis_title="mg/dL"
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 2: LOGISTICAL RISK ---
    with tab2:
        st.markdown('<div class="steel-sub-header"><span class="steel-text-main" style="font-size: 20px !important;">Forward Risk Projection</span></div>', unsafe_allow_html=True)

        # Risk Dashboard
        r1, r2, r3 = st.columns(3)
        with r1:
            st.info("**1 HOUR HORIZON**")
            if "Driving" in next_event and current_bg < 100:
                st.error("🔴 **HIGH RISK** (Driving + Hypo)")
            else:
                st.success("🟢 **STABLE**")
        with r2:
            st.info("**4 HOUR HORIZON**")
            st.warning("🟡 **MODERATE** (Schedule Intensity)")
        with r3:
            st.info("**24 HOUR HORIZON**")
            st.success("🟢 **OPTIMAL** (Sleep Pattern)")

        st.divider()
        st.markdown(f"**Current Context:** {next_event}")
        st.caption("Risk assessment based on mocked schedule data.")

    # --- TAB 3: AGENTIC CONTEXT ---
    with tab3:
        st.markdown('<div class="steel-sub-header"><span class="steel-text-main" style="font-size: 20px !important;">AI Context Synthesis</span></div>', unsafe_allow_html=True)

        # 1. Briefing
        with st.expander("AI Risk Assessment: Next 12 Hours", expanded=True):
            with st.spinner("Synthesizing Context..."):
                try:
                    briefing_text = get_agentic_briefing(current_bg, current_trend, f"{iob} U", next_event)
                    st.markdown(briefing_text)
                except Exception as e:
                    st.error(f"Could not generate briefing: {e}")

        st.divider()

        # 2. Chat Interface
        st.subheader("Agentic Chat")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if user_input := st.chat_input("Log context or ask for risk analysis..."):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                try:
                    stream = llm_client.chat.completions.create(
                        model="local-model",
                        messages=[
                            {"role": "system", "content": "You are an Enterprise Risk Manager for a T1D. Be concise and actionable."},
                            *st.session_state.messages
                        ],
                        stream=True,
                    )
                    response = st.write_stream(stream)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"LM Studio Error: {str(e)}")

else:
    st.error("Telemetry Offline. Check Sensor Connection.")

st.markdown(styles.FOOTER_HTML, unsafe_allow_html=True)
