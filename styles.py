import streamlit as st

def apply_theme():
    custom_css = """
    <style>
        /* HIDE STREAMLIT UI */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}

        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

        :root {
            /* Sleek Light Theme */
            --bg-color: #F8F9FA;
            --card-bg: #FFFFFF;
            --text-primary: #111827;
            --text-secondary: #6B7280;
            
            /* The Option 2 Logo Gradient */
            --accent-start: #8A2BE2; /* Deep Purple */
            --accent-end: #4169E1;   /* Royal Blue */
            --accent-gradient: linear-gradient(135deg, var(--accent-start), var(--accent-end));
            
            --border: #E5E7EB;
            --card-shadow: 0 10px 40px -10px rgba(0,0,0,0.08);
        }

        @media (prefers-color-scheme: dark) {
            :root {
                /* Deep Dark Theme matching the logo's modern aesthetic */
                --bg-color: #0F172A;
                --card-bg: #1E293B;
                --text-primary: #F8FAFC;
                --text-secondary: #94A3B8;
                
                /* Brighter gradient for dark mode pop */
                --accent-start: #A855F7; 
                --accent-end: #3B82F6;
                --accent-gradient: linear-gradient(135deg, var(--accent-start), var(--accent-end));
                
                --border: #334155;
                --card-shadow: 0 10px 40px -10px rgba(0,0,0,0.4);
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
            background: var(--accent-gradient) !important; /* APPLIED BRAND GRADIENT */
            color: #FFFFFF !important;
            border-radius: 20px !important;
            border: none !important;
            box-shadow: var(--card-shadow) !important;
            font-weight: 800 !important;
            transition: transform 0.2s ease, filter 0.2s ease !important;
        }
        
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
            box-shadow: 0 4px 15px rgba(138, 43, 226, 0.1) !important; /* Subtle purple glow */
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
            font-weight: 800;
            display: inline-block;
            margin-top: 5px;
            letter-spacing: 1px;
            box-shadow: var(--card-shadow);
            text-transform: uppercase;
        }
        
        /* General Fixes */
        .block-container { padding-top: 1.5rem !important; }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

FOOTER_HTML = """
<div style="text-align: center; margin-top: 60px; padding-bottom: 24px; border-top: 1px solid rgba(128,128,128,0.2); color: var(--text-secondary); font-size: 13px; font-family: 'Inter', sans-serif; letter-spacing: 1.5px;">
    TOTAL LIFE DOWNLOAD HUB • AGENTIC RISK MANAGEMENT
</div>
"""