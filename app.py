import html
import streamlit as st
import plotly.graph_objects as go
import google.generativeai as genai
import styles
import logic
import json
import logging
import whoop
import hashlib
from datetime import datetime
import calendar_sync
from audio_recorder_streamlit import audio_recorder

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
        active_model_name = 'gemini-2.0-flash'
        model_status = "⚡ PRODUCTION: GEMINI 2.0 FLASH ONLINE"

    model_json = genai.GenerativeModel(
        active_model_name,
        generation_config={"response_mime_type": "application/json"}
    )
except Exception as e:
    st.error("⚠️ API Critical Failure. Please check system logs.")
    st.stop()

# -----------------------------------------------------------------------------
# 3. CONTEXT STATE & AUTH LOGIC
# -----------------------------------------------------------------------------
if "current_context" not in st.session_state:
    st.session_state.current_context = "Normal"

# 1. Initialize the state variable FIRST
if "whoop_token" not in st.session_state:
    st.session_state.whoop_token = None

# 2. Try to get a valid token from the vault silently
if not st.session_state.whoop_token:
    st.session_state.whoop_token = whoop.get_valid_access_token()

# 3. If the vault is empty, check if we are returning from a manual login
if "code" in st.query_params and not st.session_state.whoop_token:
    with st.spinner("Finalizing Whoop Connection..."):
        query_state = st.query_params.get("state")
        session_state = st.session_state.get("oauth_state")

        if query_state and session_state and query_state == session_state:
            auth_code = st.query_params["code"]
            token_data = whoop.get_access_token(auth_code)

            # Safety check: ensure Whoop actually returned a token
            if token_data and "access_token" in token_data:
                st.session_state.whoop_token = token_data.get("access_token")
                whoop.save_tokens(token_data) # Save it to the vault!
                st.query_params.clear() # Scrub the URL clean
                st.rerun()
            else:
                st.error("Whoop Auth Failed. Please try again.")
        else:
            st.error("Invalid or missing state parameter. Authentication failed.")
            st.query_params.clear()

# -----------------------------------------------------------------------------
# 4. DATA LOADING
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300) # Cache simulation for 5 minutes
def get_cached_health_data():
    return logic.fetch_health_data()

@st.cache_data(ttl=60) # Cache risk state for 1 minute
def get_cached_glycemic_risk(df, context, whoop_data=None, meeting_count=0, speaker_mode=False):
    return logic.calc_glycemic_risk(df, context, whoop_data, meeting_count, speaker_mode)

try:
    with st.spinner("Syncing Health & Schedule Data..."):
        # A. Fetch Whoop Data
        whoop_metrics = None
        if st.session_state.whoop_token:
            whoop_metrics = whoop.fetch_whoop_recovery(st.session_state.whoop_token)
        
        # B. Fetch Schedule Context 
        meeting_count, speaker_mode = calendar_sync.fetch_calendar_context()
        
        # C. Fetch Dexcom/Health Data
        raw_data = get_cached_health_data()
        
        # D. Calculate Risk 
        full_data, status, color_hex, reason = get_cached_glycemic_risk(
            raw_data, 
            st.session_state.current_context,
            whoop_data=whoop_metrics,
            meeting_count=meeting_count,
            speaker_mode=speaker_mode
        )
        latest = full_data.iloc[-1]
except Exception as e:
    st.error("Data loading failed. Please try again.")

# -----------------------------------------------------------------------------
# 5. HEADER UI & HAMBURGER MENU
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
    p_col1, p_col2, p_col3, p_col4 = st.columns([1.5, 2.5, 3, 1.5])
    
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
                
    with p_col4:
        # Hamburger Menu Popover
        with st.popover("☰ MENU", use_container_width=True):
            st.markdown("##### 🔌 Integrations")
            
            # 1. Whoop Sync Logic inside the menu
            if not st.session_state.whoop_token:
                auth_link = whoop.get_authorization_url()
                st.link_button("🔗 Connect Whoop", auth_link, use_container_width=True)
            else:
                if st.button("✅ Whoop Synced", use_container_width=True):
                    st.rerun() 
            
            st.divider()
            
            # 2. Clinical Export Logic inside the menu
            st.markdown("##### 🖨️ Export")
            try:
                avg_glucose = int(full_data['Glucose_Value'].mean())
                std_dev = int(full_data['Glucose_Value'].std())
                
                w_rec = whoop_metrics.get('score', {}).get('recovery_score', 0) if whoop_metrics else 0
                w_sleep = whoop_metrics.get('score', {}).get('sleep_performance_percentage', 0) if whoop_metrics else 0
                w_strain = round(whoop_metrics.get('score', {}).get('day_strain', 0.0), 1) if whoop_metrics else 0.0
                
                clinical_snapshot = {
                    "export_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "active_context": st.session_state.current_context,
                    "schedule_load": {
                        "meetings_next_8h": meeting_count,
                        "weekend_window_active": logic.is_weekend_window()
                    },
                    "metabolic_telemetry_24h": {
                        "current_glucose_mgdl": int(latest['Glucose_Value']),
                        "trend_velocity": latest['Trend'],
                        "average_glucose_mgdl": avg_glucose,
                        "standard_deviation": std_dev
                    },
                    "systemic_resilience": {
                        "whoop_recovery_pct": w_rec,
                        "whoop_sleep_perf_pct": w_sleep,
                        "whoop_day_strain": w_strain
                    }
                }
                json_export = json.dumps(clinical_snapshot, indent=4)
                
                st.download_button(
                    label="📥 Download JSON",
                    data=json_export,
                    file_name=f"TLDH_Clinical_Snapshot_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            except Exception:
                st.warning("Awaiting full data sync...")
    
    st.markdown(f"""
        <div style="margin-top: 10px; font-size: 14px; color: var(--text-secondary); font-style: italic; border-left: 3px solid var(--accent-start); padding-left: 10px;">
            Analysis: {safe_reason}
        </div>
    """, unsafe_allow_html=True)

st.divider()

# -----------------------------------------------------------------------------
# 5.5 VOICE ASSISTANT (GLOBAL PERSISTENT UI)
# -----------------------------------------------------------------------------
st.markdown("### 🎙️ Agentic Voice Dump")
st.caption("Tap the mic to log an unstructured voice note. The AI will instantly correlate it with your live biology.")

v_col1, v_col2 = st.columns([1, 10])
with v_col1:
    audio_bytes = audio_recorder(
        text="",
        recording_color="#ED8796",
        neutral_color="#8B5CF6",
        icon_size="2x"
    )

if audio_bytes:
    # Hash the bytes to prevent Streamlit from constantly re-processing the same audio on every interaction
    audio_hash = hashlib.md5(audio_bytes).hexdigest()
    
    if audio_hash != st.session_state.get("last_audio_hash"):
        st.session_state.last_audio_hash = audio_hash
        
        with st.spinner("Processing Voice Dump and Correlating Telemetry..."):
            try:
                avg_glucose = int(full_data['Glucose_Value'].mean())
                std_dev = int(full_data['Glucose_Value'].std())
                w_rec = whoop_metrics.get('score', {}).get('recovery_score', 0) if whoop_metrics else 0
                w_sleep = whoop_metrics.get('score', {}).get('sleep_performance_percentage', 0) if whoop_metrics else 0
                w_strain = round(whoop_metrics.get('score', {}).get('day_strain', 0.0), 1) if whoop_metrics else 0.0
                
                live_context = {
                    "active_context": st.session_state.current_context,
                    "meetings_next_8h": meeting_count,
                    "is_weekend_window": logic.is_weekend_window(),
                    "current_glucose": int(latest['Glucose_Value']),
                    "glucose_trend": latest['Trend'],
                    "glucose_volatility_std_dev": std_dev,
                    "whoop_recovery": w_rec,
                    "whoop_sleep": w_sleep,
                    "whoop_day_strain": w_strain
                }
                
                system_instruction = f"""
                You are an elite clinical AI assistant managing a high-performer's physiological and cognitive load.
                Here is the user's real-time hardware telemetry: {json.dumps(live_context)}
                
                The user will provide an audio brain dump. Listen to the audio and correlate their subjective state with their objective telemetry.
                Return a valid JSON object with EXACTLY these keys:
                - "reply": "A highly actionable, context-aware response under 40 words. No medical jargon."
                - "summary": "A 3-word summary."
                - "scores": {"bio_strain": 5, "cog_load": 5}
                - "impact_prediction": "A 1-sentence prediction of how their current state and telemetry will impact their glucose over the next 2 hours."
                """
                
                secure_model = genai.GenerativeModel(
                    active_model_name,
                    system_instruction=system_instruction,
                    generation_config={"response_mime_type": "application/json"}
                )

                # Bundle the text prompt and raw audio bytes natively into Gemini
                audio_part = {
                    "mime_type": "audio/wav",
                    "data": audio_bytes
                }
                
                response = secure_model.generate_content([audio_part])
                clean_text = response.text.strip()
                
                markdown_fence = chr(96) * 3
                clean_text = clean_text.replace(f"{markdown_fence}json", "").replace(markdown_fence, "").strip()
                
                parsed = json.loads(clean_text)
                parsed["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                if "journal_history" not in st.session_state: 
                    st.session_state.journal_history = []
                st.session_state.journal_history.insert(0, parsed)
                
                # Auto-switch to the Assistant tab so they can see the generated insight
                st.session_state.active_view = "Assistant"
                st.rerun()
            except Exception as e:
                st.error("Voice Analysis failed. Please try again.")

st.divider()

# -----------------------------------------------------------------------------
# 6. NAVIGATION
# -----------------------------------------------------------------------------
if "active_view" not in st.session_state:
    st.session_state.active_view = "Daily Briefing"

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    if st.button("Daily Briefing", use_container_width=True, type="primary" if st.session_state.active_view == "Daily Briefing" else "secondary"):
        st.session_state.active_view = "Daily Briefing"
        st.rerun()
with c2:
    if st.button("Wellness", use_container_width=True, type="primary" if st.session_state.active_view == "Wellness" else "secondary"):
        st.session_state.active_view = "Wellness"
        st.rerun()
with c3:
    if st.button("Schedule", use_container_width=True, type="primary" if st.session_state.active_view == "Schedule" else "secondary"):
        st.session_state.active_view = "Schedule"
        st.rerun()
with c4:
    if st.button("Assistant", use_container_width=True, type="primary" if st.session_state.active_view == "Assistant" else "secondary"):
        st.session_state.active_view = "Assistant"
        st.rerun()
with c5:
    if st.button("Sleep", use_container_width=True, type="primary" if st.session_state.active_view == "Sleep" else "secondary"):
        st.session_state.active_view = "Sleep"
        st.rerun()
st.markdown("---")

# -----------------------------------------------------------------------------
# 7. RENDER VIEWS
# -----------------------------------------------------------------------------

# --- VIEW: DAILY BRIEFING (BLUF) ---
if st.session_state.active_view == "Daily Briefing":
    st.markdown("### 📋 Executive Daily Briefing")
    st.markdown("A tactical synthesis of your readiness, load, and biology.")

    with st.spinner("Compiling Executive Briefing..."):
        try:
            bg_val = int(latest['Glucose_Value'])
            trend = latest['Trend']

            rec_score, sleep_perf, strain = "Unknown", "Unknown", "Unknown"
            if st.session_state.whoop_token and whoop_metrics:
                rec_score = whoop_metrics.get('score', {}).get('recovery_score', "Unknown")
                sleep_perf = whoop_metrics.get('score', {}).get('sleep_performance_percentage', "Unknown")
                strain = round(whoop_metrics.get('score', {}).get('day_strain', 0.0), 1)

            is_weekend = logic.is_weekend_window()
            day_type = "Weekend / Recharge Day" if is_weekend else "Standard Workday"

            system_instruction = f"""
            You are an executive performance coach. Write a daily briefing based on these metrics:
            - Day Type: {day_type}
            - Schedule Density: {meeting_count} meetings.
            - Whoop Metrics: {rec_score}% Recovery, {sleep_perf}% Sleep, {strain} Day Strain.
            - Current Glucose: {bg_val} mg/dL, Trend: {trend}.
            - Active Context: {st.session_state.current_context}
            """

            briefing_model = genai.GenerativeModel(
                active_model_name,
                generation_config={"response_mime_type": "application/json"},
                system_instruction=system_instruction
            )

            response = briefing_model.generate_content("Generate the executive daily briefing now.")
            clean_text = response.text.strip()
            
            # Replaced the .startswith method with safe replacement to avoid parser cutoff
            markdown_fence = chr(96) * 3
            clean_text = clean_text.replace(f"{markdown_fence}json", "").replace(markdown_fence, "").strip()
            
            briefing_data = json.loads(clean_text)

            st.info(f"**1. Load & Resilience:** {html.escape(briefing_data.get('bullet_1', ''))}")
            st.warning(f"**2. Metabolic State:** {html.escape(briefing_data.get('bullet_2', ''))}")
            st.success(f"**3. Recommended Action:** {html.escape(briefing_data.get('bullet_3', ''))}")

        except Exception as e:
            st.error("Failed to generate briefing. Please check API connection.")

# --- VIEW A: WELLNESS ---
elif st.session_state.active_view == "Wellness":
    prev = full_data.iloc[-2]
    
    st.markdown("#### 🧬 Metabolic Baseline")
    cols_dex = st.columns(2)
    cols_dex[0].metric("Blood Sugar (mg/dL)", int(latest['Glucose_Value']), int(latest['Glucose_Value'] - prev['Glucose_Value']))
    cols_dex[1].metric("Trend", latest['Trend'])

    if st.session_state.whoop_token and whoop_metrics:
        st.markdown("#### ⚡ Systemic Resilience")
        cols_whoop = st.columns(5)
        
        recovery_val = whoop_metrics.get('score', {}).get('recovery_score', 0)
        hrv_val = int(whoop_metrics.get('score', {}).get('hrv_rmssd_milli_seconds', 0))
        rhr_val = int(whoop_metrics.get('score', {}).get('resting_heart_rate_beats_per_minute', 0))
        strain_val = round(whoop_metrics.get('score', {}).get('day_strain', 0.0), 1)
        sleep_val = whoop_metrics.get('score', {}).get('sleep_performance_percentage', 0)
        
        rec_color = "normal" if recovery_val > 66 else "inverse" if recovery_val < 34 else "off"
        sleep_color = "normal" if sleep_val > 85 else "inverse" if sleep_val < 70 else "off"
        
        cols_whoop[0].metric("Recovery", f"{recovery_val}%", delta=None, delta_color=rec_color)
        cols_whoop[1].metric("Sleep Perf", f"{sleep_val}%", delta=None, delta_color=sleep_color)
        cols_whoop[2].metric("Day Strain", f"{strain_val}")
        cols_whoop[3].metric("HRV (ms)", hrv_val)
        cols_whoop[4].metric("Resting HR", rhr_val, delta_color="inverse")
    else:
        st.info("🔗 Open the ☰ MENU above to connect Whoop and view live resilience metrics.")
    
    time_window = st.radio("Time Range", ["3h", "6h", "12h", "24h"], index=1, horizontal=True, label_visibility="collapsed")
    row_mapping = {"3h": 36, "6h": 72, "12h": 144, "24h": 288}
    plot_data = full_data.tail(row_mapping[time_window])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plot_data['Timestamp'], y=plot_data['Glucose_Value'], mode='lines', line=dict(color='#8B5CF6', width=3)))
    fig.add_hrect(y0=70, y1=180, line_width=0, fillcolor="rgba(166, 218, 149, 0.1)", opacity=0.5)
    fig.add_hline(y=70, line_dash="dash", line_color="#ED8796", annotation_text="LOW GATES")
    
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='gray'), height=400, margin=dict(l=0, r=0, t=30, b=0), yaxis_title="mg/dL", xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# --- VIEW B: SCHEDULE ---
elif st.session_state.active_view == "Schedule":
    st.markdown("### 🗓️ Cognitive Load & Schedule Density")
    h1, h2, h3, h4 = st.columns(4)
    card_css = "background-color: var(--card-bg); padding: 20px; border-radius: 20px; border: 1px solid rgba(128, 128, 128, 0.1); box-shadow: var(--card-shadow); text-align: center;"
    
    t_status = '✈️ SHIFTING' if st.session_state.current_context == 'Travel' else '🟢 SAFE'
    m_status = '🟡 CAUTION' if st.session_state.current_context == 'Stressed' else '🟢 CLEAR'
    
    density_label = "🟢 LIGHT"
    if meeting_count >= 7: density_label = "🔴 CRITICAL"
    elif meeting_count >= 4: density_label = "🟡 ELEVATED"

    with h1: st.markdown(f"<div style='{card_css}'><div style='color:var(--text-secondary);font-size:0.8rem;'>1 HOUR</div><div style='font-weight:800;'>{t_status}</div></div>", unsafe_allow_html=True)
    with h2: st.markdown(f"<div style='{card_css}'><div style='color:var(--text-secondary);font-size:0.8rem;'>4 HOURS</div><div style='font-weight:800;'>{m_status}</div></div>", unsafe_allow_html=True)
    with h3: st.markdown(f"<div style='{card_css}'><div style='color:var(--text-secondary);font-size:0.8rem;'>24 HOURS</div><div style='font-weight:800;'>🟢 GOOD</div></div>", unsafe_allow_html=True)
    with h4: st.markdown(f"<div style='{card_css}'><div style='color:var(--text-secondary);font-size:0.8rem;'>MEETINGS</div><div style='font-weight:800;'>{meeting_count} ({density_label})</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.info(f"**Agentic Insight:** The Risk Engine is currently factoring in **{meeting_count} meetings** over the next 8 hours to adjust your glycemic sensitivity threshold.")

# --- VIEW C: ASSISTANT ---
elif st.session_state.active_view == "Assistant":
    st.markdown("### 🧬 Smart Health Companion")
    st.markdown("Ask a question or log how you are feeling. The AI will correlate your input with your live telemetry.")
    
    if "journal_history" not in st.session_state: st.session_state.journal_history = []
    
    with st.form("journal_form", clear_on_submit=True):
        text_input = st.text_area("Life Download (Text Fallback):", placeholder="E.g., 'Just finished rebuilding the deck doors. Legs feel heavy.'")
        
        if st.form_submit_button("Analyze Correlation", type="primary") and text_input:
            with st.spinner("Correlating subjective report with objective telemetry..."):
                try:
                    avg_glucose = int(full_data['Glucose_Value'].mean())
                    std_dev = int(full_data['Glucose_Value'].std())
                    w_rec = whoop_metrics.get('score', {}).get('recovery_score', 0) if whoop_metrics else 0
                    w_sleep = whoop_metrics.get('score', {}).get('sleep_performance_percentage', 0) if whoop_metrics else 0
                    w_strain = round(whoop_metrics.get('score', {}).get('day_strain', 0.0), 1) if whoop_metrics else 0.0
                    
                    live_context = {
                        "active_context": st.session_state.current_context,
                        "meetings_next_8h": meeting_count,
                        "is_weekend_window": logic.is_weekend_window(),
                        "current_glucose": int(latest['Glucose_Value']),
                        "glucose_trend": latest['Trend'],
                        "glucose_volatility_std_dev": std_dev,
                        "whoop_recovery": w_rec,
                        "whoop_sleep": w_sleep,
                        "whoop_day_strain": w_strain
                    }
                    
                    system_instruction = f"""
                    You are an elite clinical AI assistant managing a high-performer's physiological and cognitive load.
                    Here is the user's real-time hardware telemetry: {json.dumps(live_context)}
                    
                    Correlate their subjective report with their objective telemetry. 
                    Return a valid JSON object with EXACTLY these keys:
                    - "reply": "A highly actionable, context-aware response under 40 words. No medical jargon."
                    - "summary": "A 3-word summary."
                    - "scores": {"bio_strain": 5, "cog_load": 5}
                    - "impact_prediction": "A 1-sentence prediction of how their current state and telemetry will impact their glucose over the next 2 hours."
                    """
                    
                    assistant_model = genai.GenerativeModel(
                        active_model_name,
                        generation_config={"response_mime_type": "application/json"},
                        system_instruction=system_instruction
                    )

                    response = assistant_model.generate_content(text_input)
                    clean_text = response.text.strip()
                    
                    # Safe replacement to avoid markdown parser cutoff
                    markdown_fence = chr(96) * 3
                    clean_text = clean_text.replace(f"{markdown_fence}json", "").replace(markdown_fence, "").strip()
                    
                    parsed = json.loads(clean_text)
                    parsed["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.journal_history.insert(0, parsed)
                    st.rerun()
                except Exception as e: 
                    st.error("Correlation Analysis failed. Please try again.")
                    
    if st.session_state.journal_history:
        entry = st.session_state.journal_history[0]
        st.success(f"**Agentic Insight:** {html.escape(entry.get('reply', ''))}")
        
        sc = entry.get("scores", {"bio_strain": 0, "cog_load": 0})
        c1, c2, c3 = st.columns(3)
        c1.metric("🧬 Bio-Strain", f"{sc.get('bio_strain', 0)}/10")
        c2.metric("🧠 Cog-Load", f"{sc.get('cog_load', 0)}/10")
        c3.metric("📌 Status", html.escape(entry.get("summary", "")))
        st.info(f"**📉 Horizon Scan:** {html.escape(entry.get('impact_prediction', ''))}")

# --- VIEW D: SLEEP IMPACT ---
elif st.session_state.active_view == "Sleep":
    st.markdown("### 🌙 Sleep & Recovery Correlation")
    if st.session_state.whoop_token and whoop_metrics:
        sleep_perf = whoop_metrics.get('score', {}).get('sleep_performance_percentage', 85)
        overnight_df = full_data.tail(96)
        std_dev = int(overnight_df['Glucose_Value'].std())
        
        s_col1, s_col2 = st.columns(2)
        with s_col1: st.metric("Sleep Performance", f"{sleep_perf}%", delta="Restorative" if sleep_perf > 80 else "Deficit", delta_color="normal" if sleep_perf > 80 else "inverse")
        with s_col2: st.metric("Overnight Volatility", f"±{std_dev} mg/dL", delta="Stable" if std_dev < 15 else "Erratic", delta_color="normal" if std_dev < 15 else "inverse")
        st.markdown("---")
        
        sleep_fig = go.Figure()
        sleep_fig.add_trace(go.Scatter(x=overnight_df['Timestamp'], y=overnight_df['Glucose_Value'], mode='lines+markers', line=dict(color='#A855F7', width=4)))
        sleep_fig.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='gray'))
        st.plotly_chart(sleep_fig, use_container_width=True)
        
        if std_dev > 20 and sleep_perf < 70: st.warning("⚠️ **Agentic Insight:** High volatility detected. Consider a +20% basal temporary increase.")
        else: st.success("✅ **Agentic Insight:** Stable overnight metabolic state.")
    else:
        st.info("🔗 Open the ☰ MENU above to connect Whoop and enable Sleep Impact correlation.")

st.markdown(styles.FOOTER_HTML, unsafe_allow_html=True)