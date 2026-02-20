import streamlit as st
import plotly.graph_objects as go
from openai import OpenAI
import styles
import logic

# 1. PAGE SETUP
st.set_page_config(page_title="T1DLH | Contextual Life Hub", page_icon="🩸", layout="wide")
theme = styles.apply_theme()

# 2. INITIALIZE LOCAL LLM CLIENT (LM Studio)
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

# 3. CONTEXT SIDEBAR
with st.sidebar:
    st.header("Context Settings")
    current_context = st.selectbox(
        "Current Activity",
        ["Nominal", "Driving", "High Stress Meeting", "Capital One Strategy Review", "Pinewood Derby prep with Lucas"],
        index=0
    )

# 4. DATA LOADING
try:
    with st.spinner("Connecting to Bio-Telemetry..."):
        full_data = logic.fetch_health_data()
        _, status, color, reason = logic.calc_glycemic_risk(full_data, current_context)
        latest = full_data.iloc[-1]
except Exception as e:
    st.error(f"System Error: {e}")
    st.stop()

# 5. HEADER UI
st.markdown(f"""
    <div style="padding-bottom: 20px;">
        <span style="font-size: 28px; font-weight: bold; color: {theme['TEXT_PRIMARY']};">Personal ERM: Contextual Life Hub</span><br>
        <span style="color: {theme['TEXT_SECONDARY']};">Cognitive Offloading & Risk Governance</span>
    </div>
    <div style="margin-bottom: 20px;">
        <span style="font-weight: 600; color: {theme['TEXT_SECONDARY']};">System Status: </span>
        <div class="gov-pill" style="background: {color}44; border: 1px solid {color}; color: {theme['TEXT_PRIMARY']};">{status}</div>
        <div style="margin-top: 5px; font-size: 14px; color: {theme['TEXT_SECONDARY']};">Analysis: {reason}</div>
    </div>
""", unsafe_allow_html=True)
st.divider()

# 6. DASHBOARD TABS
tab1, tab2, tab3 = st.tabs(["Metabolic State", "Logistical Risk", "Agentic Context"])

with tab1:
    prev = full_data.iloc[-2]
    cols = st.columns(4)
    cols[0].metric("Glucose (mg/dL)", int(latest['Glucose_Value']), int(latest['Glucose_Value'] - prev['Glucose_Value']))
    cols[1].metric("Trend Vector", latest['Trend'])
    cols[2].metric("Active Insulin", "1.5 U", "-0.2 U")
    cols[3].metric("Next Context", current_context, "Active", delta_color="off")
    
    st.markdown("---")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=full_data['Timestamp'], y=full_data['Glucose_Value'], mode='lines', line=dict(color=theme['ACCENT'], width=3)))
    fig.add_hrect(y0=70, y1=180, line_width=0, fillcolor="rgba(166, 218, 149, 0.1)", opacity=0.5)
    fig.add_hline(y=70, line_dash="dash", line_color="#ED8796")
    fig.update_layout(template=theme['CHART_TEMPLATE'], height=400, margin=dict(l=0, r=0, t=30, b=0), yaxis_title="mg/dL")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    h1, h2, h3 = st.columns(3)
    with h1: 
        st.info("**1 HOUR (Transit Risk)**")
        st.markdown("🟢 **SAFE**" if current_context != "Driving" else "🔴 **EVALUATE TRANSIT**")
    with h2: 
        st.info("**4 HOURS (Meeting Risk)**")
        st.markdown("🟡 **CAUTION: CORTISOL SPIKE**" if "Strategy" in current_context else "🟢 **NOMINAL**")
    with h3: 
        st.info("**24 HOURS (Logistics)**")
        st.markdown("🟢 **SAFE** - Sensor expires in 3 days.")

with tab3:
    st.markdown("### Agentic Context Synthesis")
    
    # AI Briefing Generation
    with st.spinner("Synthesizing context with Local LLM..."):
        try:
            response = client.chat.completions.create(
                model="local-model",
                messages=[
                    {"role": "system", "content": "You are a T1D Risk Manager. Analyze the data and give a 2-sentence risk summary."},
                    {"role": "user", "content": f"Glucose: {latest['Glucose_Value']}, Context: {current_context}"}
                ],
                timeout=8
            )
            st.success("**AI Risk Briefing:**")
            st.write(response.choices[0].message.content)
        except Exception:
            st.warning("⚠️ LM Studio connection pending. Ensure the local server is running at port 1234.")

    st.divider()
    
    # Interactive Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Log an event or ask for a risk assessment..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                response = client.chat.completions.create(
                    model="local-model",
                    messages=[{"role": "system", "content": "You are a T1D Risk Manager."}] + st.session_state.messages
                )
                answer = response.choices[0].message.content
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception:
                st.error("Connection to local engine lost.")

st.markdown(styles.FOOTER_HTML, unsafe_allow_html=True)