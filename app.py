import html
import streamlit as st
import plotly.graph_objects as go
import google.generativeai as genai
import styles
import logic
import json
import logging

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# 1. PAGE SETUP
st.set_page_config(page_title="TLDH | Contextual Life Hub", page_icon="🩸", layout="wide")
styles.apply_theme() # Injects auto-switching CSS variables

# 2. INITIALIZE GEMINI CLIENT
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

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
        ["Normal", "Stressed", "Sick", "Exercise", "Travel"],
        index=0
    )

# 4. DATA LOADING
try:
    with st.spinner("Connecting to Bio-Telemetry..."):
        full_data = logic.fetch_health_data()
        _, status, reason = logic.calc_glycemic_risk(full_data, current_context)
        latest = full_data.iloc[-1]
except Exception as e:
    logger.error(f"Data loading failed: {e}", exc_info=True)
    st.error("Oops! Something went wrong loading your health data.")
    st.stop()

# 5. HEADER UI
safe_status = html.escape(str(status))
safe_reason = html.escape(str(reason))
st.markdown(f"""
    <div style="padding-bottom: 20px;">
        <span style="font-size: 28px; font-weight: bold; color: var(--text-primary);">My Health Hub</span><br>
        <span style="color: var(--text-secondary);">Smart Health Companion</span>
    </div>
    <div style="margin-bottom: 20px;">
        <span style="font-weight: 600; color: var(--text-secondary);">Status: </span>
        <div class="gov-pill">{safe_status}</div>
        <div style="margin-top: 5px; font-size: 14px; color: var(--text-secondary);">Analysis: {safe_reason}</div>
    </div>
""", unsafe_allow_html=True)
st.divider()

# 6. MOBILE-FIRST BUTTON NAVIGATION (Replacing Tabs)
if "active_view" not in st.session_state:
    st.session_state.active_view = "Wellness"

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Wellness", use_container_width=True, type="primary" if st.session_state.active_view == "Wellness" else "secondary"):
        st.session_state.active_view = "Wellness"
        st.rerun()

with col2:
    if st.button("Schedule", use_container_width=True, type="primary" if st.session_state.active_view == "Schedule" else "secondary"):
        st.session_state.active_view = "Schedule"
        st.rerun()

with col3:
    if st.button("Assistant", use_container_width=True, type="primary" if st.session_state.active_view == "Assistant" else "secondary"):
        st.session_state.active_view = "Assistant"
        st.rerun()

st.markdown("---")

# 7. RENDER SELECTED VIEW
if st.session_state.active_view == "Wellness":
    prev = full_data.iloc[-2]
    cols = st.columns(3)
    cols[0].metric("Blood Sugar (mg/dL)", int(latest['Glucose_Value']), int(latest['Glucose_Value'] - prev['Glucose_Value']))
    cols[1].metric("Trend", latest['Trend'])
    cols[2].metric("Active Insulin", "1.5 U", "-0.2 U")

    st.markdown("---")
    
    # Plotly setup with transparent backgrounds to let OS theme show through
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=full_data['Timestamp'], y=full_data['Glucose_Value'], mode='lines', line=dict(color='#8AADF4', width=3)))
    fig.add_hrect(y0=70, y1=180, line_width=0, fillcolor="rgba(166, 218, 149, 0.1)", opacity=0.5)
    fig.add_hline(y=70, line_dash="dash", line_color="#ED8796")
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='gray'),
        height=400, 
        margin=dict(l=0, r=0, t=30, b=0), 
        yaxis_title="mg/dL"
    )
    st.plotly_chart(fig, use_container_width=True)

elif st.session_state.active_view == "Schedule":
    h1, h2, h3 = st.columns(3)
    
    card_style = "background-color: var(--card-bg); padding: 20px; border-radius: 20px; border: 1px solid rgba(128, 128, 128, 0.1); box-shadow: var(--card-shadow); text-align: center; height: 100%;"
    label_style = "color: var(--text-secondary); font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; font-size: 0.8rem; margin-bottom: 10px;"
    value_style = "color: var(--text-primary); font-weight: 800; font-size: 1.2rem;"

    transit_status = "🟢 SAFE" if current_context != "Travel" else "🔴 EVALUATE TRANSIT"
    meeting_status = "🟡 CAUTION" if current_context == "Stressed" else "🟢 ALL CLEAR"
    daily_status = "🟢 GOOD<br><span style='font-size:0.9rem; font-weight:400; color:var(--text-secondary)'>Sensor expires in 3 days</span>"

    with h1:
        st.markdown(f"<div style='{card_style}'><div style='{label_style}'>1 HOUR (Transit)</div><div style='{value_style}'>{transit_status}</div></div>", unsafe_allow_html=True)
    with h2:
        st.markdown(f"<div style='{card_style}'><div style='{label_style}'>4 HOURS (Logistics)</div><div style='{value_style}'>{meeting_status}</div></div>", unsafe_allow_html=True)
    with h3:
        st.markdown(f"<div style='{card_style}'><div style='{label_style}'>24 HOURS (Daily)</div><div style='{value_style}'>{daily_status}</div></div>", unsafe_allow_html=True)

elif st.session_state.active_view == "Assistant":
    st.markdown("### Health Assistant")

    if st.button("Generate Live Health Briefing", type="primary"):
        with st.spinner("Analyzing health data..."):
            try:
                briefing_prompt = f"You are a friendly health assistant. Analyze the data and give a 2-sentence friendly summary.\nCurrent Blood Sugar: {latest['Glucose_Value']}, Current Activity: {current_context}"
                briefing_res = model_text.generate_content(briefing_prompt)
                st.success("**Health Briefing:**")
                st.write(briefing_res.text)
            except Exception as e:
                logger.error(f"Briefing generation failed: {e}", exc_info=True)
                st.warning("⚠️ AI assistant connection failed. Please try again later.")

    st.divider()

    extraction_prompt = """
    You are a friendly health assistant. The user will provide a casual update on how they are feeling or what they are doing.
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
                st.caption("🔍 **Logged Details:**")
                st.json(message["tags"], expanded=False)
            else:
                st.markdown(message["content"])

    if prompt := st.chat_input("Log an event (e.g., 'Pump site itching, ate handful of pretzels, stressed')"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                full_prompt = f"{extraction_prompt}\n\nUser Input: {prompt}"
                response = model_json.generate_content(full_prompt)

                parsed_data = json.loads(response.text)

                reply_text = parsed_data.get("reply", "Context logged.")
                extracted_tags = parsed_data.get("tags", {})

                st.markdown(reply_text)
                st.caption("🔍 **Logged Details:**")
                st.json(extracted_tags, expanded=False)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply_text,
                    "tags": extracted_tags
                })

            except Exception as e:
                logger.error(f"Event extraction failed: {e}", exc_info=True)
                st.error("Oops! Something went wrong processing your input.")

st.markdown(styles.FOOTER_HTML, unsafe_allow_html=True)