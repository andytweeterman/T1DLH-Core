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
    page_icon="assets/tldh_logo.png",
    layout="wide"
)
styles.apply_theme()

# -----------------------------------------------------------------------------
# 2. INITIALIZE GEMINI CLIENT (2026 PROTOCOL)
# -----------------------------------------------------------------------------
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    try:
        target_model = 'gemini-3-flash-preview'
        test_model = genai.GenerativeModel(target_model)
        test_model.generate_content("Ping") 
        active_model_name = target_model
        model_status = "✨ GEMINI 3.0 FLASH (PREVIEW) ONLINE"
    except Exception:
        active_model_name = 'gemini-1.5-flash'
        model_status = "⚠️ LEGACY FALLBACK: GEMINI 1.5 FLASH"

    model_json = genai.GenerativeModel(
        active_model_name,
        generation_config={"response_mime_type": "application/json"}
    )
except Exception as e:
    st.error(f"⚠️ API Critical Failure: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 3. CONTEXT STATE MANAGEMENT
# -----------------------------------------------------------------------------
if "current_context" not in st.session_state:
    st.session_state.current_context = "Normal"

with st.sidebar:
    st.image("assets/tldh_logo.png", width=100)
    st.header("System Monitor")
    st.caption(f"**AI Engine:**\n{model_status}")
    st.divider()
    st.info("The Hub correlates biological telemetry with lifestyle context to offload cognitive strain.")

# -----------------------------------------------------------------------------
# 4. DATA LOADING
# -----------------------------------------------------------------------------
try:
    with st.spinner("Syncing Health Data..."):
        raw_data = logic.fetch_health_data()
        full_data, status, color_hex, reason = logic.calc_glycemic_risk(raw_data, st.session_state.current_context)
        latest = full_data.iloc[-1]
except Exception as e:
    st.error(f"Data loading failed: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 5. HEADER UI (Unified Control Bar)
# -----------------------------------------------------------------------------
safe_status = html.escape(str(status))
safe_reason = html.escape(str(reason))
safe_color_hex = html.escape(str(color_hex))
safe_context = html.escape(str(st.session_state.current_context))

col_logo, col_text = st.columns([1, 8])
with col_logo:
    try:
        st.image("assets/tldh_logo.png", width=80)
    except:
        st.write("🧬")

with col_text:
    st.markdown(f"""
        <div style="margin-top: 5px;">
            <span style="font-size: 32px; font-weight: 800; background: var(--accent-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Total Life Download Hub</span><br>
            <span style="color: var(--text-secondary); font-weight: 600; font-size: 1.1rem;">Agentic Risk Management Engine</span>
        </div>
    """, unsafe_allow_html=True)

with st.container(border=True):
    p_col1, p_col2, p_col3, p_spacer = st.columns([1.5, 2, 3, 5])
    
    with p_col1:
        st.markdown("<p style='font-weight: 700; color: var(--text-secondary); text-transform: uppercase; font-size: 0.85rem; letter-spacing: 1px; margin-top: 10px;'>Live Status</p>", unsafe_allow_html=True)
    
    with p_col2:
        st.markdown(f'<div class="gov-pill" style="background-color: {safe_color_hex}; color: #000000; width: 100%; text-align: center; margin:0;">{safe_status}</div>', unsafe_allow_html=True)
    
    with p_col3:
        with st.popover(f"CONTEXT: {safe_context.upper()}", use_container_width=True):
            new_ctx = st.radio(
                "Update Activity Context:",
                ["Normal", "Stressed", "Sick", "Exercise", "Travel"],
                index=["Normal", "Stressed", "Sick", "Exercise", "Travel"].index(st.session_state.current_context)
            )
            if st.button("Apply Changes"):
                st.session_state.current_context = new_ctx
                st.rerun()
    
    st.markdown(f"""
        <div style="margin-top: 10px; font-size: 14px; color: var(--text-secondary); font-style: italic; border-left: 3px solid var(--accent-start); padding-left: 10px;">
            Analysis: {safe_reason}
        </div>
    """, unsafe_allow_html=True)

st.divider()

# -----------------------------------------------------------------------------
# 6. NAVIGATION
# -----------------------------------------------------------------------------
if "active_view" not in st.session_state:
    st.session_state.active_view = "Wellness"

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("Wellness", use_container_width=True, type="primary" if st.session_state.active_view == "Wellness" else "secondary"):
        st.session_state.active_view = "Wellness"
        st.rerun()
with c2:
    if st.button("Schedule", use_container_width=True, type="primary" if st.session_state.active_view == "Schedule" else "secondary"):
        st.session_state.active_view = "Schedule"
        st.rerun()
with c3:
    if st.button("Assistant", use_container_width=True, type="primary" if st.session_state.active_view == "Assistant" else "secondary"):
        st.session_state.active_view = "Assistant"
        st.rerun()

st.markdown("---")

# -----------------------------------------------------------------------------
# 7. RENDER VIEWS
# -----------------------------------------------------------------------------
if st.session_state.active_view == "Wellness":
    prev = full_data.iloc[-2]
    cols = st.columns(3)
    cols[0].metric("Blood Sugar (mg/dL)", int(latest['Glucose_Value']), int(latest['Glucose_Value'] - prev['Glucose_Value']))
    cols[1].metric("Trend", latest['Trend'])
    cols[2].metric("Active Insulin", "1.5 U", "-0.2 U")
    st.markdown("---")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=full_data['Timestamp'], y=full_data['Glucose_Value'], mode='lines', line=dict(color='#8B5CF6', width=3)))
    fig.add_hrect(y0=70, y1=180, line_width=0, fillcolor="rgba(166, 218, 149, 0.1)", opacity=0.5)
    fig.add_hline(y=70, line_dash="dash", line_color="#ED8796")
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='gray'), height=400, margin=dict(l=0, r=0, t=30, b=0), yaxis_title="mg/dL")
    st.plotly_chart(fig, use_container_width=True)

elif st.session_state.active_view == "Schedule":
    h1, h2, h3 = st.columns(3)
    card_css = "background-color: var(--card-bg); padding: 20px; border-radius: 20px; border: 1px solid rgba(128, 128, 128, 0.1); box-shadow: var(--card-shadow); text-align: center;"
    
    # Logic for status strings
    t_status = '🟢 SAFE' if st.session_state.current_context != 'Travel' else '🔴 EVALUATE'
    m_status = '🟡 CAUTION' if st.session_state.current_context == 'Stressed' else '🟢 CLEAR'
    
    with h1: 
        st.markdown(f"<div style='{card_css}'><div style='color:var(--text-secondary);font-size:0.8rem;'>1 HOUR</div><div style='font-weight:800;'>{t_status}</div></div>", unsafe_allow_html=True)
    with h2: 
        st.markdown(f"<div style='{card_css}'><div style='color:var(--text-secondary);font-size:0.8rem;'>4 HOURS</div><div style='font-weight:800;'>{m_status}</div></div>", unsafe_allow_html=True)
    with h3: 
        st.markdown(f"<div style='{card_css}'><div style='color:var(--text-secondary);font-size:0.8rem;'>24 HOURS</div><div style='font-weight:800;'>🟢 GOOD</div></div>", unsafe_allow_html=True)

elif st.session_state.active_view == "Assistant":
    st.markdown("### 🧬 Smart Health Companion")
    if "journal_history" not in st.session_state: st.session_state.journal_history = []
    with st.form("journal_form", clear_on_submit=True):
        text_input = st.text_area("Life Download:", placeholder="How are you feeling?")
        if st.form_submit_button("Analyze Load", type="primary") and text_input:
            with st.spinner("Analyzing..."):
                try:
                    prompt = f"Analyze this life download and return JSON with reply, summary, tags, scores (bio, cog, emo), and impact_prediction: {text_input}"
                    response = model_json.generate_content(prompt)
                    clean_text = response.text.strip().replace("```json", "").replace("```", "")
                    parsed = json.loads(clean_text)
                    parsed["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.journal_history.insert(0, parsed)
                    st.rerun()
                except Exception as e: st.error(f"Analysis failed: {e}")
    if st.session_state.journal_history:
        entry = st.session_state.journal_history[0]
        st.success(f"**Insight:** {entry['reply']}")
        sc = entry.get("scores", {"bio":0, "cog":0, "emo":0})
        st.metric("🧬 Physical", f"{sc['bio']}/10")
        st.info(f"**📉 Prediction:** {entry['impact_prediction']}")

st.markdown(styles.FOOTER_HTML, unsafe_allow_html=True)