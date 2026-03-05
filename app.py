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
st.set_page_config(
    page_title="TLDH | Total Life Download Hub", 
    page_icon="assets/tldh_logo.png", # Points to your image
    layout="wide"
)
styles.apply_theme()  # Injects auto-switching CSS variables

# -----------------------------------------------------------------------------
# 2. INITIALIZE GEMINI CLIENT (2026 PROTOCOL)
# -----------------------------------------------------------------------------
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    try:
        # TARGET STATE: March 2026 Architecture
        target_model = 'gemini-3-flash-preview'
        test_model = genai.GenerativeModel(target_model)
        test_model.generate_content("Ping") 
        active_model_name = target_model
        model_status = "✨ GEMINI 3.0 FLASH (PREVIEW) ONLINE"
        
    except Exception:
        # FALLBACK STATE: Legacy Architecture (Safety Net)
        active_model_name = 'gemini-1.5-flash'
        model_status = "⚠️ LEGACY FALLBACK: GEMINI 1.5 FLASH"

    model_text = genai.GenerativeModel(active_model_name)
    model_json = genai.GenerativeModel(
        active_model_name,
        generation_config={"response_mime_type": "application/json"}
    )
    
except Exception as e:
    st.error(f"⚠️ API Critical Failure: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 3. CONTEXT SIDEBAR
# -----------------------------------------------------------------------------
# We now offer a popover for the main screen, in addition to the sidebar
with st.popover("⚙️ Current Context"):
    current_context = st.radio(
        "Select Activity",
        ["Normal", "Stressed", "Sick", "Exercise", "Travel"],
        index=0
    )

# Optionally, keep the sidebar as a secondary redundancy
with st.sidebar:
    st.header("Context Settings")
    current_context_sidebar = st.selectbox(
        "Current Activity",
        ["Normal", "Stressed", "Sick", "Exercise", "Travel"],
        index=0
    )
    # Sync them up
    current_context = current_context_sidebar
    st.markdown("---")
    st.caption(f"**AI Engine:**\n{model_status}")

# -----------------------------------------------------------------------------
# 4. DATA LOADING
# -----------------------------------------------------------------------------
try:
    with st.spinner("Syncing Health Data..."):
        raw_data = logic.fetch_health_data()
        full_data, status, color_hex, reason = logic.calc_glycemic_risk(raw_data, current_context)
        latest = full_data.iloc[-1]
except Exception as e:
    logger.error(f"Data loading failed: {e}", exc_info=True)
    st.error("Oops! Something went wrong loading your health data.")
    st.stop()

# -----------------------------------------------------------------------------
# 5. HEADER UI (Branded)
# -----------------------------------------------------------------------------
safe_status = html.escape(str(status))
safe_reason = html.escape(str(reason))
safe_color_hex = html.escape(str(color_hex))

# Inject Logo & Title layout
col_logo, col_text = st.columns([1, 8])
with col_logo:
    try:
        st.image("assets/tldh_logo.png", width=80)
    except Exception:
        st.error("Logo missing")

with col_text:
    st.markdown(f"""
        <div style="margin-top: 5px;">
            <span style="font-size: 32px; font-weight: 800; background: var(--accent-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Total Life Download Hub</span><br>
            <span style="color: var(--text-secondary); font-weight: 600; font-size: 1.1rem;">Agentic Risk Management Engine</span>
        </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
    <div style="margin-top: 25px; margin-bottom: 20px;">
        <span style="font-weight: 600; color: var(--text-secondary);">Current Status: </span>
        <div class="gov-pill" style="background-color: {safe_color_hex}; color: #000000;">{safe_status}</div>
        <div style="margin-top: 5px; font-size: 14px; color: var(--text-secondary);">Analysis: {safe_reason}</div>
    </div>
""", unsafe_allow_html=True)

st.divider()

# -----------------------------------------------------------------------------
# 6. NAVIGATION
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

# --- VIEW A: WELLNESS ---
if st.session_state.active_view == "Wellness":
    prev = full_data.iloc[-2]
    cols = st.columns(3)
    cols[0].metric("Blood Sugar (mg/dL)", int(latest['Glucose_Value']), int(latest['Glucose_Value'] - prev['Glucose_Value']))
    cols[1].metric("Trend", latest['Trend'])
    cols[2].metric("Active Insulin", "1.5 U", "-0.2 U")

    st.markdown("---")
    
    fig = go.Figure()
    # UPDATED LINE COLOR TO MATCH BRANDING (#8B5CF6 - Indigo/Purple)
    fig.add_trace(go.Scatter(x=full_data['Timestamp'], y=full_data['Glucose_Value'], mode='lines', line=dict(color='#8B5CF6', width=3)))
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

# --- VIEW B: SCHEDULE ---
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

# --- VIEW C: ASSISTANT ---
elif st.session_state.active_view == "Assistant":
    st.markdown("### 🧬 Smart Health Companion")
    st.caption("Log unstructured thoughts to track Physical, Mental, and Emotional load.")

    extraction_prompt = """
    **ROLE:** You are the Total Life Download Analyst. 
    **GOAL:** The user will provide unstructured "downloads".
    
    **YOUR TASK:**
    1. **Validate:** Offer a brief, 1-sentence empathetic acknowledgement in the "reply" field.
    2. **Structure:** Convert the qualitative text into a strict JSON data object that tracks "Life Load".
    
    **SCORING FRAMEWORK (1-10 Scale):**
    * **Bio:** Physical stress, illness, high blood sugar, poor sleep.
    * **Cog:** Deep work, studying, strategic planning, decision fatigue.
    * **Emo:** Family dynamics, anxiety, excitement, frustration.
    
    **OUTPUT FORMAT (Strict JSON):**
    {
        "reply": "Empathetic response string here.",
        "summary": "5-word summary",
        "tags": ["Tag1", "Tag2"],
        "scores": { "bio": 5, "cog": 5, "emo": 5 },
        "impact_prediction": "Prediction on physiology."
    }
    """

    if "journal_history" not in st.session_state:
        st.session_state.journal_history = []

    with st.form("journal_form", clear_on_submit=True):
        text_input = st.text_area("Life Download:", placeholder="e.g. 'Stressed about work plan, but wife is home...'")
        submitted = st.form_submit_button("Analyze Load", type="primary")
        
        if submitted and text_input:
            with st.spinner("Analyzing Life Load..."):
                try:
                    full_prompt = f"{extraction_prompt}\n\nUser Entry: {text_input}"
                    
                    response = model_json.generate_content(full_prompt)
                    
                    clean_text = response.text.strip()
                    if clean_text.startswith("```"):
                        clean_text = clean_text.replace("```json", "").replace("```", "")
                    
                    parsed_data = json.loads(clean_text)
                    parsed_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.journal_history.insert(0, parsed_data)
                    st.rerun()
                    
                except Exception as e:
                    logger.error(f"Journal analysis failed: {e}", exc_info=True)
                    st.error(f"Analysis failed. Error: {e}")

    if st.session_state.journal_history:
        latest_entry = st.session_state.journal_history[0]
        st.success(f"**Insight:** {latest_entry.get('reply', 'Analysis complete.')}")
        
        s_col1, s_col2, s_col3 = st.columns(3)
        scores = latest_entry.get("scores", {"bio":0, "cog":0, "emo":0})
        
        with s_col1:
            st.metric("🧬 Physical Load", f"{scores['bio']}/10", delta="Physical Stress" if scores['bio'] > 6 else None, delta_color="inverse")
        with s_col2:
            st.metric("🧠 Mental Load", f"{scores['cog']}/10", delta="Focus Strain" if scores['cog'] > 6 else None, delta_color="inverse")
        with s_col3:
            st.metric("❤️ Emotional Load", f"{scores['emo']}/10", delta="Emotional Strain" if scores['emo'] > 6 else None, delta_color="inverse")
            
        tags = latest_entry.get('tags', [])
        st.markdown(f"**🏷️ Drivers:** {' '.join([f'`{t}`' for t in tags])}")
        st.info(f"**📉 Physiological Prediction:** {latest_entry.get('impact_prediction', 'No prediction available.')}")
        
        st.divider()
        
        with st.expander("📜 Previous Downloads"):
            for entry in st.session_state.journal_history[1:]:
                st.markdown(f"**{entry['timestamp']}** - *{entry.get('summary', 'Log')}*")
                scores_prev = entry.get("scores", {"bio":0, "cog":0, "emo":0})
                st.caption(f"Bio: {scores_prev['bio']} | Cog: {scores_prev['cog']} | Emo: {scores_prev['emo']}")
                st.markdown("---")

st.markdown(styles.FOOTER_HTML, unsafe_allow_html=True)