import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import styles
import logic
import mock_data

# 1. PAGE SETUP (MUST BE FIRST)
st.set_page_config(
    page_title="MacroEffects | Outthink the Market",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. SETUP & THEME
theme = styles.apply_theme()

# 3. DATA LOADING
full_data = None
closes = None
cgm_data = None
status, color, reason = "SYSTEM BOOT", "#888888", "Initializing..."

try:
    with st.spinner("Connecting to Global Swarm..."):
        full_data = logic.fetch_market_data()
        strat_data = logic.load_strategist_data()
        cgm_data = mock_data.get_mock_cgm()

    if full_data is not None and not full_data.empty:
        closes = full_data['Close']
        gov_df, status, color, reason = logic.calc_governance(full_data)
        latest_monitor = gov_df.iloc[-1]
    else:
        status, color, reason = "DATA ERROR", "#ff0000", "Data Feed Unavailable"
except Exception as e:
    status, color, reason = "SYSTEM ERROR", "#ff0000", "Connection Failed"

# 4. HEADER UI
c_title, c_menu = st.columns([0.90, 0.10], gap="small")
with c_title:
    img_b64 = styles.get_base64_image("shield.png")
    header_html = f"""
    <div class="header-bar">
    {'<img src="data:image/png;base64,' + img_b64 + '" style="height: 50px; width: auto; flex-shrink: 0; object-fit: contain;">' if img_b64 else ''}
    <div class="header-text-col">
    <span class="steel-text-main">MacroEffects</span>
    <span class="steel-text-sub">Outthink the Market</span>
    </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

with c_menu:
    with st.popover("☰", use_container_width=True):
        st.caption("Settings & Links")
        is_dark = st.toggle("Dark Mode", value=st.session_state.get("dark_mode", False))
        if is_dark != st.session_state.get("dark_mode", False):
            st.session_state["dark_mode"] = is_dark
            st.rerun()
        st.divider()
        st.page_link("https://sixmonthstockmarketforecast.com/home/", label="Six Month Forecast", icon="📈")
        st.link_button("User Guide", "https://github.com/andytweeterman/alpha-swarm-dashboard/blob/main/docs/USER_GUIDE.md")
        st.link_button("About Us", "https://sixmonthstockmarketforecast.com/about")

# 5. STATUS BAR
st.markdown(f"""
<div style="margin-bottom: 20px; margin-top: 5px;">
    <span style="font-family: 'Inter'; font-weight: 600; font-size: 16px; color: var(--text-secondary);">Macro-Economic Intelligence: Global Market Command Center</span>
    <div class="gov-pill" style="background: linear-gradient(135deg, {color}, {color}88); border: 1px solid {color};">{status}</div>
    <div class="premium-pill">PREMIUM</div>
</div>
""", unsafe_allow_html=True)
st.divider()

# 6. MAIN CONTENT GRID
if full_data is not None and closes is not None:

    tab1, tab2, tab3 = st.tabs(["Markets", "Safety & Stress Tests", "Strategist"])

    # --- TAB 1: MARKETS ---
    with tab1:
        st.markdown('<div class="steel-sub-header"><span class="steel-text-main" style="font-size: 20px !important;">Global Asset Grid</span></div>', unsafe_allow_html=True)
        assets = [
            {"name": "Dow Jones", "ticker": "^DJI", "color": "#00CC00"},
            {"name": "S&P 500", "ticker": "SPY", "color": "#00CC00"},
            {"name": "Nasdaq", "ticker": "^IXIC", "color": "#00CC00"},
            {"name": "VIX Index", "ticker": "^VIX", "color": "#FF5500"},
            {"name": "Gold", "ticker": "GC=F", "color": "#FFD700"},
            {"name": "Crude Oil", "ticker": "CL=F", "color": "#888888"}
        ]

        cols = st.columns(3)
        for i, asset in enumerate(assets):
            with cols[i % 3]:
                if asset['ticker'] in closes:
                    s = closes[asset['ticker']].dropna()
                    if not s.empty:
                        cur, prev = s.iloc[-1], s.iloc[-2]
                        st.markdown(styles.render_market_card(asset['name'], cur, cur-prev, ((cur-prev)/prev)*100), unsafe_allow_html=True)
                        st.plotly_chart(styles.render_sparkline(s.tail(30), asset['color']), use_container_width=True, config={'displayModeBar': False})

        st.divider()

        # Deep Dive Chart -> Continuous Glucose Monitoring (24H)
        st.markdown('<div class="steel-sub-header"><span class="steel-text-main" style="font-size: 20px !important;">Continuous Glucose Monitoring (24H)</span></div>', unsafe_allow_html=True)

        if cgm_data is not None:
            fig = go.Figure()

            # Glucose Line
            fig.add_trace(go.Scatter(
                x=cgm_data['Timestamp'],
                y=cgm_data['Glucose_Value'],
                mode='lines',
                line=dict(color='#00BFFF', width=2), # Bright blue
                name='Glucose'
            ))

            # Target Range (70-180) - Green background
            fig.add_hrect(
                y0=70, y1=180,
                fillcolor="rgba(0, 255, 0, 0.1)",
                layer="below",
                line_width=0,
                annotation_text="Target Range",
                annotation_position="top left"
            )

            # Hypo Threshold (70) - Red line
            fig.add_hline(
                y=70,
                line_dash="dash",
                line_color="red",
                annotation_text="Hypo Threshold",
                annotation_position="bottom right"
            )

            fig.update_layout(
                template=theme["CHART_TEMPLATE"],
                height=400,
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis_title="Time",
                yaxis_title="Glucose (mg/dL)"
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("CGM Data Unavailable")

    # --- TAB 2: SAFETY -> LOGISTICAL RISK ---
    with tab2:
        st.markdown('<div class="steel-sub-header"><span class="steel-text-main" style="font-size: 20px !important;">Logistical Risk & Executive Function</span></div>', unsafe_allow_html=True)

        st.markdown(f'<div class="gov-pill" style="background: linear-gradient(135deg, {color}, {color}88); border: 1px solid {color};">{status}</div>', unsafe_allow_html=True)
        st.caption(f"Reason: {reason}")

        st.subheader("⏱️ Tactical Horizons")

        h1, h2, h3 = st.columns(3)
        with h1:
            st.markdown("**1 HOUR (Immediate/Transit)**")
            st.info("**Commute Risk**")
            st.markdown("🟢 **SAFE** - Glucose stable at 115, no transit expected.")
        with h2:
            st.markdown("**4 HOURS (Upcoming Meetings/Meals)**")
            st.info("**Context Override**")
            st.markdown("🟡 **CAUTION** - Team Strategy Review at 2:00 PM. Anticipate adrenaline spike. Suggest delaying correction bolus.")
        with h3:
            st.markdown("**24 HOURS (Overnight Logistics)**")
            st.info("**Supply Prep**")
            st.markdown("🟢 **NOMINAL** - Sensor expires in 3 days. No immediate action required.")

    # --- TAB 3: STRATEGIST ---
    with tab3:
        st.markdown('<div class="steel-sub-header"><span class="steel-text-main" style="font-size: 20px !important;">MacroEffects: Chief Strategist\'s View</span></div>', unsafe_allow_html=True)
        try:
            update_df = logic.get_strategist_update()
            if update_df is not None:
                update_data = dict(zip(update_df['Key'], update_df['Value']))
                with st.expander(f"Read Forecast ({update_data.get('Date', 'Current')})", expanded=True):
                    st.markdown(f'**"{update_data.get("Title", "Market Update")}"**')
                    st.markdown(str(update_data.get('Text', '')).replace("\\n", "\n"))
                st.info("💡 **Analyst Note:** This commentary is pulled live from the Chief Strategist's desk via the Alpha Swarm CMS.")
            else: st.warning("Strategist feed temporarily unavailable.")
        except Exception: st.warning("Strategist feed temporarily unavailable.")
else:
    st.error("Data connection initializing or offline. Please check network.")

st.markdown(styles.FOOTER_HTML, unsafe_allow_html=True)
