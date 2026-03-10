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
import base64
import requests
import re
import pandas as pd
import os
from datetime import datetime, timedelta
import calendar_sync
from audio_recorder_streamlit import audio_recorder
from openai import OpenAI
import tempfile

# -----------------------------------------------------------------------------
# 1. SETUP & CLAUDE WRAPPER 
# -----------------------------------------------------------------------------
st.set_page_config(page_title="TLDH", page_icon="🧠", layout="wide", initial_sidebar_state="collapsed")
styles.apply_theme()
styles.inject_custom_css()

# UI POLISH: Shadows, Alignment Spacers, Premium Button CSS, and Matrix Grid
st.markdown("""
    <style>
    /* Global Button Styling with Drop Shadows */
    div[data-testid="stButton"] > button { border-radius: 50px !important; font-weight: 700 !important; transition: all 0.3s ease !important; letter-spacing: 0.5px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important; }
    div[data-testid="stButton"] > button[kind="primary"] { background: linear-gradient(135deg, #8B5CF6, #6D28D9) !important; color: white !important; border: none !important; }
    div[data-testid="stButton"] > button[kind="primary"]:hover { box-shadow: 0 6px 15px rgba(139, 92, 246, 0.4) !important; transform: translateY(-2px); }
    div[data-testid="stButton"] > button[kind="secondary"] { border: 1px solid rgba(139, 92, 246, 0.3) !important; background-color: var(--secondary-background-color) !important; }
    div[data-testid="stButton"] > button[kind="secondary"]:hover { border-color: #8B5CF6 !important; color: #8B5CF6 !important; transform: translateY(-2px); }
    
    /* Popover Button specific shadow to make them pop */
    div[data-testid="stPopover"] > button { border-radius: 50px !important; font-weight: 700 !important; box-shadow: 0 4px 12px rgba(0,0,0,0.12) !important; border: 1px solid rgba(139, 92, 246, 0.2) !important; transition: all 0.3s ease !important;}
    div[data-testid="stPopover"] > button:hover { transform: translateY(-2px); box-shadow: 0 6px 15px rgba(139, 92, 246, 0.25) !important; border-color: #8B5CF6 !important; }
    
    /* Matrix Grid Override for Total Life Drivers */
    .driver-pill { 
        margin: 0 !important; 
        width: 100% !important; 
        justify-content: center !important; 
        text-align: center !important; 
        padding: 8px 4px !important;
        font-size: 0.75rem !important;
    }
    
    /* Dynamic Alignment Spacer (Only shows on Desktop) */
    @media (max-width: 768px) {
        .desktop-spacer { display: none !important; }
    }
    </style>
""", unsafe_allow_html=True)

try:
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    ACTIVE_MODEL = 'claude-haiku-4-5' 
except Exception as e:
    st.error(f"⚠️ API Critical Failure: {e}"); st.stop()

try:
    openai_client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))
except Exception:
    openai_client = None

def ask_claude(system_instruction, user_messages, max_tokens=500, parse_json=True):
    try:
        res = client.messages.create(model=ACTIVE_MODEL, max_tokens=max_tokens, system=system_instruction, messages=user_messages)
        text = res.content[0].text.strip()
        return json.loads(text.replace("```json", "").replace("```", "").strip()) if parse_json else text
    except Exception as e:
        if "not_found_error" in str(e) or "404" in str(e):
            raise Exception(f"**API Account Locked:** Your Anthropic account cannot access '{ACTIVE_MODEL}'. You must add at least $5 in prepaid credits at console.anthropic.com/settings/billing to unlock API access to Claude 3 models.")
        raise e

def get_ai_chart_summary(chart_type, time_window, metrics, active_memory=""):
    sys_prompt = f"""You are my elite personal performance coach. Analyze my {chart_type} over the last {time_window}. 
    Metrics: {metrics}. 
    Recent Events Context: {active_memory}. 
    Clinical Guardrails: Target range is 70-180 mg/dL. Any spike above 180 is considered high and requires attention.
    CRITICAL INSTRUCTION: If the Recent Events explain the current glucose trend (e.g., a recently logged meal causing a spike, or recent exercise/strain causing a drop), you MUST explicitly acknowledge that connection. 
    Provide a 2-sentence highly actionable synthesis. Speak directly to me ('you'). No 'the patient'. No markdown."""
    return ask_claude(sys_prompt, [{"role": "user", "content": "Synthesize this trend based on my recent context."}], max_tokens=150, parse_json=False)

def render_adaptive_schedule_card(title, value):
    card_css = "background-color: var(--secondary-background-color); padding: 20px; border-radius: 20px; border: 1px solid rgba(128,128,128,0.2); box-shadow: 0 4px 10px rgba(0,0,0,0.05); text-align: center;"
    return f"<div style='{card_css}'><div style='color:var(--text-secondary);font-size:0.85rem;font-weight:700;text-transform:uppercase;'>{title}</div><div style='font-weight:800; color:var(--text-color); font-size:1.3rem; margin-top:5px;'>{value}</div></div>"

# --- DYNAMIC TONE ENGINE ---
def get_claude_tone():
    ctx = st.session_state.current_context
    if ctx == "Stressed": return "gentle, concerned, and highly supportive. Encourage rest, restorative action, and self-compassion."
    elif ctx == "Exercise": return "excited, energetic, and highly encouraging. Push healthy activity and proper metabolic fueling."
    elif ctx == "Recovery": return "calm, analytical, and restorative. Focus on refueling, managing post-exercise spikes/drops, and optimizing sleep."
    elif ctx == "Sick": return "compassionate, cautious, and clinically protective. Focus on hydration, gentle recovery, and fighting resistance."
    elif ctx == "Travel": return "vigilant, organized, and proactive. Focus on logistical stability."
    else: return "warm, personal, and highly actionable like an elite clinical coach."

def get_time_remaining(end_time):
    if not end_time: return ""
    diff = end_time - datetime.now()
    if diff.total_seconds() <= 0: return ""
    mins = int(diff.total_seconds() / 60)
    return f"{mins//60}h {mins%60}m left" if mins >= 60 else f"{mins}m left"

# -----------------------------------------------------------------------------
# 2. STATE, TIMERS & EVENT LOGGING
# -----------------------------------------------------------------------------
def load_ns_config():
    try:
        with open("ns_config.json", "r") as f: return json.load(f)
    except: return {"url": "", "token": ""}

def save_ns_config(url, token):
    try:
        with open("ns_config.json", "w") as f: json.dump({"url": url, "token": token}, f)
    except: pass

ns_cfg = load_ns_config()

# Initialization
if "current_context" not in st.session_state: st.session_state.current_context = "Normal"
if "context_end_time" not in st.session_state: st.session_state.context_end_time = None
if "ns_url" not in st.session_state: st.session_state.ns_url = ns_cfg.get("url", "")
if "ns_token" not in st.session_state: st.session_state.ns_token = ns_cfg.get("token", "")
if "whoop_token" not in st.session_state: st.session_state.whoop_token = whoop.get_valid_access_token()
if "camera_active" not in st.session_state: st.session_state.camera_active = False
if "mic_active" not in st.session_state: st.session_state.mic_active = False
if "event_log" not in st.session_state: st.session_state.event_log = []
if "muted_intercepts" not in st.session_state: st.session_state.muted_intercepts = {}
if "_toast" not in st.session_state: st.session_state._toast = None
if "active_view" not in st.session_state: st.session_state.active_view = "Home"

# Consume transient toast message
if st.session_state._toast:
    st.toast(st.session_state._toast)
    st.session_state._toast = None

def log_event(event_type, description):
    st.session_state.event_log.append({
        "time": datetime.now().strftime("%I:%M %p"),
        "type": event_type,
        "desc": description
    })
    st.session_state.event_log = st.session_state.event_log[-15:] # Keep last 15

# Time-Decaying State Check & Recovery Handoff
if st.session_state.context_end_time and datetime.now() > st.session_state.context_end_time:
    if st.session_state.current_context == "Exercise":
        st.session_state.current_context = "Recovery"
        st.session_state.context_end_time = datetime.now() + timedelta(hours=2)
        log_event("📍 Mode Shift", "Auto-shifted from Exercise to Recovery")
        st.session_state._toast = "🔋 Exercise concluded. Recovery mode activated."
        st.rerun() 
    else:
        st.session_state.current_context = "Normal"
        st.session_state.context_end_time = None
        log_event("📍 Mode Shift", "Context timer expired. Returned to Normal.")
        st.session_state._toast = "🟢 Context timer expired. Returned to Normal."
        st.rerun() 

if "code" in st.query_params and not st.session_state.whoop_token:
    with st.spinner("Authenticating Integrations..."):
        if st.query_params.get("state") == st.session_state.get("oauth_state"):
            token_data = whoop.get_access_token(st.query_params["code"])
            if token_data and "access_token" in token_data:
                st.session_state.whoop_token = token_data["access_token"]
                whoop.save_tokens(token_data); st.query_params.clear(); st.rerun()

@st.cache_data(ttl=300)
def get_cached_health_data(url, token):
    if url:
        real_df = logic.fetch_nightscout_data(url, token)
        if real_df is not None and not real_df.empty: return real_df, True
    return logic.fetch_health_data(), False

@st.cache_data(ttl=60)
def get_cached_glycemic_risk(df, context, whoop_data=None, meeting_count=0, speaker_mode=False, owm_api_key="", is_real_data=False):
    return logic.calc_glycemic_risk(df, context, whoop_data, meeting_count, speaker_mode, owm_api_key, is_real_data)

try:
    with st.spinner("Synchronizing biometric telemetry..."):
        whoop_metrics = whoop.fetch_whoop_recovery(st.session_state.whoop_token) if st.session_state.whoop_token else None
        meeting_count = st.session_state.get("local_meeting_count", calendar_sync.fetch_calendar_context()[0])
        speaker_mode = st.session_state.get("local_speaker_mode", calendar_sync.fetch_calendar_context()[1])
        
        if whoop_metrics:
            w_rec = whoop_metrics.get('recovery', {}).get('score', {}).get('recovery_score', 0) if 'recovery' in whoop_metrics else whoop_metrics.get('score', {}).get('recovery_score', 0)
            w_sleep = whoop_metrics.get('sleep', {}).get('score', {}).get('sleep_performance_percentage', 0) if 'sleep' in whoop_metrics else whoop_metrics.get('score', {}).get('sleep_performance_percentage', 0)
            w_strain = round(whoop_metrics.get('score', {}).get('strain', 0.0), 1)
            w_hrv = int(whoop_metrics.get('recovery', {}).get('score', {}).get('hrv_rmssd_milli', 0)) if 'recovery' in whoop_metrics else int(whoop_metrics.get('score', {}).get('hrv_rmssd_milli', 0))
            w_rhr = int(whoop_metrics.get('recovery', {}).get('score', {}).get('resting_heart_rate', 0)) if 'recovery' in whoop_metrics else int(whoop_metrics.get('score', {}).get('resting_heart_rate', 0))
        else: w_rec, w_sleep, w_strain, w_hrv, w_rhr = 0, 0, 0.0, 0, 0

        raw_data, is_real_cgm = get_cached_health_data(st.session_state.ns_url, st.session_state.ns_token)
        full_data, status, color_hex, raw_reason = get_cached_glycemic_risk(raw_data, st.session_state.current_context, whoop_metrics, meeting_count, speaker_mode, st.secrets.get("OWM_API_KEY", ""), is_real_cgm)
        latest_bg = full_data.iloc[-1]
except Exception as e:
    st.error(f"Data loading failed: {e}"); st.stop()

# -----------------------------------------------------------------------------
# 3. BUILD ACTIVE MEMORY (Context Injector)
# -----------------------------------------------------------------------------
active_memory_list = []
if st.session_state.get("latest_meal_analysis"):
    meal_mem = st.session_state.latest_meal_analysis
    raw_c = meal_mem.get('estimated_carbs_g', 0)
    display_c = raw_c.get('total_estimated', raw_c.get('total', 0)) if isinstance(raw_c, dict) else raw_c
    active_memory_list.append(f"Recently logged a meal: {meal_mem.get('food_identified', 'Food')} ({display_c}g carbs, {meal_mem.get('glycemic_index', 'Unknown')} GI).")

if st.session_state.current_context in ["Exercise", "Recovery"]:
    active_memory_list.append(f"Currently in {st.session_state.current_context} mode. High physiological load expected.")
elif w_strain > 12.0:
    active_memory_list.append(f"Notable daily Whoop strain recorded today: {w_strain}.")

context_memory_string = " | ".join(active_memory_list) if active_memory_list else "No active external events logged."

# -----------------------------------------------------------------------------
# 4. AUTO-DETECT INTERCEPTS & UI HEADERS
# -----------------------------------------------------------------------------
# POLISHED HEADER: Glass-morphic gradient container
st.markdown(f"""
    <div style="margin-top: 10px; margin-bottom: 25px; padding: 24px 30px; background: linear-gradient(135deg, rgba(139,92,246,0.08), rgba(109,40,217,0.03)); border: 1px solid rgba(139,92,246,0.2); border-radius: 24px; box-shadow: 0 8px 24px rgba(0,0,0,0.04);">
        <div style="font-size: 34px; font-weight: 900; background: linear-gradient(135deg, #8B5CF6, #6D28D9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.5px; line-height: 1.2;">Total Life Download Hub</div>
        <div style="color: var(--text-secondary); font-weight: 600; font-size: 1.15rem; margin-top: 4px; letter-spacing: 0.5px;">Agentic Risk Management Engine</div>
    </div>
""", unsafe_allow_html=True)

# Hardware Auto-Detect Intercepts
if st.session_state.current_context == "Normal":
    auto_mode, auto_dur, auto_reason = None, 0, ""
    
    if len(full_data) >= 6 and all(full_data.tail(6)['Glucose_Value'] > 160):
        auto_mode, auto_dur, auto_reason = "Stressed", 3, "Sustained elevated glucose detected."
    elif w_strain > 14.0 and latest_bg['Trend'] in ["Falling", "Falling Fast"]:
        auto_mode, auto_dur, auto_reason = "Recovery", 2, "High Whoop strain detected with dropping glucose (Post-Workout)."
    elif w_strain > 14.0:
        auto_mode, auto_dur, auto_reason = "Exercise", 2, "High systemic strain detected via Whoop."
        
    if auto_mode and auto_mode in st.session_state.muted_intercepts:
        if datetime.now() < st.session_state.muted_intercepts[auto_mode]:
            auto_mode = None 
            
    if auto_mode:
        st.info(f"🤖 **Agentic Intercept:** {auto_reason} Shift to **{auto_mode}** mode for {auto_dur} hours?")
        col1, col2, _ = st.columns([1, 1, 3])
        if col1.button(f"✅ Yes, activate", key=f"yes_{auto_mode}"):
            st.session_state.current_context = auto_mode
            st.session_state.context_end_time = datetime.now() + timedelta(hours=auto_dur)
            log_event("📍 Mode Shift", f"Auto-shifted to {auto_mode} ({auto_reason})")
            st.session_state._toast = f"✅ Agentic shift to {auto_mode} active!"
            st.rerun()
        if col2.button(f"❌ No, dismiss", key=f"no_{auto_mode}"):
            st.session_state.muted_intercepts[auto_mode] = datetime.now() + timedelta(hours=2)
            st.rerun()

elif st.session_state.current_context == "Exercise":
    if latest_bg['Trend'] == "Falling Fast":
        if "Recovery" not in st.session_state.muted_intercepts or datetime.now() >= st.session_state.muted_intercepts["Recovery"]:
            st.warning("🤖 **Agentic Intercept:** Rapid glucose drop detected during Exercise. Shift to **Recovery** mode early to focus on refueling?")
            col1, col2, _ = st.columns([1, 1, 3])
            if col1.button("✅ Yes, activate Recovery", key="yes_rec_early"):
                st.session_state.current_context = "Recovery"
                st.session_state.context_end_time = datetime.now() + timedelta(hours=2)
                log_event("📍 Mode Shift", "Early auto-shift to Recovery due to BG drop")
                st.session_state._toast = "✅ Recovery mode activated!"
                st.rerun()
            if col2.button("❌ No, dismiss", key="no_rec_early"):
                st.session_state.muted_intercepts["Recovery"] = datetime.now() + timedelta(hours=2)
                st.rerun()

with st.container(border=True):
    hc1, hc2, hc3, hc4 = st.columns([3.5, 2.5, 2.5, 1.5])
    
    with hc1:
        st.markdown("<p style='font-weight: 800; color: var(--text-secondary); text-transform: uppercase; font-size: 0.75rem; letter-spacing: 1px; margin-top: 5px; margin-bottom: 12px;'>⚡ Total Life Drivers</p>", unsafe_allow_html=True)
        vectors = []
        
        if st.session_state.current_context != "Normal":
            rem = get_time_remaining(st.session_state.context_end_time)
            icon = {"Stressed": "🧘‍♂️", "Exercise": "🏃‍♂️", "Recovery": "🔋", "Sick": "🤒", "Project": "🧠", "Travel": "✈️"}.get(st.session_state.current_context, "🟣")
            vectors.append(f"{icon} {st.session_state.current_context} ({rem})")

        tir_df = full_data.tail(36)
        if len(tir_df) > 0:
            low, tgt, elev, high = [len(tir_df[cond])/len(tir_df)*100 for cond in [tir_df['Glucose_Value'] < 80, (tir_df['Glucose_Value'] >= 80) & (tir_df['Glucose_Value'] <= 140), (tir_df['Glucose_Value'] > 140) & (tir_df['Glucose_Value'] <= 180), tir_df['Glucose_Value'] > 180]]
            if low > 5: vectors.append(f"🔴 {int(low)}% BG Low (3h)")
            elif high > 15: vectors.append(f"🔴 {int(high)}% BG High (3h)")
            elif elev > 25: vectors.append(f"🟡 {int(elev)}% BG Elevated (3h)")
            else: vectors.append(f"🟢 {int(tgt)}% BG On Target (3h)")

        for p in raw_reason.split("|"):
            clean = re.sub(r'Hyperglycemic risk detected\.?|Hypoglycemic risk detected\.?|Compounded Strain Detected\!|System nominal\.?', '', p).replace('()', '').replace('(', '').replace(')', '').strip()
            if clean: vectors.append(html.escape(clean))
        
        # UI POLISH: Matrix Layout for Pills
        tags_html = "".join([styles.get_driver_pill_html(t) for t in (vectors[:4] if vectors else ["🟢 All Systems Nominal"])])
        st.markdown(f"<div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;'>{tags_html}</div>", unsafe_allow_html=True)
    
    with hc2:
        st.markdown("<div class='desktop-spacer' style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.session_state.get("journal_history"):
            if st.button("🎙️ Log Another Note", use_container_width=True):
                st.session_state.journal_history = []
                st.rerun()
        else:
            with st.popover("🎙️ Companion", use_container_width=True):
                if st.button("🔽 Close Panel", key="close_comp_panel", use_container_width=True): st.rerun() # Mobile UX Fix
                st.caption("Tap the mic or type a note. The AI will correlate your state with live telemetry.")
                if not st.session_state.mic_active:
                    if st.button("🎙️ Enable Microphone", use_container_width=True):
                        st.session_state.mic_active = True
                        st.rerun()
                else:
                    audio_bytes = audio_recorder(text="Record Voice Note", recording_color="#ED8796", neutral_color="#8B5CF6", icon_size="2x")
                    if st.button("❌ Disable Mic", use_container_width=True):
                        st.session_state.mic_active = False; st.rerun()
                    if audio_bytes and hashlib.md5(audio_bytes).hexdigest() != st.session_state.get("last_audio_hash"):
                        st.session_state.last_audio_hash = hashlib.md5(audio_bytes).hexdigest()
                        if openai_client and st.secrets.get("OPENAI_API_KEY"):
                            with st.spinner("Transcribing Voice Note..."):
                                try:
                                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as fp:
                                        fp.write(audio_bytes)
                                        temp_path = fp.name
                                    with open(temp_path, "rb") as af:
                                        transcript = openai_client.audio.transcriptions.create(model="whisper-1", file=af)
                                    text_input = transcript.text
                                    text_submit = True 
                                except Exception as e:
                                    st.error(f"Transcription failed: {e}")
                        else:
                            st.warning("🎙️ **OpenAI API Key Missing!** Add OPENAI_API_KEY to your Streamlit secrets to enable Speech-to-Text.")
                
                st.divider()
                with st.form("journal_form", clear_on_submit=True):
                    form_text = st.text_area("Or type your observation:", placeholder="E.g., 'Just finished a heavy lift.'", label_visibility="collapsed")
                    form_submit = st.form_submit_button("Synthesize Telemetry", use_container_width=True)
                
                if form_submit and form_text:
                    text_input = form_text
                    text_submit = True
            
    with hc3:
        st.markdown("<div class='desktop-spacer' style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.session_state.get("latest_meal_analysis"):
            if st.button("🍽️ Scan Another Meal", use_container_width=True):
                st.session_state.latest_meal_analysis = None
                st.rerun()
        else:
            with st.popover("🍽️ Meals", use_container_width=True):
                if st.button("🔽 Close Panel", key="close_meals_panel", use_container_width=True): st.rerun() # Mobile UX Fix
                st.caption("Snap a photo to estimate carbohydrates and metabolic impact.")
                if not st.session_state.camera_active:
                    if st.button("📸 Open Camera Scanner", use_container_width=True):
                        st.session_state.camera_active = True
                        st.rerun()
                else:
                    food_image = st.camera_input("Food Scanner", label_visibility="collapsed")
                    if st.button("❌ Disable Camera", use_container_width=True):
                        st.session_state.camera_active = False; st.rerun()
                        
                st.divider()
                with st.form("usda_search_form"):
                    db_search_query = st.text_input("Search USDA Database:", placeholder="E.g., 1 cup cooked quinoa")
                    db_search_submit = st.form_submit_button("Lookup Exact Macros", use_container_width=True)
                
    with hc4:
        st.markdown("<div class='desktop-spacer' style='height: 28px;'></div>", unsafe_allow_html=True)
        with st.popover("☰ Menu", use_container_width=True):
            if st.button("🔽 Close Panel", key="close_menu_panel", use_container_width=True): st.rerun() # Mobile UX Fix
            st.markdown("##### 📍 Context Settings")
            with st.form("context_override_form"):
                new_ctx = st.selectbox("Force Context Mode:", ["Normal", "Stressed", "Recovery", "Sick", "Exercise", "Project", "Travel"], index=["Normal", "Stressed", "Recovery", "Sick", "Exercise", "Project", "Travel"].index(st.session_state.current_context))
                dur_val = st.selectbox("Duration:", [0.5, 1.0, 3.0, 6.0], format_func=lambda x: f"{int(x)} hours" if x >= 1 else "30 mins")
                if st.form_submit_button("Apply Mode", use_container_width=True):
                    st.session_state.current_context = new_ctx
                    st.session_state.context_end_time = datetime.now() + timedelta(hours=dur_val) if new_ctx != "Normal" else None
                    log_event("📍 Mode Shift", f"Manually set to {new_ctx} for {dur_val}h")
                    st.session_state._toast = f"✅ Context updated to {new_ctx}!"
                    st.rerun()
            
            st.divider()
            st.markdown("##### 🔌 Integrations")
            st.markdown("**🩸 Nightscout CGM Sync**")
            if st.session_state.ns_url:
                if is_real_cgm: st.success("🟢 Connected & Streaming Live")
                else: st.error("🔴 Connection Failed. (Simulated Data)")
                if st.button("Disconnect / Reconnect", key="dc_ns"):
                    st.session_state.ns_url = ""; st.session_state.ns_token = ""
                    save_ns_config("", "")
                    st.cache_data.clear(); st.rerun()
            else:
                with st.form("ns_form"):
                    ns_url_input = st.text_input("Nightscout URL", placeholder="https://your-name.herokuapp.com")
                    ns_token_input = st.text_input("API Token (Optional)", type="password")
                    if st.form_submit_button("Connect", use_container_width=True):
                        st.session_state.ns_url = ns_url_input; st.session_state.ns_token = ns_token_input
                        save_ns_config(ns_url_input, ns_token_input)
                        st.cache_data.clear(); st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**📱 Native Calendar (Mock)**")
            cal_file = st.file_uploader("Upload .ics", type=["ics"], label_visibility="collapsed")
            if cal_file:
                mc, sm = calendar_sync.analyze_local_calendar(cal_file.getvalue().decode("utf-8"))
                st.session_state.local_meeting_count, st.session_state.local_speaker_mode = mc, sm
                st.success(f"Local Sync: {mc} events loaded.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**⚡ Whoop Telemetry**")
            if not st.session_state.whoop_token:
                oauth_state = secrets.token_urlsafe(16)
                st.components.v1.html(f"<script>window.parent.document.cookie = 'whoop_oauth_state={oauth_state}; path=/; max-age=3600; SameSite=Lax';</script>", height=0)
                st.link_button("🔗 Connect Whoop", whoop.get_authorization_url(oauth_state), use_container_width=True)
            else:
                if whoop_metrics: st.success("🟢 Connected & Syncing")
                else: st.error("🔴 Data Sync Failed (Cached)")
                if st.button("🔄 Force Refresh Sync", use_container_width=True): 
                    st.session_state.whoop_token = whoop.get_valid_access_token()
                    whoop.fetch_whoop_recovery.clear()
                    st.rerun() 

st.divider()

# -----------------------------------------------------------------------------
# 5. EVENT PROCESSORS (SEMANTIC NLP DETECT)
# -----------------------------------------------------------------------------
if 'text_submit' in locals() and text_submit and text_input:
    with st.spinner("Correlating subjective report with objective telemetry..."):
        try:
            ctx = {"context": st.session_state.current_context, "meetings": meeting_count, "glucose": int(latest_bg['Glucose_Value']), "trend": latest_bg['Trend']}
            sys = f"""You are my elite AI clinical assistant. My telemetry: {json.dumps(ctx)}. 
            Active Memory Context: {context_memory_string}.
            Clinical Guardrails: Target range is 70-180 mg/dL. Any spike above 180 is considered high and requires attention.
            Correlate my text with the telemetry and memory. 
            Speak to me as 'you'. Tone should be {get_claude_tone()}. NEVER refer to me as "the patient".
            Return ONLY a valid JSON object with EXACTLY these keys:
            - "reply": "A contextual response."
            - "summary": "3 words."
            - "scores": {{"bio_strain": 5, "cog_load": 5}}
            - "impact_prediction": "1-sentence prediction."
            - "suggested_mode": "Exercise", "Recovery", "Stressed", "Sick", "Project", "Travel", or "Normal" (Detect from my text)
            - "suggested_duration_hours": 1.5"""
            res_data = ask_claude(sys, [{"role": "user", "content": text_input}])
            st.session_state.journal_history = [res_data]
            log_event("🎙️ Note", res_data.get("summary", "Logged observation."))
            st.session_state.mic_active = False 
            st.rerun() 
        except Exception as e: st.error(f"Failed: {e}")

if 'food_image' in locals() and food_image is not None:
    img_hash = hashlib.md5(food_image.getvalue()).hexdigest()
    if img_hash != st.session_state.get("last_img_hash"):
        st.session_state.last_img_hash = img_hash
        with st.spinner("Analyzing meal nutrition..."):
            try:
                b64 = base64.b64encode(food_image.getvalue()).decode("utf-8")
                sys = f"""You are my elite personal clinical nutritionist managing my Type 1 Diabetes.
                Analyze the food image. Estimate carbs and glycemic index.
                Speak directly to me using "you" and "your". Tone should be {get_claude_tone()}. NEVER refer to me as "the patient".
                Return ONLY a valid JSON object with EXACTLY these keys and strict data types:
                - "food_identified": "Short description." (Must be a String)
                - "estimated_carbs_g": 45 (MUST be a single Integer. No dictionaries)
                - "glycemic_index": "High", "Medium", or "Low" (Must be a String)
                - "analysis": "A concise 2-sentence clinical breakdown." (Must be a String)"""
                meal_data = ask_claude(sys, [{"role": "user", "content": [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}}, {"type": "text", "text": "Analyze this meal for T1D."}]}])
                meal_data["source"] = "📸 Vision Estimate"
                
                raw_c = meal_data.get('estimated_carbs_g', 0)
                display_c = raw_c.get('total_estimated', raw_c.get('total', 0)) if isinstance(raw_c, dict) else raw_c
                log_event("🍽️ Meal", f"{meal_data.get('food_identified', 'Meal')} ({display_c}g Carbs)")
                
                st.session_state.latest_meal_analysis = meal_data
                st.session_state.camera_active = False 
                st.rerun() 
            except Exception as e: st.error(f"Failed: {e}")

# Render Semantic Suggestions (Assistant Output)
if st.session_state.get("journal_history"):
    entry = st.session_state.journal_history[0]
    st.success(f"**Agentic Insight:** {html.escape(str(entry.get('reply', '')))}")
    
    # NLP Context Suggestion
    s_mode = entry.get("suggested_mode", "Normal")
    if s_mode and s_mode != "Normal" and s_mode != st.session_state.current_context:
        s_dur = float(entry.get("suggested_duration_hours", 1.0))
        st.warning(f"🤖 **Context Suggestion:** Your note implies you are in **{s_mode}** mode.")
        col1, col2, _ = st.columns([1, 1, 3])
        if col1.button(f"⚡ Apply '{s_mode}'", key="nlp_yes"):
            st.session_state.current_context = s_mode
            st.session_state.context_end_time = datetime.now() + timedelta(hours=s_dur)
            log_event("📍 Mode Shift", f"Applied {s_mode} via AI Suggestion")
            st.session_state._toast = f"✅ Context shifted to {s_mode}!"
            st.session_state.journal_history = []
            st.rerun()
        if col2.button(f"❌ Dismiss", key="nlp_no"):
            entry['suggested_mode'] = "Normal" # Suppress this suggestion
            st.rerun()

    c1, c2, c3 = st.columns(3); c1.metric("🧬 Bio-Strain", f"{entry.get('scores',{}).get('bio_strain', 0)}/10"); c2.metric("🧠 Cog-Load", f"{entry.get('scores',{}).get('cog_load', 0)}/10"); c3.metric("📌 Status", html.escape(str(entry.get("summary", ""))))
    st.info(f"**📉 Horizon Scan:** {html.escape(str(entry.get('impact_prediction', '')))}")
    if st.button("Dismiss Insight", use_container_width=True): st.session_state.journal_history = []; st.rerun()
    st.divider()

if st.session_state.get("latest_meal_analysis"):
    meal = st.session_state.latest_meal_analysis
    st.markdown(f"### 🍽️ Meal Analysis <span style='font-size:14px;color:gray;'>({meal.get('source')})</span>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns([1, 1, 2])
    m1.metric("Identified", str(meal.get("food_identified", "Unknown")))
    
    raw_carbs = meal.get('estimated_carbs_g', 0)
    display_carbs = raw_carbs.get('total_estimated', raw_carbs.get('total', 0)) if isinstance(raw_carbs, dict) else raw_carbs
    m2.metric("Carbs", f"{display_carbs}g")
    
    gi = str(meal.get("glycemic_index", "Unknown"))
    gi_color = "🔴" if "high" in gi.lower() else "🟡" if "medium" in gi.lower() else "🟢"
    m3.metric("Glycemic Index", f"{gi_color} {gi}")
    
    st.info(f"**Clinical Insight:** {meal.get('analysis', '')}")
    if st.button("Dismiss Analysis", use_container_width=True): st.session_state.latest_meal_analysis = None; st.rerun()
    st.divider()

# -----------------------------------------------------------------------------
# 6. NAVIGATION & RENDER VIEWS
# -----------------------------------------------------------------------------
# UI POLISH: 6-Column Navigation Array includes the dedicated "Events" view
views = ["Home", "Briefing", "Metrics", "Events", "Schedule", "Sleep"]
v_cols = st.columns(len(views))
for i, view in enumerate(views):
    is_active = (st.session_state.active_view == view)
    if v_cols[i].button(view, use_container_width=True, type="primary" if is_active else "secondary"):
        st.session_state.active_view = view
        st.rerun()
st.markdown("---")

# DYNAMIC LANDING DASHBOARD (Zero API Cost)
if st.session_state.active_view == "Home":
    c1, c2, c3 = st.columns(3)
    delta = int(latest_bg['Glucose_Value'] - full_data.iloc[-2]['Glucose_Value'])
    delta_str = f"+{delta}" if delta >= 0 else f"{delta}"
    c1.metric("🩸 Blood Sugar", f"{int(latest_bg['Glucose_Value'])} mg/dL", f"{delta_str} ({latest_bg['Trend']})")
    
    if st.session_state.whoop_token and whoop_metrics:
        c2.metric("⚡ Systemic Strain", f"{w_strain}", f"Recovery: {w_rec}%")
    else:
        c2.metric("⚡ Systemic Strain", "N/A", "Whoop Not Synced")
        
    last_event_str = "No events logged today."
    if st.session_state.event_log:
        last_event = st.session_state.event_log[-1]
        last_event_str = f"{last_event['type']}: {last_event['desc']}"
    c3.metric("📝 Latest Activity", last_event_str)

elif st.session_state.active_view == "Briefing":
    with st.spinner("Compiling Executive Briefing..."):
        try:
            sys = f"""You are an elite personal performance coach and clinical AI agent. Tone should be {get_claude_tone()}
            Metrics: {st.session_state.current_context} Context, {meeting_count} meetings today, Whoop Recovery: {w_rec}%, Current BG: {int(latest_bg['Glucose_Value'])} ({latest_bg['Trend']}). 
            Active Memory Context: {context_memory_string}.
            Clinical Guardrails: Target range is 70-180 mg/dL. Any spike above 180 is considered high and requires attention.
            CRITICAL: If the Active Memory explains the current glucose trend, explicitly acknowledge this.
            Synthesize this into a proactive daily briefing. Focus on cognitive load management and metabolic forecasting. Speak directly to me using 'you'.
            Return ONLY a valid JSON object with these EXACT keys: 
            'metabolic_baseline' (assess my physical readiness and insulin sensitivity based on Whoop, BG, and Memory), 
            'schedule_friction' (how my calendar density impacts my glucose management today), 
            'action_directive' (one clear, proactive step to take right now)."""
            
            data = ask_claude(sys, [{"role": "user", "content": "Generate my morning briefing."}])
            st.info(f"**🧬 Metabolic Baseline:** {html.escape(data.get('metabolic_baseline', ''))}")
            st.warning(f"**🗓️ Schedule Friction:** {html.escape(data.get('schedule_friction', ''))}")
            st.success(f"**🎯 Action Directive:** {html.escape(data.get('action_directive', ''))}")
        except Exception as e: st.error(f"Failed: {e}")

elif st.session_state.active_view == "Metrics":
    c_dex = st.columns(2)
    c_dex[0].metric("Blood Sugar (mg/dL)", int(latest_bg['Glucose_Value']), int(latest_bg['Glucose_Value'] - full_data.iloc[-2]['Glucose_Value']))
    c_dex[1].metric("Trend", latest_bg['Trend'])
    
    if st.session_state.whoop_token and whoop_metrics:
        st.markdown("<br>", unsafe_allow_html=True)
        c_wh1, c_wh2, c_wh3 = st.columns(3)
        c_wh1.metric("Recovery", f"{w_rec}%")
        c_wh2.metric("HRV", f"{w_hrv} ms")
        c_wh3.metric("Resting HR", f"{w_rhr} bpm")
        st.markdown("<br>", unsafe_allow_html=True)
        
    tw = st.radio("Time Range", ["3h", "6h", "12h", "24h"], index=1, horizontal=True, label_visibility="collapsed")
    p_df = full_data.tail({"3h": 36, "6h": 72, "12h": 144, "24h": 288}[tw])
    
    fig = go.Figure(go.Scatter(x=p_df['Timestamp'], y=p_df['Glucose_Value'], mode='lines', line=dict(color='#8B5CF6', width=3)))
    fig.add_hrect(y0=70, y1=180, line_width=0, fillcolor="rgba(166, 218, 149, 0.1)", opacity=0.5); fig.add_hline(y=70, line_dash="dash", line_color="#ED8796")
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='gray'), height=400, margin=dict(l=0, r=0, t=30, b=0), yaxis_title="mg/dL", xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with st.spinner("Synthesizing Trend..."):
        std_val = p_df['Glucose_Value'].std()
        safe_std = int(std_val) if pd.notna(std_val) else 0
        metrics_str = f"Avg: {int(p_df['Glucose_Value'].mean())}, Min: {int(p_df['Glucose_Value'].min())}, Max: {int(p_df['Glucose_Value'].max())}, Std Dev: {safe_std}, Latest: {int(p_df['Glucose_Value'].iloc[-1])}"
        st.success(f"**🤖 Agentic Synthesis:** {get_ai_chart_summary('Glucose', tw, metrics_str, context_memory_string)}")

elif st.session_state.active_view == "Events":
    st.markdown("### 📜 System Event Log")
    st.caption("A chronological record of agentic shifts, logged meals, and clinical insights.")
    if not st.session_state.event_log:
        st.info("No events logged yet today.")
    else:
        for event in reversed(st.session_state.event_log):
            st.markdown(f"**{event['time']}** - {event['type']}<br><span style='color:gray;'>{event['desc']}</span>", unsafe_allow_html=True)
            st.divider()

elif st.session_state.active_view == "Schedule":
    h1, h2, h3, h4 = st.columns(4)
    with h1: st.markdown(render_adaptive_schedule_card("1 HOUR", '✈️ SHIFTING' if st.session_state.current_context == 'Travel' else '🟢 SAFE'), unsafe_allow_html=True)
    with h2: st.markdown(render_adaptive_schedule_card("4 HOURS", '🟡 CAUTION' if st.session_state.current_context == 'Stressed' else '🟢 CLEAR'), unsafe_allow_html=True)
    with h3: st.markdown(render_adaptive_schedule_card("24 HOURS", '🟢 GOOD'), unsafe_allow_html=True)
    with h4: st.markdown(render_adaptive_schedule_card("MEETINGS", f"{meeting_count} ({'🔴 CRITICAL' if meeting_count>=7 else '🟡 ELEVATED' if meeting_count>=4 else '🟢 LIGHT'})"), unsafe_allow_html=True)
    st.info(f"**Agentic Insight:** The Risk Engine is factoring in **{meeting_count} meetings** to adjust glycemic sensitivity.")

elif st.session_state.active_view == "Sleep":
    if st.session_state.whoop_token and whoop_metrics:
        st.metric("Sleep Perf", f"{w_sleep}%")
        
        tw = st.radio("Range", ["4h", "8h", "12h"], index=1, horizontal=True, label_visibility="collapsed")
        o_df = full_data.tail({"4h": 48, "8h": 96, "12h": 144}[tw])
        
        st.markdown("##### 🩸 Overnight Blood Sugar")
        fig = go.Figure(go.Scatter(x=o_df['Timestamp'], y=o_df['Glucose_Value'], mode='lines+markers', line=dict(color='#A855F7', width=4)))
        fig.add_hrect(y0=70, y1=180, line_width=0, fillcolor="rgba(166, 218, 149, 0.1)", opacity=0.5); fig.add_hline(y=70, line_dash="dash", line_color="#ED8796")
        fig.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with st.spinner("Synthesizing..."):
            std_val = o_df['Glucose_Value'].std()
            safe_std = int(std_val) if pd.notna(std_val) else 0
            metrics_str = f"Avg: {int(o_df['Glucose_Value'].mean())}, Min: {int(o_df['Glucose_Value'].min())}, Max: {int(o_df['Glucose_Value'].max())}, Std Dev: {safe_std}, Latest: {int(o_df['Glucose_Value'].iloc[-1])}"
            st.success(f"**🤖 Agentic Synthesis:** {get_ai_chart_summary(f'Overnight Glucose (with {w_sleep}% Sleep)', tw, metrics_str, context_memory_string)}")
    else: st.info("🔗 Open ☰ Menu to connect Whoop.")

st.markdown(styles.FOOTER_HTML, unsafe_allow_html=True)
