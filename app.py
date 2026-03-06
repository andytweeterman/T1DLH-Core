import html
import streamlit as st
import plotly.graph_objects as go
import google.generativeai as genai
import styles
import logic
import json
import logging
import whoop
from datetime import datetime
import calendar_sync

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
        generation_config={"response_mime_type": "application/json"},
        system_instruction="Analyze this life download and return JSON with reply, summary, tags, scores (bio, cog, emo), and impact_prediction."
    )
except Exception as e:
    logger.exception(f"API Critical Failure: {e}")
    st.error("⚠️ API Critical Failure. Please check system logs.")
    st.stop()

# -----------------------------------------------------------------------------
# 3. CONTEXT STATE MANAGEMENT
# -----------------------------------------------------------------------------
if "current_context" not in st.session_state:
    st.session_state.current_context = "Normal"

with st.sidebar:
    st.header("System Monitor")
    st.caption(f"**AI Engine:**\n{model_status}")
    st.divider()
    st.info("The Hub correlates biological telemetry with lifestyle context to offload cognitive strain.")

# --- WHOOP AUTH LOGIC ---
if "whoop_token" not in st.session_state:
    st.session_state.whoop_token = None

query_params = st.query_params
if "code" in query_params and not st.session_state.whoop_token:
    with st.spinner("Finalizing Whoop Connection..."):
        auth_code = query_params["code"]
        token_data = whoop.get_access_token(auth_code)
        st.session_state.whoop_token = token_data.get("access_token")
        st.query_params.clear()
        st.rerun()

with st.sidebar:
    st.divider()
    if not st.session_state.whoop_token:
        auth_link = whoop.get_authorization_url()
        st.link_button("🔗 Connect Whoop", auth_link, use_container_width=True, type="primary")
    else:
        st.success("✅ Whoop Connected")
        if st.button("Refresh Biometrics"):
            st.rerun()

# -----------------------------------------------------------------------------
# 4. DATA LOADING
# -----------------------------------------------------------------------------
try:
    with st.spinner("Syncing Health & Schedule Data..."):
        # A. Fetch Whoop Data
        whoop_metrics = None
        if st.session_state.whoop_token:
            whoop_metrics = whoop.fetch_whoop_recovery(st.session_state.whoop_token)
        
        # B. Fetch Schedule Context 
        meeting_count, speaker_mode = calendar_sync.fetch_calendar_context()
        
        # C. Fetch Dexcom/Health Data
        raw_data = logic.fetch_health_data()
        
        # D. Calculate Risk 
        full_data, status, color_hex, reason = logic.calc_glycemic_risk(
            raw_data, 
            st.session_state.current_context,
            whoop_data=whoop_metrics,
            meeting_count=meeting_count,
            speaker_mode=speaker_mode
        )
        latest = full_data.iloc[-1]
except KeyError as e:
    logger.exception(f"Data loading failed (missing columns): {e}")
    status = "DATA ERROR"
    color_hex = "#EF4444"
    reason = "Missing expected data columns."
except Exception as e:
    logger.exception(f"Data loading failed: {e}")
    status = "SYSTEM ERROR"
    color_hex = "#EF4444"
    reason = "A system error occurred during data loading."

# -----------------------------------------------------------------------------
# 5. HEADER UI (Clean & Text-Only)
# -----------------------------------------------------------------------------
safe_status = html.escape(str(status))
safe_reason = html.escape(str(reason)) 
safe_color_hex = html.escape(str(color_hex))
safe_context = html.escape(str(st.session_state.current_context))

st.markdown(f"""
    <div style="margin-top: 5px; margin-bottom: 20px;">
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
                ["Normal", "Stressed", "Sick", "Exercise", "Project", "Travel"],
                index=["Normal", "Stressed", "Sick", "Exercise", "Project", "Travel"].index(st.session_state.current_context)
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

c1, c2, c3, c4 = st.columns(4)
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
with c4:
    if st.button("Sleep", use_container_width=True, type="primary" if st.session_state.active_view == "Sleep" else "secondary"):
        st.session_state.active_view = "Sleep"
        st.rerun()
st.markdown("---")

# -----------------------------------------------------------------------------
# 7. RENDER VIEWS
# -----------------------------------------------------------------------------

# --- VIEW A: WELLNESS ---
if st.session_state.active_view == "Wellness":
    prev = full_data.iloc[-2]
    
    # ROW 1: Metabolic Telemetry (Dexcom Only)
    st.markdown("#### 🧬 Metabolic Baseline")
    
    # Changed from 3 columns to 2 to scrub the IOB placeholder
    cols_dex = st.columns(2)
    cols_dex[0].metric("Blood Sugar (mg/dL)", int(latest['Glucose_Value']), int(latest['Glucose_Value'] - prev['Glucose_Value']))
    cols_dex[1].metric("Trend", latest['Trend'])
    # REMOVED: cols_dex[2].metric("Active Insulin", "1.5 U", "-0.2 U")

    # ROW 2: Systemic Resilience (Whoop)
    if st.session_state.whoop_token and whoop_metrics:
        st.markdown("#### ⚡ Systemic Resilience")
        cols_whoop = st.columns(3)
        recovery_val = whoop_metrics.get('score', {}).get('recovery_score', 0)
        hrv_val = int(whoop_metrics.get('score', {}).get('hrv_rmssd_milli_seconds', 0))
        rhr_val = int(whoop_metrics.get('score', {}).get('resting_heart_rate_beats_per_minute', 0))
        rec_color = "normal" if recovery_val > 66 else "inverse" if recovery_val < 34 else "off"
        
        cols_whoop[0].metric("Recovery Score", f"{recovery_val}%", delta=None, delta_color=rec_color)
        cols_whoop[1].metric("HRV (ms)", hrv_val)
        cols_whoop[2].metric("Resting HR", rhr_val, delta_color="inverse")
    else:
        st.info("🔗 Connect Whoop in the sidebar to view real-time Resilience metrics.")

    st.markdown("---")
    
    # Universal Radio Toggle instead of segmented_control
    time_window = st.radio(
        "Time Range", 
        options=["3h", "6h", "12h", "24h"], 
        index=1,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    row_mapping = {"3h": 36, "6h": 72, "12h": 144, "24h": 288}
    plot_data = full_data.tail(row_mapping[time_window])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plot_data['Timestamp'], y=plot_data['Glucose_Value'], mode='lines', line=dict(color='#8B5CF6', width=3)))
    fig.add_hrect(y0=70, y1=180, line_width=0, fillcolor="rgba(166, 218, 149, 0.1)", opacity=0.5)
    fig.add_hline(y=70, line_dash="dash", line_color="#ED8796", annotation_text="LOW GATES")
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='gray'),
        height=400, 
        margin=dict(l=0, r=0, t=30, b=0), 
        yaxis_title="mg/dL",
        xaxis=dict(fixedrange=True),
        yaxis=dict(fixedrange=True)
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# --- VIEW B: SCHEDULE ---
elif st.session_state.active_view == "Schedule":
    st.markdown("### 🗓️ Cognitive Load & Schedule Density")
    
    h1, h2, h3, h4 = st.columns(4)
    card_css = "background-color: var(--card-bg); padding: 20px; border-radius: 20px; border: 1px solid rgba(128, 128, 128, 0.1); box-shadow: var(--card-shadow); text-align: center;"
    
    # ERM-style status strings
    # Adjusted to recognize Travel as an active advisory state, not an error
    t_status = '🟢 SAFE'
    if st.session_state.current_context == 'Travel':
        t_status = '✈️ SHIFTING'
        
    m_status = '🟡 CAUTION' if st.session_state.current_context == 'Stressed' else '🟢 CLEAR'
    
    # MEETING DENSITY LOGIC (The new "Jules" Metric)
    # We grab 'meeting_count' which was defined in Section 4 (Data Loading)
    density_label = "🟢 LIGHT"
    if meeting_count >= 7:
        density_label = "🔴 CRITICAL"
    elif meeting_count >= 4:
        density_label = "🟡 ELEVATED"

    with h1: 
        st.markdown(f"<div style='{card_css}'><div style='color:var(--text-secondary);font-size:0.8rem;'>1 HOUR</div><div style='font-weight:800;'>{t_status}</div></div>", unsafe_allow_html=True)
    with h2: 
        st.markdown(f"<div style='{card_css}'><div style='color:var(--text-secondary);font-size:0.8rem;'>4 HOURS</div><div style='font-weight:800;'>{m_status}</div></div>", unsafe_allow_html=True)
    with h3: 
        st.markdown(f"<div style='{card_css}'><div style='color:var(--text-secondary);font-size:0.8rem;'>24 HOURS</div><div style='font-weight:800;'>🟢 GOOD</div></div>", unsafe_allow_html=True)
    with h4:
        st.markdown(f"<div style='{card_css}'><div style='color:var(--text-secondary);font-size:0.8rem;'>MEETINGS</div><div style='font-weight:800;'>{meeting_count} ({density_label})</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.info(f"**Agentic Insight:** The Risk Engine is currently factoring in **{meeting_count} meetings** over the next 8 hours to adjust your glycemic sensitivity threshold.")

# --- VIEW C: ASSISTANT ---
elif st.session_state.active_view == "Assistant":
    st.markdown("### 🧬 Smart Health Companion")
    if "journal_history" not in st.session_state: st.session_state.journal_history = []
    with st.form("journal_form", clear_on_submit=True):
        text_input = st.text_area("Life Download:", placeholder="How are you feeling?")
        if st.form_submit_button("Analyze Load", type="primary") and text_input:
            with st.spinner("Analyzing..."):
                try:
                    response = model_json.generate_content(text_input)
                    clean_text = response.text.strip().replace("```json", "").replace("```", "")
                    parsed = json.loads(clean_text)
                    parsed["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.journal_history.insert(0, parsed)
                    st.rerun()
                except Exception as e:
                    logger.exception(f"Analysis failed: {e}")
                    st.error("Analysis failed. Please try again.")
    if st.session_state.journal_history:
        entry = st.session_state.journal_history[0]
        st.success(f"**Insight:** {entry['reply']}")
        sc = entry.get("scores", {"bio":0, "cog":0, "emo":0})
        st.metric("🧬 Physical", f"{sc['bio']}/10")
        st.info(f"**📉 Prediction:** {entry['impact_prediction']}")

# --- VIEW D: SLEEP IMPACT ---
elif st.session_state.active_view == "Sleep":
    st.markdown("### 🌙 Sleep & Recovery Correlation")
    if st.session_state.whoop_token and whoop_metrics:
        sleep_perf = whoop_metrics.get('score', {}).get('sleep_performance_percentage', 85)
        overnight_df = full_data.tail(96)
        std_dev = int(overnight_df['Glucose_Value'].std())
        
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            st.metric("Sleep Performance", f"{sleep_perf}%", delta="Restorative" if sleep_perf > 80 else "Deficit", delta_color="normal" if sleep_perf > 80 else "inverse")
        with s_col2:
            st.metric("Overnight Volatility", f"±{std_dev} mg/dL", delta="Stable" if std_dev < 15 else "Erratic", delta_color="normal" if std_dev < 15 else "inverse")

        st.markdown("---")
        st.markdown("#### Overnight Stability Trend")
        sleep_fig = go.Figure()
        sleep_fig.add_trace(go.Scatter(x=overnight_df['Timestamp'], y=overnight_df['Glucose_Value'], mode='lines+markers', line=dict(color='#A855F7', width=4)))
        sleep_fig.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='gray'))
        st.plotly_chart(sleep_fig, use_container_width=True)
        
        if std_dev > 20 and sleep_perf < 70:
            st.warning("⚠️ **Agentic Insight:** High volatility detected. Consider a +20% basal temporary increase.")
        else:
            st.success("✅ **Agentic Insight:** Stable overnight metabolic state.")
    else:
        st.info("🔗 Connect Whoop to enable Sleep Impact correlation.")

st.markdown(styles.FOOTER_HTML, unsafe_allow_html=True)