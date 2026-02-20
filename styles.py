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
        }}
        
        .stApp {{
            background-color: {theme['BG_COLOR']};
            color: {theme['TEXT_PRIMARY']};
        }}
        
        /* 2. TAB GLOW UP */
        div[data-testid="stTabs"] > div[role="tablist"] {{
            gap: 12px;
            background-color: transparent;
            padding-bottom: 10px;
            border-bottom: 1px solid {theme['BORDER']};
        }}
        
        button[data-baseweb="tab"] {{
            flex: 1; 
            background-color: {theme['CARD_BG']} !important;
            color: {theme['TEXT_SECONDARY']} !important;
            border-radius: 12px !important;
            padding: 14px 24px !important;
            font-weight: 600 !important;
            border: 1px solid transparent !important;
            transition: all 0.3s ease;
        }}
        
        button[data-baseweb="tab"]:hover {{
            border: 1px solid {theme['BORDER']} !important;
            color: {theme['TEXT_PRIMARY']} !important;
            transform: translateY(-1px);
        }}

        button[data-baseweb="tab"][aria-selected="true"] {{
            background-color: {theme['ACCENT']} !important;
            color: #24273A !important;
            box-shadow: 0 4px 15px rgba(138, 173, 244, 0.3) !important; 
            font-weight: 800 !important;
        }}

        /* 3. METRIC CARDS */
        [data-testid="stMetric"] {{
            background-color: {theme['CARD_BG']};
            padding: 16px 20px;
            border-radius: 16px;
            border: 1px solid {theme['BORDER']};
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        [data-testid="stMetricValue"] {{
            color: {theme['TEXT_PRIMARY']} !important;
            font-weight: 800 !important;
        }}
        
        [data-testid="stMetricLabel"] {{
            color: {theme['TEXT_SECONDARY']} !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            font-size: 0.85rem !important;
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

        /* 5. FIX CHAT TEXT VISIBILITY */
        [data-testid="stChatMessageContent"] *, 
        [data-testid="stMarkdownContainer"] p, 
        .streamlit-expanderContent p {{
            color: {theme['TEXT_PRIMARY']} !important;
        }}

        /* 6. FIX FORMULA/CODE BLOCK VISIBILITY */
        code, pre {{
            background-color: {theme['BG_COLOR']} !important;
            color: {theme['ACCENT']} !important;
            border: 1px solid {theme['BORDER']} !important;
            border-radius: 6px !important;
            padding: 2px 6px !important;
            font-family: monospace !important;
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