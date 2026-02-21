import streamlit as st

def apply_theme():
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = True 

    # Catppuccin Macchiato Color Palette
    if st.session_state["dark_mode"]:
        theme = {
            "BG_COLOR": "#24273A",        
            "CARD_BG": "#363A4F",         
            "TEXT_PRIMARY": "#CAD3F5",    
            "TEXT_SECONDARY": "#A5ADCB",  
            "CHART_TEMPLATE": "plotly_dark",
            "CHART_FONT": "#CAD3F5",
            "ACCENT": "#8AADF4",          
            "BORDER": "#494D64"           
        }
    else:
        # Light Mode Fallback
        theme = {
            "BG_COLOR": "#eff1f5",
            "CARD_BG": "#e6e9ef",
            "TEXT_PRIMARY": "#4c4f69",
            "TEXT_SECONDARY": "#5c5f77",
            "CHART_TEMPLATE": "plotly_white",
            "CHART_FONT": "#4c4f69",
            "ACCENT": "#1e66f5",
            "BORDER": "#ccd0da"
        }

    # The "Glow Up" CSS Injection
    custom_css = f"""
    <style>
        /* 1. Import Premium Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

        /* Apply Font Globally */
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif !important;
            -webkit-font-smoothing: antialiased;
        }}
        
        .stApp {{
            background-color: {theme['BG_COLOR']};
            color: {theme['TEXT_PRIMARY']};
        }}

        /* GLASSMORPHISM UTILS */
        /* Note: We can't easily wrap the Streamlit header, but we can style our custom header */
        
        /* 2. TAB GLOW UP (Segmented Control Style) */
        div[data-baseweb="tab-list"] {{
            gap: 8px;
            background-color: rgba(255, 255, 255, 0.05);
            padding: 6px;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        button[data-baseweb="tab"] {{
            flex: 1; 
            background-color: transparent !important;
            color: {theme['TEXT_SECONDARY']} !important;
            border-radius: 12px !important;
            padding: 10px 16px !important;
            font-weight: 600 !important;
            border: none !important;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            margin: 0 !important;
            min-height: 44px; /* Touch target */
        }}
        
        button[data-baseweb="tab"]:hover {{
            color: {theme['TEXT_PRIMARY']} !important;
            background-color: rgba(255, 255, 255, 0.05) !important;
        }}

        button[data-baseweb="tab"][aria-selected="true"] {{
            background-color: {theme['CARD_BG']} !important;
            color: {theme['ACCENT']} !important; /* Accent text for selected */
            box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
            font-weight: 800 !important;
        }}

        /* Remove default Streamlit tab borders */
        div[data-testid="stTabs"] > div[role="tablist"] {{
            border-bottom: none !important;
        }}

        /* 3. METRIC CARDS */
        [data-testid="stMetric"] {{
            background-color: {theme['CARD_BG']};
            padding: 20px;
            border-radius: 20px; /* iOS rounded corners */
            border: 1px solid rgba(255, 255, 255, 0.05);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1);
            transition: transform 0.2s ease;
        }}
        
        [data-testid="stMetric"]:hover {{
            transform: scale(1.02);
            box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.15);
        }}

        [data-testid="stMetricValue"] {{
            color: {theme['TEXT_PRIMARY']} !important;
            font-weight: 800 !important;
            font-size: 2rem !important;
        }}
        
        [data-testid="stMetricLabel"] {{
            color: {theme['TEXT_SECONDARY']} !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            font-size: 0.8rem !important;
        }}

        /* 4. PREMIUM STATUS PILL */
        .gov-pill {{
            padding: 8px 24px;
            border-radius: 30px;
            color: #24273A;
            font-weight: 800;
            display: inline-block;
            margin-top: 5px;
            letter-spacing: 1px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            text-transform: uppercase;
        }}

        /* 5. MOBILE RESPONSIVENESS */

        /* iPhone Max Width */
        @media (max-width: 430px) {{
            /* Fluid Metrics: Force 2x2 Grid */
            [data-testid="stHorizontalBlock"] {{
                flex-wrap: wrap !important;
                gap: 12px !important;
            }}

            [data-testid="column"], [data-testid="stColumn"] {{
                min-width: 40% !important;
                flex: 1 1 calc(50% - 12px) !important;
            }}

            /* Tabs: Ensure they don't scroll off */
            div[data-baseweb="tab-list"] {{
                flex-wrap: nowrap;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
            }}

            button[data-baseweb="tab"] {{
                padding: 8px 12px !important;
                font-size: 0.85rem !important;
                white-space: nowrap;
            }}

            /* Header adjustments */
            h1 {{
                font-size: 1.8rem !important;
            }}
        }}

        /* iPad Width */
        @media (min-width: 431px) and (max-width: 1024px) {{
             /* Similar fluid behavior if needed */
        }}

        /* Touch Targets */
        button, input, [role="button"] {{
            min-height: 48px !important; /* Apple Human Interface Guidelines */
        }}

        /* Glass Header Container */
        .header-container {{
            background: rgba(36, 39, 58, 0.6);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 24px;
            border: 1px solid rgba(255,255,255,0.05);
            box-shadow: 0 8px 32px 0 rgba(0,0,0,0.1);
        }}

        /* 6. GENERAL FIXES */
        [data-testid="stChatMessageContent"] *, 
        [data-testid="stMarkdownContainer"] p, 
        .streamlit-expanderContent p {{
            color: {theme['TEXT_PRIMARY']} !important;
        }}

        code, pre {{
            background-color: {theme['BG_COLOR']} !important;
            color: {theme['ACCENT']} !important;
            border: 1px solid {theme['BORDER']} !important;
            border-radius: 6px !important;
            padding: 2px 6px !important;
            font-family: monospace !important;
        }}

        /* Remove top padding */
        .block-container {{
            padding-top: 1rem !important;
        }}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
    return theme

FOOTER_HTML = """
<div style="text-align: center; margin-top: 60px; padding-top: 24px; border-top: 1px solid #494D64; color: #A5ADCB; font-size: 13px; font-family: 'Inter', sans-serif; letter-spacing: 1.5px;">
    T1DLH • CONTEXTUAL LIFE HUB • EXPERIMENTAL COGNITIVE OFFLOADING
</div>
"""