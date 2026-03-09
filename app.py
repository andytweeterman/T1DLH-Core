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

# Custom CSS for the Glowing Pill
st.markdown("""
    <style>
    /* Target the 2nd column specifically inside the bordered header container */
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"]:nth-of-type(2) button {
        background: linear-gradient(135deg, #8B5CF6, #6D28D9) !important;
        color: white !important;
        border: none !important;
        border-radius: 50px !important;
        animation: pulse-purple 2s infinite !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"]:nth-of-type(2) button * {
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
    active_model_name = 'claude-sonnet-4-6' 
    model_status = "✨ CLAUDE SONNET 4.6 ONLINE"
except Exception as e:
    st.error(f"⚠️ API Critical Failure. Details: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 2.5 AI SYNTHESIS HELPERS
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def get_ai_chart_summary(chart_type, time_window, avg_val, min_val, max_val, std_val, latest_val):
    """Caches and generates an agentic summary of visual chart data."""
    system_instruction = f"""
    You are my elite personal performance coach. Analyze my {chart_type} summary data over the last {time_window}.
    Metrics:
    - Average Glucose: {avg_val} mg/dL
    - Min Glucose: {min_val} mg/dL
    - Max Glucose: {max_val} mg/dL
    - Volatility (Std Dev): {std_val} mg/dL
    - Latest Reading: {latest_val} mg/dL
    
    Provide a 2-sentence highly actionable synthesis of what this means for my performance and metabolic load. Speak directly to me using "you" and "your". Tone should be warm, personal, and sharp. NEVER refer to me as "the patient" or "the user". Do not use markdown formatting outside of bolding.
    """
    try:
        response = client.messages.create(
            model=active_model_name,
            max_tokens=150,
            system=system_instruction,
            messages=[{"role": "user", "content": "Synthesize this trend."}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return "AI Analysis temporarily unavailable."

# -----------------------------------------------------------------------------
# 3. CONTEXT STATE & AUTH LOGIC
# -----------------------------------------------------------------------------
if "current_context" not in st.session_state:
    st.session_state.current_context = "Normal"

if "whoop_token" not in st.session_state:
    st.session_state.whoop_token = None

if not st.session_state.whoop_token:
    st.session_state.whoop_token = whoop.get_valid_access_token()

if "code" in st.query_params and not st.session_state.whoop_token:
    with st.spinner("Finalizing Whoop Connection..."):
        query_state = st.query_params.get("state")
        session_state = st.session_state.get("oauth_state")

        if query_state and session_state and query_state == session_state:
            auth_code = st.query_params["code"]
            token_data = whoop.get_access_token(auth_code)

            if token_data and "access_token" in token_data:
                st.session_state.whoop_token = token_data.get("access_token")
                whoop.save_tokens(token_data) 
                st.query_params.clear() 
                st.rerun()
            else:
                st.error("Whoop Auth Failed. Please try again.")
        else:
            st.error("Invalid or missing state parameter. Authentication failed.")
            st.query_params.clear()

# -----------------------------------------------------------------------------
# 4. DATA LOADING
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300)
def get_cached_health_data():
    return logic.fetch_health_data()

@st.cache_data(ttl=60)
def get_cached_glycemic_risk(df, context, whoop_data=None, meeting_count=0, speaker_mode=False, owm_api_key=""):
    return logic.calc_glycemic_risk(df, context, whoop_data, meeting_count, speaker_mode, owm_api_key)

try:
    with st.spinner("Syncing Health & Schedule Data..."):
        whoop_metrics = None
        if st.session_state.whoop_token:
            whoop_metrics = whoop.fetch_whoop_recovery(st.session_state.whoop_token)
        
        meeting_count, speaker_mode = calendar_sync.fetch_calendar_context()
        raw_data = get_cached_health_data()
        
        full_data, status, color_hex, reason = get_cached_glycemic_risk(
            raw_data, 
            st.session_state.current_context,
            whoop_data=whoop_metrics,
            meeting_count=meeting_count,
            speaker_mode=speaker_mode,
            owm_api_key=st.secrets.get("OWM_API_KEY", "")
        )
        latest = full_data.iloc[-1]
except Exception as e:
    st.error("Data loading failed. Please try again.")

# -----------------------------------------------------------------------------
# 5. HEADER UI & HAMBURGER MENU
# -----------------------------------------------------------------------------
safe_status = html.escape(str(status))
safe_reason = html.escape(str(reason)) 

st.markdown(f"""
    <div style="margin-top: 5px; margin-bottom: 20px;">
        <span style="font-size: 32px; font-weight: 800; background: var(--accent-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Total Life Download Hub</span><br>
        <span style="color: var(--text-secondary); font-weight: 600; font-size: 1.1rem;">Agentic Risk Management Engine</span>
    </div>
""", unsafe_allow_html=True)

with st.container(border=True):
    hc1, hc2, hc3, hc4 = st.columns([3.5, 2.5, 2.5, 1.5])
    
    with hc1:
        st.markdown("<p style='font-weight: 700; color: var(--text-secondary); text-transform: uppercase; font-size: 0.75rem; letter-spacing: 1px; margin-top: 5px; margin-bottom: 8px;'>Total Life Drivers</p>", unsafe_allow_html=True)
        
        # Cleanly parse the reason string into individual vector tags
        parts = safe_reason.split("|")
        vectors = []
        for part in parts:
            clean_part = re.sub(r'Hyperglycemic risk detected\.?|Hypoglycemic risk detected\.?|Compounded Strain Detected\!|System nominal\.?', '', part)
            clean_part = clean_part.replace('()', '').replace('(', '').replace(')', '').strip()
            if clean_part:
                vectors.append(html.escape(clean_part))
        
        # Build beautifully styled pill buttons for the Drivers
        tags_html = ""
        for t in vectors[:3]:
            # Assign colors based on risk severity logic
            if "🔴" in t or "🔥" in t or "❄️" in t:
                bg, text, border = "rgba(237, 135, 150, 0.15)", "#ED8796", "rgba(237, 135, 150, 0.4)"
            elif "🟡" in t or "⚡" in t or "💤" in t:
                bg, text, border = "rgba(238, 212, 159, 0.15)", "#EED49F", "rgba(238, 212, 159, 0.4)"
            elif "🟢" in t or "☁️" in t:
                bg, text, border = "rgba(166, 218, 149, 0.15)", "#A6DA95", "rgba(166, 218, 149, 0.4)"
            else:
                bg, text, border = "rgba(139, 92, 246, 0.15)", "#B4A1F5", "rgba(139, 92, 246, 0.4)"
            
            # Make the text friendly and title cased
            friendly_text = t.replace("BENIGN ENVIRONMENT", "CLEAR WEATHER").title()
            
            tags_html += f"<div style='display:inline-flex; align-items:center; background-color:{bg}; color:{text}; padding:4px 12px; border-radius:20px; font-size:0.75rem; font-weight:700; margin-right:8px; margin-bottom:8px; border:1px solid {border}; box-shadow: 0 2px 5px rgba(0,0,0,0.1);'>{friendly_text}</div>"
        
        st.markdown(tags_html, unsafe_allow_html=True)
    
    with hc2:
        with st.popover("Smart Health Companion", use_container_width=True):
            st.markdown("Ask a question or log how you are feeling. The AI will correlate your input with your live telemetry.")
            st.caption("Tap the mic to log a voice note.")
            audio_bytes = audio_recorder(
                text="",
                recording_color="#ED8796",
                neutral_color="#8B5CF6",
                icon_size="2x"
            )
            
    with hc3:
        with st.popover("🍽️ Smart Meals", use_container_width=True):
            st.markdown("Snap a photo to estimate carbohydrates and metabolic impact.")
            food_image = st.camera_input("Food Scanner", label_visibility="collapsed")
            
            st.divider()
            st.markdown("##### 🔍 Database Lookup")
            st.caption("Pull verified macros from the USDA FoodData Central database.")
            with st.form("usda_search_form"):
                db_search_query = st.text_input("Search Food:", placeholder="E.g., 1 cup cooked quinoa")
                db_search_submit = st.form_submit_button("Lookup Macros", use_container_width=True)
                
    with hc4:
        with st.popover("☰ MENU", use_container_width=True):
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
            
            st.markdown("##### 🔌 Integrations")
            if not st.session_state.whoop_token:
                oauth_state = secrets.token_urlsafe(16)
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

st.divider()

# -----------------------------------------------------------------------------
# 5.1 EVENT PROCESSORS (Audio & Images & Database)
# -----------------------------------------------------------------------------

# A. Process Audio Dump logic
if 'audio_bytes' in locals() and audio_bytes:
    audio_hash = hashlib.md5(audio_bytes).hexdigest()
    if audio_hash != st.session_state.get("last_audio_hash"):
        st.session_state.last_audio_hash = audio_hash
        with st.spinner("Processing Voice Dump and Correlating Telemetry..."):
            st.error("🎙️ **Claude API Limitation:** Anthropic does not currently accept raw audio files. To use voice notes, please integrate a transcription service (like OpenAI Whisper) to convert `audio_bytes` to text first.")

# B. Process Smart Meals logic (CAMERA)
if 'food_image' in locals() and food_image is not None:
    image_bytes = food_image.getvalue()
    img_hash = hashlib.md5(image_bytes).hexdigest()
    
    if img_hash != st.session_state.get("last_img_hash"):
        st.session_state.last_img_hash = img_hash
        
        with st.spinner("Analyzing meal nutrition and estimating carbohydrates..."):
            try:
                base64_image = base64.b64encode(image_bytes).decode("utf-8")
                
                system_instruction = """
                You are my elite personal clinical nutritionist managing my Type 1 Diabetes.
                Analyze the food image I provided. Estimate the total carbohydrates in grams and the glycemic index.
                Speak directly to me using "you" and "your". Tone should be warm, personal, and highly actionable. NEVER refer to me as "the patient" or "the user".
                Return ONLY a valid JSON object with EXACTLY these keys. Do not include markdown or extra text:
                - "food_identified": "Short description of the meal."
                - "estimated_carbs_g": 45
                - "glycemic_index": "High", "Medium", or "Low"
                - "analysis": "A concise 2-sentence clinical breakdown of how this meal will impact my glucose."
                """
                
                response = client.messages.create(
                    model=active_model_name,
                    max_tokens=400,
                    system=system_instruction,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": base64_image,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": "Analyze this meal for my Type 1 Diabetes management."
                                }
                            ],
                        }
                    ]
                )
                
                clean_text = response.content[0].text.strip()
                markdown_fence = chr(96) * 3
                clean_text = clean_text.replace(f"{markdown_fence}json", "").replace(markdown_fence, "").strip()
                
                meal_data = json.loads(clean_text)
                meal_data["source"] = "📸 Vision Estimate"
                st.session_state.latest_meal_analysis = meal_data
                
            except Exception as e:
                st.error(f"Meal Analysis failed. Details: {e}")

# C. Process Database Lookup (USDA)
if 'db_search_submit' in locals() and db_search_submit and db_search_query:
    with st.spinner(f"Querying USDA FoodData Central for '{db_search_query}'..."):
        try:
            usda_key = st.secrets.get("USDA_API_KEY", "DEMO_KEY")
            url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={db_search_query}&api_key={usda_key}&pageSize=1"
            
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            data = res.json()
            
            if data.get("foods"):
                food = data["foods"][0]
                food_name = food.get("description", "Unknown Food")
                nutrients = food.get("foodNutrients", [])
                
                carbs = next((n["value"] for n in nutrients if n["nutrientName"] == "Carbohydrate, by difference"), 0.0)
                protein = next((n["value"] for n in nutrients if n["nutrientName"] == "Protein"), 0.0)
                fat = next((n["value"] for n in nutrients if n["nutrientName"] == "Total lipid (fat)"), 0.0)
                
                system_instruction = f"""
                You are my elite personal clinical nutritionist managing my Type 1 Diabetes.
                I am querying the USDA database for: {food_name}. 
                Here are the exact macros per 100g: Carbs: {carbs}g, Protein: {protein}g, Fat: {fat}g.
                
                Speak directly to me using "you" and "your". Tone should be warm, personal, and highly actionable.
                Return ONLY a valid JSON object with EXACTLY these keys:
                - "food_identified": "{food_name.title()}"
                - "estimated_carbs_g": {int(carbs)}
                - "glycemic_index": "Database Verified"
                - "analysis": "A concise 2-sentence clinical breakdown of how this specific macro profile (factoring in the fat and protein) will impact my glucose absorption."
                """
                
                response = client.messages.create(
                    model=active_model_name,
                    max_tokens=400,
                    system=system_instruction,
                    messages=[{"role": "user", "content": "Provide clinical insight on these exact USDA macros."}]
                )
                
                clean_text = response.content[0].text.strip()
                markdown_fence = chr(96) * 3
                clean_text = clean_text.replace(f"{markdown_fence}json", "").replace(markdown_fence, "").strip()
                
                meal_data = json.loads(clean_text)
                meal_data["source"] = "🔍 USDA Verified (per 100g)"
                st.session_state.latest_meal_analysis = meal_data
            else:
                st.warning(f"No exact matches found in USDA database for '{db_search_query}'. Try a simpler term.")
                
        except Exception as e:
            st.error(f"Database lookup failed. Details: {e}")

# D. Display Meal Analysis Result
if st.session_state.get("latest_meal_analysis"):
    meal = st.session_state.latest_meal_analysis
    
    st.markdown("### 🍽️ Smart Meals Analysis")
    st.caption(f"Data Source: {meal.get('source', 'Unknown')}")
    
    m_c1, m_c2, m_c3 = st.columns([1, 1, 2])
    m_c1.metric("Identified Meal", meal.get("food_identified", "Unknown"))
    m_c2.metric("Estimated Carbs", f"{meal.get('estimated_carbs_g', 0)}g")
    
    gi = meal.get("glycemic_index", "Unknown")
    gi_color = "🔴" if gi.lower() == "high" else "🟡" if gi.lower() == "medium" else "🟢"
    m_c3.metric("Glycemic Index / Status", f"{gi_color} {gi}")
    
    st.info(f"**Clinical Insight:** {meal.get('analysis', '')}")
    
    if st.button("Dismiss Analysis", use_container_width=True):
        st.session_state.latest_meal_analysis = None
        st.rerun()
        
    st.divider()

# -----------------------------------------------------------------------------
# 6. NAVIGATION
# -----------------------------------------------------------------------------
if "active_view" not in st.session_state:
    st.session_state.active_view = "Insights"

c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("Insights", use_container_width=True, type="primary" if st.session_state.active_view == "Insights" else "secondary"):
        st.session_state.active_view = "Insights"
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

# --- VIEW: INSIGHTS (BLUF) ---
if st.session_state.active_view == "Insights":
    st.markdown("### 📋 Insights")
    st.markdown("A tactical synthesis of your readiness, load, and biology.")

    with st.spinner("Compiling Insights..."):
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
            You are my elite personal performance coach. Write your insights based on my current metrics:
            - Day Type: {day_type}
            - Schedule Density: {meeting_count} meetings.
            - Whoop Metrics: {rec_score}% Recovery, {sleep_perf}% Sleep, {strain} Day Strain.
            - Current Glucose: {bg_val} mg/dL, Trend: {trend}.
            - Active Context: {st.session_state.current_context}
            
            Speak directly to me using "you" and "your". Tone should be warm, personal, and highly actionable. NEVER refer to me as "the patient" or "the user".
            Return ONLY a valid JSON object with the exact keys: "bullet_1", "bullet_2", "bullet_3". Do not include markdown formatting or extra text.
            """

            response = client.messages.create(
                model=active_model_name,
                max_tokens=500,
                system=system_instruction,
                messages=[
                    {"role": "user", "content": "Generate my insights now."}
                ]
            )
            
            clean_text = response.content[0].text.strip()
            markdown_fence = chr(96) * 3
            clean_text = clean_text.replace(f"{markdown_fence}json", "").replace(markdown_fence, "").strip()
            
            insights_data = json.loads(clean_text)

            st.info(f"**1. Load & Resilience:** {html.escape(insights_data.get('bullet_1', ''))}")
            st.warning(f"**2. Metabolic State:** {html.escape(insights_data.get('bullet_2', ''))}")
            st.success(f"**3. Recommended Action:** {html.escape(insights_data.get('bullet_3', ''))}")

        except Exception as e:
            st.error(f"Failed to generate insights. Details: {e}")

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
    
    with st.spinner("Synthesizing Trend..."):
        avg_g = int(plot_data['Glucose_Value'].mean())
        min_g = int(plot_data['Glucose_Value'].min())
        max_g = int(plot_data['Glucose_Value'].max())
        std_g = int(plot_data['Glucose_Value'].std())
        lat_g = int(plot_data['Glucose_Value'].iloc[-1])
        
        summary = get_ai_chart_summary("Glucose/CGM", time_window, avg_g, min_g, max_g, std_g, lat_g)
        st.success(f"**🤖 Agentic Synthesis:** {summary}")

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

# --- VIEW C: ASSISTANT (Now Integrated via Popovers) ---
# Check if the user submitted text via the Smart Health Companion form (Text Fallback)
with st.sidebar:
    st.markdown("### 🧬 Smart Health Companion (Fallback)")
    with st.form("journal_form", clear_on_submit=True):
        text_input = st.text_area("Life Download (Text Fallback):", placeholder="E.g., 'Just finished rebuilding the deck doors. Legs feel heavy.'")
        if st.form_submit_button("Analyze Load", type="primary") and text_input:
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
                    You are my elite clinical AI assistant managing my physiological and cognitive load.
                    Here is my real-time hardware telemetry: {json.dumps(live_context)}
                    
                    Correlate my subjective report with my objective telemetry. 
                    Speak directly to me using "you" and "your". Tone should be warm, personal, and highly actionable. NEVER refer to me as "the patient" or "the user".
                    Return ONLY a valid JSON object with EXACTLY these keys. Do not include markdown or extra text:
                    - "reply": "A highly actionable, context-aware response under 40 words. No medical jargon."
                    - "summary": "A 3-word summary."
                    - "scores": {{"bio_strain": 5, "cog_load": 5}}
                    - "impact_prediction": "A 1-sentence prediction of how my current state and telemetry will impact my glucose over the next 2 hours."
                    """
                    
                    response = client.messages.create(
                        model=active_model_name,
                        max_tokens=800,
                        system=system_instruction,
                        messages=[
                            {"role": "user", "content": text_input}
                        ]
                    )
                    
                    clean_text = response.content[0].text.strip()
                    markdown_fence = chr(96) * 3
                    clean_text = clean_text.replace(f"{markdown_fence}json", "").replace(markdown_fence, "").strip()
                    
                    parsed = json.loads(clean_text)
                    parsed["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    if "journal_history" not in st.session_state: st.session_state.journal_history = []
                    st.session_state.journal_history.insert(0, parsed)
                except Exception as e: 
                    st.error(f"Correlation Analysis failed. Details: {e}")

# Render Text Fallback Result if it exists
if st.session_state.get("journal_history"):
    entry = st.session_state.journal_history[0]
    st.markdown("### 🧬 Smart Companion Correlation")
    st.success(f"**Agentic Insight:** {html.escape(entry.get('reply', ''))}")
    
    sc = entry.get("scores", {"bio_strain": 0, "cog_load": 0})
    c1, c2, c3 = st.columns(3)
    c1.metric("🧬 Bio-Strain", f"{sc.get('bio_strain', 0)}/10")
    c2.metric("🧠 Cog-Load", f"{sc.get('cog_load', 0)}/10")
    c3.metric("📌 Status", html.escape(entry.get("summary", "")))
    st.info(f"**📉 Horizon Scan:** {html.escape(entry.get('impact_prediction', ''))}")
    
    if st.button("Dismiss Feedback", key="dismiss_journal"):
        st.session_state.journal_history = []
        st.rerun()

# --- VIEW D: SLEEP IMPACT ---
elif st.session_state.active_view == "Sleep":
    st.markdown("### 🌙 Sleep & Recovery Correlation")
    if st.session_state.whoop_token and whoop_metrics:
        score_data = whoop_metrics.get('score', {})
        sleep_perf = score_data.get('sleep_performance_percentage', 85)
        recovery_score = score_data.get('recovery_score', 0)
        hrv = int(score_data.get('hrv_rmssd_milli_seconds', 0))
        rhr = int(score_data.get('resting_heart_rate_beats_per_minute', 0))
        
        s_time_window = st.radio("Overnight Range", ["4h", "8h", "12h"], index=1, horizontal=True, label_visibility="collapsed")
        s_row_mapping = {"4h": 48, "8h": 96, "12h": 144}
        overnight_df = full_data.tail(s_row_mapping[s_time_window])
        
        std_dev = int(overnight_df['Glucose_Value'].std())
        
        st.markdown("##### 💤 Whoop Recovery Metrics")
        s_col1, s_col2, s_col3, s_col4, s_col5 = st.columns(5)
        with s_col1: st.metric("Sleep Perf", f"{sleep_perf}%", delta="Restorative" if sleep_perf > 80 else "Deficit", delta_color="normal" if sleep_perf > 80 else "inverse")
        with s_col2: st.metric("Recovery", f"{recovery_score}%", delta="Ready" if recovery_score > 66 else "Strained", delta_color="normal" if recovery_score > 66 else "inverse")
        with s_col3: st.metric("HRV", f"{hrv} ms")
        with s_col4: st.metric("Resting HR", f"{rhr} bpm")
        with s_col5: st.metric("Overnight Volatility", f"±{std_dev} mg/dL", delta="Stable" if std_dev < 15 else "Erratic", delta_color="normal" if std_dev < 15 else "inverse")
        
        st.markdown("---")
        
        st.markdown("##### 🩸 Overnight Blood Sugar")
        sleep_fig = go.Figure()
        sleep_fig.add_trace(go.Scatter(x=overnight_df['Timestamp'], y=overnight_df['Glucose_Value'], mode='lines+markers', line=dict(color='#A855F7', width=4)))
        sleep_fig.add_hrect(y0=70, y1=180, line_width=0, fillcolor="rgba(166, 218, 149, 0.1)", opacity=0.5)
        sleep_fig.add_hline(y=70, line_dash="dash", line_color="#ED8796", annotation_text="LOW GATES")
        
        sleep_fig.update_layout(
            height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='gray'),
            xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True),
            margin=dict(l=0, r=0, t=30, b=0), yaxis_title="mg/dL"
        )
        st.plotly_chart(sleep_fig, use_container_width=True, config={'displayModeBar': False})
        
        with st.spinner("Synthesizing Overnight Trend..."):
            avg_g = int(overnight_df['Glucose_Value'].mean())
            min_g = int(overnight_df['Glucose_Value'].min())
            max_g = int(overnight_df['Glucose_Value'].max())
            std_g = int(overnight_df['Glucose_Value'].std())
            lat_g = int(overnight_df['Glucose_Value'].iloc[-1])
            
            summary = get_ai_chart_summary(f"Overnight Glucose (with {sleep_perf}% Sleep Performance and {recovery_score}% Recovery)", s_time_window, avg_g, min_g, max_g, std_g, lat_g)
            st.success(f"**🤖 Agentic Synthesis:** {summary}")
    else:
        st.info("🔗 Open the ☰ MENU above to connect Whoop and enable Sleep Impact correlation.")

st.markdown(styles.FOOTER_HTML, unsafe_allow_html=True)