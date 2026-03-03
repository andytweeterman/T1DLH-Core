import html
import streamlit as st
import plotly.graph_objects as go
import google.generativeai as genai
import styles
import logic
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# 1. PAGE SETUP & THEME
# -----------------------------------------------------------------------------
st.set_page_config(page_title="TLDH | Total Life Download Hub", page_icon="🧬", layout="wide")
styles.apply_theme()  # Injects auto-switching CSS variables (Light/Dark mode)

# -----------------------------------------------------------------------------
# 2. INITIALIZE GEMINI CLIENT
# -----------------------------------------------------------------------------
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # Text Model for general chat
    model_text = genai.GenerativeModel('gemini-1.5-flash')
    
    # JSON Model for structured data extraction
    model_json = genai.GenerativeModel(
        'gemini-1.5-flash',
        generation_config={"response_mime_type": "application/json"}
    )
except Exception as e:
    st.error(f"⚠️ API Configuration Error: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 3. CONTEXT SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("Context Settings")
    current_context = st.selectbox(
        "Current Activity",
        ["Normal", "Stressed", "Sick", "Exercise", "Travel"],
        index=0
    )

# -----------------------------------------------------------------------------
# 4. DATA LOADING (Dexcom/Whoop/Mock)
# -----------------------------------------------------------------------------
try:
    with st.spinner("Syncing Bio-Telemetry..."):
        full_data = logic.fetch_health_data()
        _, status, reason = logic.calc_glycemic_risk(full_data, current_context)
        latest = full_data.iloc[-1]
except Exception as e:
    logger.error(f"Data loading failed: {e}", exc_info=True)
    st.error("Oops! Something went wrong loading your health data.")
    st.stop()

# -----------------------------------------------------------------------------
# 5. HEADER UI
# -----------------------------------------------------------------------------
safe_status = html.escape(str(status))
safe_reason = html.escape(str(reason))

st.markdown(f"""
    <div style="padding-bottom: 20px;">
        <span style="font-size: 28px; font-weight: bold; color: var(--text-primary);">Total Life Download Hub</span><br>
        <span style="color: var(--text-secondary);">Agentic Risk Management Engine</span>
    </div>
    <div style="margin-bottom: 20px;">
        <span style="font-weight: 600; color: var(--text-secondary);">Current Status: </span>
        <div class="gov-pill">{safe_status}</div>
        <div style="margin-top: 5px; font-size: 14px; color: var(--text-secondary);">Analysis: {safe_reason}</div>
    </div>
""", unsafe_allow_html=True)

st.divider()

# -----------------------------------------------------------------------------
# 6. NAVIGATION (Mobile-First)
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# 7. RENDER VIEWS
# -----------------------------------------------------------------------------

# --- VIEW A: WELLNESS (Metrics + Chart) ---
if st.session_state.active_view == "Wellness":
    prev = full_data.iloc[-2]
    cols = st.columns(3)
    cols[0].metric("Blood Sugar (mg/dL)", int(latest['Glucose_Value']), int(latest['Glucose_Value'] - prev['Glucose_Value']))
    cols[1].metric("Trend", latest['Trend'])
    cols[2].metric("Active Insulin", "1.5 U", "-0.2 U")

    st.markdown("---")
    
    # Plotly setup with transparent backgrounds
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

# --- VIEW B: SCHEDULE (Context Cards) ---
elif st.session_state.active_view == "Schedule":
    h1, h2, h3 = st.columns(3)
    
    # Card CSS mirroring the st.metric cards
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

# --- VIEW C: ASSISTANT (The "Life Download" Engine) ---
elif st.session_state.active_view == "Assistant":
    st.markdown("### 🧬 Total Life Download Engine")
    st.caption("Log unstructured thoughts to track Biological, Cognitive, and Emotional load.")

    # The System Prompt for the LLM
    extraction_prompt = """
    **ROLE:** You are the Total Life Download Analyst. 
    **GOAL:** The user will provide unstructured "downloads" (journal entries, rants, status updates).
    
    **YOUR TASK:**
    1. **Validate:** Offer a brief, 1-sentence empathetic acknowledgement in the "reply" field.
    2. **Structure:** Convert the qualitative text into a strict JSON data object that tracks "Life Load".
    
    **SCORING FRAMEWORK (1-10 Scale):**
    * **Bio:** Physical stress, illness, high blood sugar, poor sleep.
    * **Cog:** Deep work, studying, strategic planning, decision fatigue.
    * **Emo:** Family dynamics, anxiety, excitement, frustration.
    
    **OUTPUT FORMAT (Strict JSON only):**
    {
        "reply": "Empathetic response string here.",
        "summary": "5-word summary of the entry",
        "tags": ["Tag1", "Tag2", "Tag3"],
        "scores": { "bio": 5, "cog": 5, "emo": 5 },
        "impact_prediction": "Prediction on HRV/Glucose/Insulin Resistance based on context."
    }
    """

    # Initialize Session State for History
    if "journal_history" not in st.session_state:
        st.session_state.journal_history = []

    # --- INPUT FORM ---
    with st.form("journal_form", clear_on_submit=True):
        text_input = st.text_area("Life Download:", placeholder="e.g. 'Stressed about work plan, but wife is home. Did home improvement all day.'")
        submitted = st.form_submit_button("Analyze Load", type="primary")
        
        if submitted and text_input:
            with st.spinner("Analyzing Life Load..."):
                try:
                    # 1. GENERATE
                    full_prompt = f"{extraction_prompt}\n\nUser Entry: {text_input}"
                    response = model_json.generate_content(full_prompt)
                    
                    # 2. SANITIZE (Crucial Fix for JSON Errors)
                    clean_text = response.text.strip()
                    # Remove potential markdown wrappers
                    if clean_text.startswith("```"):
                        clean_text = clean_text.replace("```json", "").replace("```", "")
                    
                    # 3. PARSE
                    parsed_data = json.loads(clean_text)
                    
                    # 4. TIMESTAMP & SAVE
                    parsed_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.journal_history.insert(0, parsed_data) # Add to top of list
                    
                    # 5. REFRESH
                    st.rerun()
                    
                except Exception as e:
                    # Robust Error Logging
                    logger.error(f"Journal analysis failed: {e}", exc_info=True)
                    st.error(f"Analysis failed. Details: {e}")

    # --- DISPLAY HISTORY ---
    if st.session_state.journal_history:
        latest_entry = st.session_state.journal_history[0]
        
        # 1. The Empathetic Reply
        st.success(f"**Insight:** {latest_entry.get('reply', 'Analysis complete.')}")
        
        # 2. The Load Scoreboard
        s_col1, s_col2, s_col3 = st.columns(3)
        scores = latest_entry.get("scores", {"bio":0, "cog":0, "emo":0})
        
        with s_col1:
            st.metric("🧬 Biological Load", f"{scores['bio']}/10", delta="Physical Stress" if scores['bio'] > 6 else None, delta_color="inverse")
        with s_col2:
            st.metric("🧠 Cognitive Load", f"{scores['cog']}/10", delta="Focus Strain" if scores['cog'] > 6 else None, delta_color="inverse")
        with s_col3:
            st.metric("❤️ Emotional Load", f"{scores['emo']}/10", delta="Allostatic Load" if scores['emo'] > 6 else None, delta_color="inverse")
            
        # 3. Context Tags & Prediction
        tags = latest_entry.get('tags', [])
        st.markdown(f"**🏷️ Drivers:** {' '.join([f'`{t}`' for t in tags])}")
        st.info(f"**📉 Physiological Prediction:** {latest_entry.get('impact_prediction', 'No prediction available.')}")
        
        st.divider()
        
        # Previous Entries Expander
        with st.expander("📜 Previous Downloads"):
            for entry in st.session_state.journal_history[1:]:
                st.markdown(f"**{entry['timestamp']}** - *{entry.get('summary', 'Log')}*")
                scores_prev = entry.get("scores", {"bio":0, "cog":0, "emo":0})
                st.caption(f"Bio: {scores_prev['bio']} | Cog: {scores_prev['cog']} | Emo: {scores_prev['emo']}")
                st.markdown("---")

st.markdown(styles.FOOTER_HTML, unsafe_allow_html=True)