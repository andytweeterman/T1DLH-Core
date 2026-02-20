import streamlit as st

def apply_theme():
    # Ensure session state is initialized for the toggle
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = True # Default to Dark Macchiato

    # Catppuccin Macchiato Color Palette
    if st.session_state["dark_mode"]:
        theme = {
            "BG_COLOR": "#24273A",        # Macchiato Base
            "CARD_BG": "#363A4F",         # Macchiato Surface0
            "TEXT_PRIMARY": "#CAD3F5",    # Macchiato Text
            "TEXT_SECONDARY": "#A5ADCB",  # Macchiato Subtext0
            "CHART_TEMPLATE": "plotly_dark",
            "CHART_FONT": "#CAD3F5",
            "ACCENT": "#8AADF4",          # Macchiato Blue
            "BORDER": "#494D64"           # Macchiato Surface1
        }
    else:
        # Catppuccin Latte (Light Mode Fallback)
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

    # Apply the CSS injection
    custom_css = f"""
    <style>
        /* Global Background and Text */
        .stApp {{
            background-color: {theme['BG_COLOR']};
            color: {theme['TEXT_PRIMARY']};
        }}
        
        /* Status Pill Styling */
        .gov-pill {{
            padding: 6px 16px;
            border-radius: 20px;
            color: #24273A;
            font-weight: 700;
            display: inline-block;
            margin-top: 5px;
        }}
        
        /* Metric Box Overrides */
        [data-testid="stMetricValue"] {{
            color: {theme['TEXT_PRIMARY']} !important;
        }}
        [data-testid="stMetricLabel"] {{
            color: {theme['TEXT_SECONDARY']} !important;
        }}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
    return theme

# Clean, subtle footer for the Life Hub
FOOTER_HTML = """
<div style="text-align: center; margin-top: 50px; padding-top: 20px; border-top: 1px solid #494D64; color: #A5ADCB; font-size: 12px; font-family: 'Inter', sans-serif;">
    T1DLH | CONTEXTUAL LIFE HUB | EXPERIMENTAL COGNITIVE OFFLOADING
</div>
"""