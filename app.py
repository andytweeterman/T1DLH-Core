import html
import secrets
import streamlit as st
import plotly.graph_objects as go
import anthropic
import styles
import logic
import json
import whoop
import hashlib
from datetime import datetime
import calendar_sync
from audio_recorder_streamlit import audio_recorder

# -----------------------------------------------------------------------------
# 1. PAGE SETUP & THEME
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="TLDH | Total Life Download Hub", 
    page_icon="assets/tldh_logo.png",
    layout="wide"
)
styles.apply_theme()

# Custom CSS for the Glowing Pill (Bulletproof Target)
st.markdown("""
    <style>
    /* Target the 3rd column specifically inside the bordered header container.
       This bypasses brittle DOM logic and ensures only this exact button glows.
    */
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"]:nth-of-type(3) button {
        background: linear-gradient(135deg, #8B5CF6, #6D28D9) !important;
        color: white !important;
        border: none !important;
        border-radius: 50px !important;
        animation: pulse-purple 2s infinite !important;
        transition: all 0.3s ease !important;
    }
    
    /* Force the text inside the button to be bold and white */
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"]:nth-of-type(3) button * {
        color: white !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px !important;
    }
    
    @keyframes pulse-purple {
        0% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.7); }
        70% { box-shadow: 0 0 0 15px rgba(139, 92, 246, 0); }
        100% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0); }
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. INITIALIZE ANTHROPIC CLIENT (CLAUDE)
# -----------------------------------------------------------------------------
try:
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    
    # Use the latest Sonnet model
    active_model_name = 'claude-sonnet-4-6' 
    model_status = "✨ CLAUDE SONNET 4.6 ONLINE"

except Exception as e:
    st.error(f"⚠️ API Critical Failure. Details: {e}")
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
        with st.popover("Smart Health Companion", use_container_width=True):
            st.markdown("Ask a question or log how you are feeling. The AI will correlate your input with your live telemetry.")
            st.caption("Tap the mic to log a voice note.")
            audio_bytes = audio_recorder(
                text="",
                recording_color="#ED8796",
                neutral_color="#8B5CF6",
                icon_size="2x"
            )
                
    with p_col4:
        # Hamburger Menu Popover
        with st.popover("☰ MENU", use_container_width=True):
            
            # 1. Context Selector moved into the menu
            st.markdown("##### 📍 Context")
            new_ctx = st.radio(
                "Update Activity Context:",
                ["Normal", "Stressed", "Sick", "Exercise", "Project", "Travel"],
                index=["Normal", "Stressed", "Sick", "Exercise", "Project", "Travel"].index(st.session_state.current_context)
            )
            if st.button("Apply Context", use_container_width=True):
                st.session_state.current_context = new_ctx
                st.rerun()
                
            st.divider()
            
            # 2. Whoop Sync Logic
            st.markdown("##### 🔌 Integrations")
            if not st.session_state.whoop_token:
                # Generate a secure random state string
                oauth_state = secrets.token_urlsafe(16)

                # Inject JavaScript to store the state parameter in a client-side cookie
                st.components.v1.html(
                    f"<script>window.parent.document.cookie = 'whoop_oauth_state={oauth_state}; path=/; max-age=3600; SameSite=Lax';</script>",
                    height=0
                )

                auth_link = whoop.get_authorization_url(oauth_state)
                st.link_button("🔗 Connect Whoop", auth_link, use_container_width=True)
            else:
                if st.button("✅ Whoop Synced", use_container_width=True):
                    st.rerun() 
            
            st.divider()
            
            # 3. Clinical Export Logic
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

# Process Audio Dump logic directly after the header
if audio_bytes:
    # Hash the bytes to prevent Streamlit from constantly re-processing the same audio on every interaction
    audio_hash = hashlib.md5(audio_bytes).hexdigest()
    
    if audio_hash != st.session_state.get("last_audio_hash"):
        st.session_state.last_audio_hash = audio_hash
        
        with st.spinner("Processing Voice Dump and Correlating Telemetry..."):
            st.error("🎙️ **Claude API Limitation:** Anthropic does not currently accept raw audio files. To use voice notes, please integrate a transcription service (like OpenAI Whisper) to convert `audio_bytes` to text first.")

# -----------------------------------------------------------------------------
# 6. NAVIGATION
# -----------------------------------------------------------------------------
if "active_view" not in st.session_state:
    st.session_state.active_view = "Daily Briefing"

c1, c2, c3, c4 = st.columns(4)
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
            
            Return ONLY a valid JSON object with the exact keys: "bullet_1", "bullet_2", "bullet_3". Do not include markdown formatting or extra text.
            """

            response = client.messages.create(
                model=active_model_name,
                max_tokens=500,
                system=system_instruction,
                messages=[
                    {"role": "user", "content": "Generate the executive daily briefing now."}
                ]
            )
            
            clean_text = response.content[0].text.strip()
            
            # Replaced the .startswith method with safe replacement to avoid parser cutoff
            markdown_fence = chr(96) * 3
            clean_text = clean_text.replace(f"{markdown_fence}json", "").replace(markdown_fence, "").strip()
            
            briefing_data = json.loads(clean_text)

            st.info(f"**1. Load & Resilience:** {html.escape(briefing_data.get('bullet_1', ''))}")
            st.warning(f"**2. Metabolic State:** {html.escape(briefing_data.get('bullet_2', ''))}")
            st.success(f"**3. Recommended Action:** {html.escape(briefing_data.get('bullet_3', ''))}")

        except Exception as e:
            st.error(f"Failed to generate briefing. Details: {e}")

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
