import streamlit as st

def apply_theme():
    # We use CSS variables and media queries so the Apple OS handles the light/dark switching natively.
    custom_css = """
    <style>
        /* HIDE STREAMLIT HEADER AND FOOTER */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}

        /* IMPORT PREMIUM FONT */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

        /* DEFINE SYSTEM COLOR VARIABLES (Light Mode Default) */
        :root {
            --bg-color: #FFFFFF;
            --card-bg: #F0F2F6;
            --text-primary: #000000;
            --text-secondary: #555555;
            --accent: #0055AA;
            --border: #E0E0E0;
            --card-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.05);
        }

        /* DEFINE SYSTEM COLOR VARIABLES (Dark Mode Override) */
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

        /* APPLY FONT AND BG GLOBALLY */
        html, body, [class*="css"], .stApp {
            font-family: 'Inter', sans-serif !important;
            -webkit-font-smoothing: antialiased;
            background-color: var(--bg-color) !important;
            color: var(--text-primary) !important;
        }

        /* BUTTON GLOW UP (Tabs & Actions) */
        button[kind="primary"] {
            background-color: var(--accent) !important;
            color: #FFFFFF !important; 
            border-radius: 20px !important;
            border: none !important;
            box-shadow: var(--card-shadow) !important;
            font-weight: 800 !important;
            transition: transform 0.2s ease, filter 0.2s ease !important;
        }
        
        button[kind="primary"] p, button[kind="primary"] div {
            color: #FFFFFF !important;
        }

        button[kind="primary"]:hover {
            transform: scale(1.02);
            filter: brightness(1.1);
        }

        button[kind="secondary"] {
            background-color: var(--card-bg) !important;
            border: 1px solid rgba(128, 128, 128, 0.1) !important;
            border-radius: 20px !important;
            box-shadow: var(--card-shadow) !important;
            color: var(--text-secondary) !important;
            font-weight: 600 !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        }
        
        button[kind="secondary"] p, button[kind="secondary"] div {
            color: var(--text-secondary) !important;
        }

        button[kind="secondary"]:hover {
            transform: scale(1.02);
            box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.15) !important;
        }
        
        button[kind="secondary"]:hover p {
            color: var(--text-primary) !important;
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
        
        [data-testid="stMetric"]:hover {
            transform: scale(1.02);
        }

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

        /* PREMIUM STATUS PILL */
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

        /* MOBILE RESPONSIVENESS */
        @media (max-width: 430px) {
            [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
                gap: 12px !important;
            }
            [data-testid="column"], [data-testid="stColumn"] {
                min-width: 40% !important;
                flex: 1 1 calc(50% - 12px) !important;
            }
            h1 { font-size: 1.8rem !important; }
        }

        button, input, [role="button"] {
            min-height: 48px !important;
        }

        /* GENERAL FIXES */
        [data-testid="stChatMessageContent"] *, 
        [data-testid="stMarkdownContainer"] p, 
        .streamlit-expanderContent p {
            color: var(--text-primary) !important;
        }

        code, pre {
            background-color: var(--card-bg) !important;
            color: var(--accent) !important;
            border-radius: 6px !important;
            padding: 2px 6px !important;
            font-family: monospace !important;
        }

        .block-container {
            padding-top: 1rem !important;
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

FOOTER_HTML = """
<div style="text-align: center; margin-top: 60px; padding-top: 24px; border-top: 1px solid rgba(128,128,128,0.2); color: var(--text-secondary); font-size: 13px; font-family: 'Inter', sans-serif; letter-spacing: 1.5px;">
    SMART HEALTH COMPANION • DAILY WELLNESS TRACKER
</div>
"""