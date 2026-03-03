import streamlit as st

def apply_theme():
    custom_css = """
    <style>
        /* HIDE STREAMLIT UI */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}

        @import url('[https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap](https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap)');

        :root {
            --bg-color: #FFFFFF;
            --card-bg: #F0F2F6;
            --text-primary: #000000;
            --text-secondary: #555555;
            --accent: #0055AA;
            --border: #E0E0E0;
            --card-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.05);
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --bg-color: #24273A;
                --card-bg: #363A4F;
                --text-primary: #CAD3F5;
                --text-secondary: #A5ADCB;
                --accent: #8AADF4;
                --border: #494D64;
                --card-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
            }
        }

        html, body, [class*="css"], .stApp {
            font-family: 'Inter', sans-serif !important;
            -webkit-font-smoothing: antialiased;
            background-color: var(--bg-color) !important;
            color: var(--text-primary) !important;
        }

        /* -----------------------
           BUTTON CSS OVERRIDES
           ----------------------- */
        
        /* 1. PRIMARY BUTTONS (Submit & Active Tabs) */
        button[kind="primary"], div.stButton > button[kind="primary"] {
            background-color: var(--accent) !important;
            color: #FFFFFF !important;  /* FORCE WHITE TEXT */
            border-radius: 20px !important;
            border: none !important;
            box-shadow: var(--card-shadow) !important;
            font-weight: 800 !important;
            transition: transform 0.2s ease, filter 0.2s ease !important;
        }
        
        /* Catch inner span/p text to ensure it stays white */
        button[kind="primary"] *, div.stButton > button[kind="primary"] * {
            color: #FFFFFF !important;
        }

        button[kind="primary"]:hover {
            transform: scale(1.02);
            filter: brightness(1.1);
        }

        /* 2. SECONDARY BUTTONS (Inactive Tabs) */
        button[kind="secondary"] {
            background-color: var(--card-bg) !important;
            border: 1px solid rgba(128, 128, 128, 0.1) !important;
            border-radius: 20px !important;
            box-shadow: var(--card-shadow) !important;
            color: var(--text-secondary) !important;
            font-weight: 600 !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        }
        
        button[kind="secondary"] * {
            color: var(--text-secondary) !important;
        }

        button[kind="secondary"]:hover {
            transform: scale(1.02);
        }
        
        /* METRIC CARDS */
        [data-testid="stMetric"] {
            background-color: var(--card-bg);
            padding: 20px;
            border-radius: 20px;
            border: 1px solid rgba(128, 128, 128, 0.1);
            box-shadow: var(--card-shadow);
            transition: transform 0.2s ease;
        }
        [data-testid="stMetric"]:hover { transform: scale(1.02); }

        [data-testid="stMetricValue"] {
            color: var(--text-primary) !important;
            font-weight: 800 !important;
            font-size: 2rem !important;
        }
        [data-testid="stMetricLabel"] {
            color: var(--text-secondary) !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            font-size: 0.8rem !important;
        }

        /* PILLS */
        .gov-pill {
            padding: 8px 24px;
            border-radius: 30px;
            color: var(--bg-color);
            background-color: var(--text-primary);
            font-weight: 800;
            display: inline-block;
            margin-top: 5px;
            letter-spacing: 1px;
            box-shadow: var(--card-shadow);
            text-transform: uppercase;
        }
        
        /* General Fixes */
        .block-container { padding-top: 1rem !important; }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

FOOTER_HTML = """
<div style="text-align: center; margin-top: 60px; padding-top: 24px; border-top: 1px solid rgba(128,128,128,0.2); color: var(--text-secondary); font-size: 13px; font-family: 'Inter', sans-serif; letter-spacing: 1.5px;">
    SMART HEALTH COMPANION • DAILY WELLNESS TRACKER
</div>
"""