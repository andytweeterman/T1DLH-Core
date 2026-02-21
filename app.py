import streamlit as st
import plotly.graph_objects as go
import google.generativeai as genai
import styles
import logic
import json

# 1. PAGE SETUP
st.set_page_config(page_title="TLDH | Contextual Life Hub", page_icon="🩸", layout="wide")
theme = styles.apply_theme()

# 2. INITIALIZE GEMINI CLIENT
# The app securely pulls your API key from Streamlit Cloud's secret vault
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Initialize the blazing fast 3.0 Flash model
# We set up two instances: one for standard text, one strictly forced into JSON mode
model_text = genai.GenerativeModel('gemini-3-flash-preview')
model_json = genai.GenerativeModel(
    'gemini-3-flash-preview', 
    generation_config={"response_mime_type": "application/json"}
)

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
    <div class="header-container">
        <div style="padding-bottom: 20px;">
            <span style="font-size: 28px; font-weight: bold; color: {theme['TEXT_PRIMARY']};">Personal ERM: TLDH Hub</span><br>
            <span style="color: {theme['TEXT_SECONDARY']};">Cognitive Offloading & Risk Governance</span>
        </div>
        <div>
            <span style="font-weight: 600; color: {theme['TEXT_SECONDARY']};">System Status: </span>
            <div class="gov-pill" style="background: {color}44; border: 1px solid {color}; color: {theme['TEXT_PRIMARY']};">{status}</div>
            <div style="margin-top: 5px; font-size: 14px; color: {theme['TEXT_SECONDARY']};">Analysis: {reason}</div>
        </div>
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
    
    # MANUAL TRIGGER TO SAVE API QUOTA
    if st.button("Generate Live Risk Briefing", type="primary"):
        with st.spinner("Synthesizing context with Gemini 3.0 Flash..."):
            try:
                briefing_prompt = f"You are a T1D Risk Manager. Analyze the data and give a 2-sentence risk summary.\nCurrent Glucose: {latest['Glucose_Value']}, Current Context: {current_context}"
                briefing_res = model_text.generate_content(briefing_prompt)
                st.success("**AI Risk Briefing:**")
                st.write(briefing_res.text)
            except Exception as e:
                st.warning(f"⚠️ Cloud AI connection failed. Check API key or Quota limit. Details: {e}")

    st.divider()
    
    # The Structured Extraction Prompt for JSON Mode
    extraction_prompt = """
    You are a T1D Risk Manager. The user will provide a messy, unstructured brain dump.
    You MUST respond in strict JSON format containing exactly two keys:
    1. "reply": A short, empathetic, helpful response to the user.
    2. "tags": A nested JSON object extracting the following keys: "event_type" (e.g. meal, stress, hardware), "estimated_carbs" (integer or null), "physiological_state" (e.g. high_stress, nominal), and "hardware_alert" (string or null).
    """

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and "tags" in message:
                st.markdown(message["content"])
                st.caption("🔍 **Extracted Telemetry Tags:**")
                st.json(message["tags"], expanded=False)
            else:
                st.markdown(message["content"])

    if prompt := st.chat_input("Log an event (e.g., 'Pump site itching, ate handful of pretzels, stressed about meeting')"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                # Combine instructions and user input for the JSON extraction
                full_prompt = f"{extraction_prompt}\n\nUser Input: {prompt}"
                response = model_json.generate_content(full_prompt)
                
                # Parse the native JSON response from Gemini
                parsed_data = json.loads(response.text)
                
                reply_text = parsed_data.get("reply", "Context logged.")
                extracted_tags = parsed_data.get("tags", {})
                
                # Display the conversational reply
                st.markdown(reply_text)
                
                # Display the invisible data tags
                st.caption("🔍 **Extracted Telemetry Tags:**")
                st.json(extracted_tags, expanded=False)
                
                # Save both to history so they persist on reload
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": reply_text,
                    "tags": extracted_tags
                })
                
            except Exception as e:
                st.error(f"Extraction failed: {e}")

st.markdown(styles.FOOTER_HTML, unsafe_allow_html=True)
