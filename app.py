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
from datetime import datetime
import calendar_sync
from audio_recorder_streamlit import audio_recorder

# -----------------------------------------------------------------------------
# 1. SETUP & CLAUDE WRAPPER 
# -----------------------------------------------------------------------------
st.set_page_config(page_title="TLDH", page_icon="🧠", layout="wide", initial_sidebar_state="collapsed")
styles.apply_theme()
styles.inject_custom_css()

# Inject Global Button Styles (Pill formatting & Gradients)
st.markdown("""
    <style>
    div[data-testid="stButton"] > button { border-radius: 50px !important; font-weight: 700 !important; transition: all 0.3s ease !important; letter-spacing: 0.5px !important; }
    div[data-testid="stButton"] > button[kind="primary"] { background: linear-gradient(135deg, #8B5CF6, #6D28D9) !important; color: white !important; border: none !important; }
    div[data-testid="stButton"] > button[kind="primary"]:hover { box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4) !important; transform: translateY(-2px); }
    div[data-testid="stButton"] > button[kind="secondary"] { border: 1px solid var(--text-color) !important; opacity: 0.8; }
    div[data-testid="stButton"] > button[kind="secondary"]:hover { opacity: 1.0; border-color: #8B5CF6 !important; color: #8B5CF6 !important; }
    </style>
""", unsafe_allow_html=True)

try:
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    ACTIVE_MODEL = 'claude-sonnet-4-6' 
except Exception as e:
    st.error(f"⚠️ API Critical Failure: {e}"); st.stop()

def ask_claude(system_instruction, user_messages, max_tokens=500, parse_json=True):
    res = client.messages.create(model=ACTIVE_MODEL, max_tokens=max_tokens, system=system_instruction, messages=user_messages)
    text = res.content[0].text.strip()
    return json.loads(text.replace("```json", "").replace("```", "").strip()) if parse_json else text

@st.cache_data(ttl=300)
def get_ai_chart_summary(chart_type, time_window, metrics):
    sys_prompt = f"You are my elite personal performance coach. Analyze my {chart_type} over the last {time_window}. Metrics: {metrics}. Provide a 2-sentence highly actionable synthesis. Speak directly to me ('you'). No 'the patient'. No markdown."
    return ask_claude(sys_prompt, [{"role": "user", "content": "Synthesize this trend."}], max_tokens=150, parse_json=False)

def render_adaptive_schedule_card(title, value):
    card_css = "background-color: var(--secondary-background-color); padding: 20px; border-radius: 20px; border: 1px solid rgba(128,128,128,0.2); box-shadow: 0 4px 10px rgba(0,0,0,0.05); text-align: center;"
    return f"<div style='{card_css}'><div style='color:var(--text-secondary);font-size:0.85rem;font-weight:700;text-transform:uppercase;'>{title}</div><div style='font-weight:800; color:var(--text-color); font-size:1.3rem; margin-top:5px;'>{value}</div></div>"

# -----------------------------------------------------------------------------
# 2. STATE & DATA LOADING
# -----------------------------------------------------------------------------
if "_toast" not in st.session_state: st.session_state._toast = None
if st.session_state._toast:
    st.toast(st.session_state._toast)
    st.session_state._toast = None

if "current_context" not in st.session_state: st.session_state.current_context = "Normal"
if "ns_url" not in st.session_state: st.session_state.ns_url = ""
if "ns_token" not in st.session_state: st.session_state.ns_token = ""
if "whoop_token" not in st.session_state: st.session_state.whoop_token = whoop.get_valid_access_token()
if "camera_active" not in st.session_state: st.session_state.camera_active = False
if "mic_active" not in st.session_state: st.session_state.mic_active = False

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
        
        # Flattened whoop schema parsing
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
# 3. HEADER & POPOVER MODULARIZATION
# -----------------------------------------------------------------------------
st.markdown(f"""
    <div style="margin-top: 10px; margin-bottom: 25px; display: flex; align-items: center; gap: 15px;">
        <span style="font-size: 46px;">🧠</span>
        <div>
            <div style="font-size: 32px; font-weight: 900; background: linear-gradient(135deg, #8B5CF6, #6D28D9); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.5px; line-height: 1.2;">Total Life Download Hub</div>
            <div style="color: var(--text-secondary); font-weight: 600; font-size: 1.1rem; margin-top: -3px;">Agentic Risk Management Engine</div>
        </div>
    </div>
""", unsafe_allow_html=True)

with st.container(border=True):
    hc1, hc2, hc3, hc4 = st.columns([3.5, 2.5, 2.5, 1.5])
    
    with hc1:
        st.markdown("<p style='font-weight: 800; color: var(--text-secondary); text-transform: uppercase; font-size: 0.75rem; letter-spacing: 1px; margin-top: 5px; margin-bottom: 12px;'>⚡ Total Life Drivers</p>", unsafe_allow_html=True)
        vectors = []
        
        # TIR Vector
        tir_df = full_data.tail(144)
        if len(tir_df) > 0:
            low, tgt, elev, high = [len(tir_df[cond])/len(tir_df)*100 for cond in [tir_df['Glucose_Value'] < 80, (tir_df['Glucose_Value'] >= 80) & (tir_df['Glucose_Value'] <= 140), (tir_df['Glucose_Value'] > 140) & (tir_df['Glucose_Value'] <= 180), tir_df['Glucose_Value'] > 180]]
            if low > 5: vectors.append(f"🔴 {int(low)}% BG Low (12h)")
            elif high > 15: vectors.append(f"🔴 {int(high)}% BG High (12h)")
            elif elev > 25: vectors.append(f"🟡 {int(elev)}% BG Elevated (12h)")
            else: vectors.append(f"🟢 {int(tgt)}% BG On Target (12h)")

        # External Vectors
        for p in raw_reason.split("|"):
            clean = re.sub(r'Hyperglycemic risk detected\.?|Hypoglycemic risk detected\.?|Compounded Strain Detected\!|System nominal\.?', '', p).replace('()', '').replace('(', '').replace(')', '').strip()
            if clean: vectors.append(html.escape(clean))
        
        tags_html = "".join([styles.get_driver_pill_html(t) for t in (vectors[:4] if vectors else ["🟢 All Systems Nominal"])])
        st.markdown(tags_html, unsafe_allow_html=True)
    
    with hc2:
        with st.popover("🎙️ Smart Companion", use_container_width=True):
            if st.session_state.get("journal_history"):
                st.success("✅ Analysis complete! View your insights below.")
                if st.button("Log Another Note", key="reset_journal_pop", use_container_width=True):
                    st.session_state.journal_history = []
                    st.rerun()
            else:
                st.caption("Tap the mic or type a note. The AI will correlate your state with live telemetry.")
                
                # Prevent mic from loading until actively requested
                if not st.session_state.mic_active:
                    if st.button("🎙️ Enable Microphone", use_container_width=True):
                        st.session_state.mic_active = True
                        st.rerun()
                else:
                    audio_bytes = audio_recorder(text="Record Voice Note", recording_color="#ED8796", neutral_color="#8B5CF6", icon_size="2x")
                    if st.button("❌ Close Mic", use_container_width=True):
                        st.session_state.mic_active = False
                        st.rerun()
                        
                    if audio_bytes and hashlib.md5(audio_bytes).hexdigest() != st.session_state.get("last_audio_hash"):
                        st.session_state.last_audio_hash = hashlib.md5(audio_bytes).hexdigest()
                        st.warning("🎙️ **Audio Detected!** Native speech-to-text requires an OpenAI API key. For this MVP, please type your note into the text box below.")
                
                st.divider()
                with st.form("journal_form", clear_on_submit=True):
                    text_input = st.text_area("Or type your observation:", placeholder="E.g., 'Just finished a heavy lift.'", label_visibility="collapsed")
                    text_submit = st.form_submit_button("Synthesize Telemetry", use_container_width=True)
            
    with hc3:
        with st.popover("🍽️ Smart Meals", use_container_width=True):
            if st.session_state.get("latest_meal_analysis"):
                st.success("✅ Meal analyzed! View your clinical insights below.")
                if st.button("Scan Another Meal", key="reset_meal_pop", use_container_width=True):
                    st.session_state.latest_meal_analysis = None
                    st.rerun()
            else:
                st.caption("Snap a photo to estimate carbohydrates and metabolic impact.")
                
                # Prevent camera from loading until actively requested
                if not st.session_state.camera_active:
                    if st.button("📸 Open Camera Scanner", use_container_width=True):
                        st.session_state.camera_active = True
                        st.rerun()
                else:
                    food_image = st.camera_input("Food Scanner", label_visibility="collapsed")
                    if st.button("❌ Close Camera", use_container_width=True):
                        st.session_state.camera_active = False
                        st.rerun()
                        
                st.divider()
                with st.form("usda_search_form"):
                    db_search_query = st.text_input("Search USDA Database:", placeholder="E.g., 1 cup cooked quinoa")
                    db_search_submit = st.form_submit_button("Lookup Exact Macros", use_container_width=True)
                
    with hc4:
        with st.popover("☰ Menu", use_container_width=True):
            new_ctx = st.radio("Force Context:", ["Normal", "Stressed", "Sick", "Exercise", "Project", "Travel"], index=["Normal", "Stressed", "Sick", "Exercise", "Project", "Travel"].index(st.session_state.current_context))
            if st.button("Apply Context", use_container_width=True): st.session_state.current_context = new_ctx; st.session_state._toast = "Context saved!"; st.rerun()
            st.divider()
            
            st.markdown("##### 🔌 Integrations")
            st.markdown("**🩸 Nightscout CGM Sync**")
            if st.session_state.ns_url:
                # DYNAMIC UI: Validate if the connection is live or if it timed out to the simulator
                if is_real_cgm:
                    st.success("🟢 Connected & Streaming Live")
                else:
                    st.error("🔴 Connection Failed. (Simulated Data)")
                    st.caption("Your Nightscout server may have been sleeping. Try reconnecting to force a fresh ping.")
                    
                if st.button("Disconnect / Reconnect", key="dc_ns"):
                    st.session_state.ns_url = ""
                    st.session_state.ns_token = ""
                    st.cache_data.clear() # CACHE BUSTING
                    st.rerun()
            else:
                with st.form("ns_form"):
                    ns_url_input = st.text_input("Nightscout URL", placeholder="https://your-name.herokuapp.com")
                    ns_token_input = st.text_input("API Token (Optional)", type="password", placeholder="token-123")
                    if st.form_submit_button("Connect", use_container_width=True):
                        st.session_state.ns_url = ns_url_input
                        st.session_state.ns_token = ns_token_input
                        st.cache_data.clear() # CACHE BUSTING: Forces the backend to ignore the old failure and try pinging Nightscout again
                        st.rerun()
            
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
                if st.button("✅ Whoop Synced", use_container_width=True): st.rerun() 

st.divider()

# -----------------------------------------------------------------------------
# 4. EVENT PROCESSORS 
# -----------------------------------------------------------------------------
if 'text_submit' in locals() and text_submit and text_input:
    with st.spinner("Correlating subjective report with objective telemetry..."):
        try:
            ctx = {"context": st.session_state.current_context, "meetings": meeting_count, "glucose": int(latest_bg['Glucose_Value']), "trend": latest_bg['Trend']}
            sys = f"You are my elite AI clinical assistant. My telemetry: {json.dumps(ctx)}. Correlate my text. Speak to me as 'you'. Return JSON: 'reply', 'summary', 'scores':{{'bio_strain', 'cog_load'}}, 'impact_prediction'."
            st.session_state.journal_history = [ask_claude(sys, [{"role": "user", "content": text_input}])]
            st.session_state.mic_active = False # Cleanup state
            st.rerun() 
        except Exception as e: st.error(f"Failed: {e}")

if 'food_image' in locals() and food_image is not None:
    img_hash = hashlib.md5(food_image.getvalue()).hexdigest()
    if img_hash != st.session_state.get("last_img_hash"):
        st.session_state.last_img_hash = img_hash
        with st.spinner("Analyzing meal nutrition..."):
            try:
                b64 = base64.b64encode(food_image.getvalue()).decode("utf-8")
                sys = "You are my elite clinical nutritionist. Speak as 'you'. Return JSON: 'food_identified', 'estimated_carbs_g', 'glycemic_index', 'analysis'."
                meal_data = ask_claude(sys, [{"role": "user", "content": [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}}, {"type": "text", "text": "Analyze this meal for T1D."}]}])
                meal_data["source"] = "📸 Vision Estimate"; st.session_state.latest_meal_analysis = meal_data
                st.session_state.camera_active = False # Cleanup state
                st.rerun() 
            except Exception as e: st.error(f"Failed: {e}")

if 'db_search_submit' in locals() and db_search_submit and db_search_query:
    with st.spinner(f"Querying USDA for '{db_search_query}'..."):
        try:
            res = requests.get(f"https://api.nal.usda.gov/fdc/v1/foods/search?query={db_search_query}&api_key={st.secrets.get('USDA_API_KEY', 'DEMO_KEY')}&pageSize=1", timeout=10).json()
            if res.get("foods"):
                nutrients = res["foods"][0].get("foodNutrients", [])
                c, p, f = [next((n["value"] for n in nutrients if n["nutrientName"] == x), 0.0) for x in ["Carbohydrate, by difference", "Protein", "Total lipid (fat)"]]
                sys = f"You are my clinical nutritionist. I am querying {res['foods'][0].get('description')}. Macros per 100g: Carbs {c}g, Protein {p}g, Fat {f}g. Return JSON: 'food_identified', 'estimated_carbs_g', 'glycemic_index', 'analysis'."
                meal_data = ask_claude(sys, [{"role": "user", "content": "Analyze macros."}])
                meal_data["source"] = "🔍 USDA Verified (per 100g)"; st.session_state.latest_meal_analysis = meal_data
                st.session_state.camera_active = False # Cleanup state
                st.rerun()
            else: st.warning("No matches found.")
        except Exception as e: st.error(f"Failed: {e}")

# Render Processed Overlays directly onto the Main View
if st.session_state.get("journal_history"):
    entry = st.session_state.journal_history[0]
    st.success(f"**Agentic Insight:** {html.escape(entry.get('reply', ''))}")
    c1, c2, c3 = st.columns(3); c1.metric("🧬 Bio-Strain", f"{entry.get('scores',{}).get('bio_strain', 0)}/10"); c2.metric("🧠 Cog-Load", f"{entry.get('scores',{}).get('cog_load', 0)}/10"); c3.metric("📌 Status", html.escape(entry.get("summary", "")))
    st.info(f"**📉 Horizon Scan:** {html.escape(entry.get('impact_prediction', ''))}")
    if st.button("Dismiss Insight", use_container_width=True): st.session_state.journal_history = []; st.rerun()
    st.divider()

if st.session_state.get("latest_meal_analysis"):
    meal = st.session_state.latest_meal_analysis
    st.markdown(f"### 🍽️ Meal Analysis <span style='font-size:14px;color:gray;'>({meal.get('source')})</span>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns([1, 1, 2])
    m1.metric("Identified", meal.get("food_identified", "Unknown")); m2.metric("Carbs", f"{meal.get('estimated_carbs_g', 0)}g")
    gi = meal.get("glycemic_index", "Unknown")
    m3.metric("Glycemic Index", f"{'🔴' if gi.lower()=='high' else '🟡' if gi.lower()=='medium' else '🟢'} {gi}")
    st.info(f"**Clinical Insight:** {meal.get('analysis', '')}")
    if st.button("Dismiss Analysis", use_container_width=True): st.session_state.latest_meal_analysis = None; st.rerun()
    st.divider()

# -----------------------------------------------------------------------------
# 5. NAVIGATION & RENDER VIEWS
# -----------------------------------------------------------------------------
if "active_view" not in st.session_state: st.session_state.active_view = "Insights"
v_cols = st.columns(4)
for i, view in enumerate(["Insights", "Total Life Metrics", "Schedule", "Sleep"]):
    with v_cols[i]: 
        if st.button(view, use_container_width=True, type="primary" if st.session_state.active_view == view else "secondary"): st.session_state.active_view = view; st.rerun()
st.markdown("---")

if st.session_state.active_view == "Insights":
    with st.spinner("Compiling Insights..."):
        try:
            sys = f"You are my elite personal performance coach. Metrics: {st.session_state.current_context} Context, {meeting_count} meetings, Whoop Recovery: {w_rec}%, BG {int(latest_bg['Glucose_Value'])} ({latest_bg['Trend']}). Write insights. Speak directly to me using 'you'. Return JSON keys: 'bullet_1', 'bullet_2', 'bullet_3'."
            data = ask_claude(sys, [{"role": "user", "content": "Generate my insights now."}])
            st.info(f"**1. Load & Resilience:** {html.escape(data.get('bullet_1', ''))}")
            st.warning(f"**2. Metabolic State:** {html.escape(data.get('bullet_2', ''))}")
            st.success(f"**3. Recommended Action:** {html.escape(data.get('bullet_3', ''))}")
        except Exception as e: st.error(f"Failed: {e}")

elif st.session_state.active_view == "Total Life Metrics":
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
        st.success(f"**🤖 Agentic Synthesis:** {get_ai_chart_summary('Glucose', tw, metrics_str)}")

elif st.session_state.active_view == "Schedule":
    h1, h2, h3, h4 = st.columns(4)
    with h1: st.markdown(render_adaptive_schedule_card("1 HOUR", '✈️ SHIFTING' if st.session_state.current_context == 'Travel' else '🟢 SAFE'), unsafe_allow_html=True)
    with h2: st.markdown(render_adaptive_schedule_card("4 HOURS", '🟡 CAUTION' if st.session_state.current_context == 'Stressed' else '🟢 CLEAR'), unsafe_allow_html=True)
    with h3: st.markdown(render_adaptive_schedule_card("24 HOURS", '🟢 GOOD'), unsafe_allow_html=True)
    with h4: st.markdown(render_adaptive_schedule_card("MEETINGS", f"{meeting_count} ({'🔴 CRITICAL' if meeting_count>=7 else '🟡 ELEVATED' if meeting_count>=4 else '🟢 LIGHT'})"), unsafe_allow_html=True)
    st.info(f"**Agentic Insight:** The Risk Engine is factoring in **{meeting_count} meetings** to adjust glycemic sensitivity.")

elif st.session_state.active_view == "Sleep":
    if st.session_state.whoop_token and whoop_metrics:
        st.markdown("##### 💤 Sleep Metrics")
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
            st.success(f"**🤖 Agentic Synthesis:** {get_ai_chart_summary(f'Overnight Glucose (with {w_sleep}% Sleep)', tw, metrics_str)}")
    else: st.info("🔗 Open ☰ Menu to connect Whoop.")

st.markdown(styles.FOOTER_HTML, unsafe_allow_html=True)
