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
    page_icon="assets/tldh_logo.png", # Points to your local asset folder
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
# 3. CONTEXT STATE MANAGEMENT
# -----------------------------------------------------------------------------
if "current_context" not in st.session_state:
    st.session_state.current_context = "Normal"

# Sidebar remains as a fallback/info panel
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
        # We pass the context directly into logic to trigger the 'Chaos Injector'
        raw_data = logic.fetch_health_data()
        full_data, status, color_hex, reason = logic.calc_glycemic_risk(raw_data, st.session_state.current_context)
        latest = full_data.iloc[-1]
except Exception as e:
    logger.error(f"Data loading failed: {e}", exc_info=True)
    st.error("Oops! Something went wrong loading your health data.")
    st.stop()

# -----------------------------------------------------------------------------
# 5. HEADER UI (Unified Control Bar)
# -----------------------------------------------------------------------------
safe_status = html.escape(str(status))
safe_reason = html.escape(str(reason))
safe_color_hex = html.escape(str(color_hex))
safe_context = html.escape(str(st.session_state.current_context))

# 1. Title & Logo Row
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

# 2. THE CONTROL BOX (Fixed Layout)
with st.container(border=True):
    # Using sub-columns to handle horizontal alignment of pills correctly
    p_col1, p_col2, p_col3, p_spacer = st.columns([1.5, 2, 3, 5])
    
    with p_col1:
        st.markdown("<p style='font-weight: 700; color: var(--text-secondary); text-transform: uppercase; font-size: 0.85rem; letter-spacing: 1px; margin-top: 10px;'>Live Status</p>", unsafe_allow_html=True)
    
    with p_col2:
        # Dynamic Risk Pill
        st.markdown(f'<div class="gov-pill" style="background-color: {safe_color_hex}; color: #000000; width: 100%; text-align: center;">{safe_status}</div>', unsafe_allow_html=True)
    
    with