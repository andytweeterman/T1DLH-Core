def get_main_css(theme):
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Fira+Code:wght@300;500;700&display=swap');

    :root {{
        --bg-color: {theme['BG_COLOR']};
        --card-bg: {theme['CARD_BG']};
        --text-primary: {theme['TEXT_PRIMARY']};
        --text-secondary: {theme['TEXT_SECONDARY']};
        --accent-gold: {theme['ACCENT_GOLD']};
        --delta-up: {theme['DELTA_UP']};
        --delta-down: {theme['DELTA_DOWN']};
    }}

    .stApp {{ background-color: var(--bg-color) !important; font-family: 'Inter', sans-serif; }}

    /* FIX FOR PC LAYOUT: Maximize Screen Usage */
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }}

    /* --- TABS (Restored in v56.2) --- */
    button[data-baseweb="tab"] {{
        background: linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(0,0,0,0.05) 100%) !important;
        border: 1px solid rgba(128,128,128,0.2) !important;
        border-radius: 6px 6px 0 0 !important;
        color: var(--text-secondary) !important;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 14px;
        text-transform: uppercase;
        padding: 10px 10px;
        margin-right: 2px;
        flex-grow: 1;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        background: linear-gradient(180deg, #2d343f 0%, #1a1f26 100%) !important;
        border-top: 2px solid var(--accent-gold) !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] p {{ color: #FFFFFF !important; }}

    /* --- MENU BUTTON STYLING (Restored in v56.3) --- */
    [data-testid="stPopover"] button {{
        border: 1px solid #333333;
        background: #000000;
        color: #C6A87C;
        font-size: 28px !important;
        font-weight: bold;
        height: 70px;
        width: 100%;
        margin-top: 0px;
        border-radius: 0 8px 8px 0;
        border-left: 1px solid #333333;
        box-shadow: 0 4px 6px rgba(0,0,0,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 100;
    }}
    [data-testid="stPopover"] button:hover {{ border-color: #C6A87C; color: #FFFFFF; }}

    /* --- TEXT ENFORCERS --- */
    .stMarkdown p, .stMarkdown span, .stMarkdown li {{ color: var(--text-primary) !important; }}
    h3 {{ color: var(--text-secondary) !important; font-weight: 600 !important; }}

    /* --- HEADER CONTAINER (Seamless Black) --- */
    .header-bar {{
        background: #000000;
        height: 70px;
        display: flex;
        flex-direction: row;
        align-items: center;
        padding-left: 15px;
        padding-right: 15px;
        border: 1px solid #333333;
        border-right: none;
        border-radius: 8px 0 0 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.5);
        overflow: hidden;
    }}

    .header-text-col {{
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-left: 12px;
        line-height: 1.1;
    }}

    .steel-text-main {{
        background: linear-gradient(180deg, #FFFFFF 0%, #E0E0E0 40%, #A0A0A0 55%, #FFFFFF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 24px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .steel-text-sub {{
        background: linear-gradient(180deg, #E0E0E0 0%, #A0A0A0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 2px;
        white-space: nowrap;
    }}

    /* MOBILE ADJUSTMENT */
    @media (max-width: 400px) {{
        .steel-text-sub {{ font-size: 9px; white-space: normal; }}
        .block-container {{ padding-left: 0.5rem !important; padding-right: 0.5rem !important; }}
    }}

    /* COMPONENTS */
    .gov-pill {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-family: 'Fira Code', monospace; font-size: 11px; font-weight: bold; color: white; box-shadow: 0 2px 5px rgba(0,0,0,0.2); margin-left: 10px; vertical-align: middle; text-transform: uppercase; }}
    .premium-pill {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 800; color: #3b2c00; background: linear-gradient(135deg, #bf953f 0%, #fcf6ba 100%); box-shadow: 0 2px 5px rgba(0,0,0,0.2); margin-left: 5px; vertical-align: middle; letter-spacing: 1px; }}
    .steel-sub-header {{ background: linear-gradient(145deg, #1a1f26, #2d343f); padding: 8px 15px; border-radius: 6px; border: 1px solid #4a4f58; box-shadow: 0 2px 4px rgba(0,0,0,0.3); margin-bottom: 15px; }}
    .market-card {{ background: var(--card-bg); border: 1px solid rgba(128,128,128,0.2); border-radius: 6px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; margin-bottom: 10px; }}
    .market-ticker {{ color: var(--text-secondary); font-size: 11px; margin-bottom: 2px; }}
    .market-price {{ color: var(--text-primary); font-family: 'Fira Code', monospace; font-size: 22px; font-weight: 700; margin: 2px 0; }}
    .market-delta {{ font-family: 'Fira Code', monospace; font-size: 13px; font-weight: 600; }}

    div[data-testid="stMetricLabel"] {{ color: var(--text-secondary) !important; font-size: 14px !important; font-weight: 500 !important; }}
    div[data-testid="stMetricValue"] {{ color: var(--text-primary) !important; }}
    header[data-testid="stHeader"] {{ visibility: hidden; }}
    #MainMenu, footer {{ visibility: hidden; }}
    div[data-testid="column"] {{ padding: 0px !important; }}
    div[data-testid="stHorizontalBlock"] {{ gap: 0rem !important; }}
    </style>
    """
