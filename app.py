# app.py — KNPC Business Data Intelligence Platform v5.0
# Market Intelligence • Benchmark Price Tracking • Quarterly Reporting (MOG)

import html
import pandas as pd
import streamlit as st
from datetime import date, datetime
from pathlib import Path

# Page layout configurations applied cleanly at the initialization stage
st.set_page_config(
    page_title="KNPC Business Data Intelligence Platform",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

try:
    from database import (
        init_db, insert_product_price, insert_crude_price, insert_development,
        get_connection, get_setting, set_setting, delete_setting,
    )
    from exporter import export_daily_excel, latest_excel_file
    from analytics import (
        crude_summary,
        product_summary,
        weekly_benchmark_change,
        quarterly_benchmark_stats,
        quarterly_product_stats,
        developments_for_period,
    )
    from config import (
        PRODUCT_PROXY_MAP,
        ANALYTICS_LOOKBACK_DAYS,
        SOURCES,
        DEVELOPMENT_CATEGORIES,
        QUARTER_MONTHS,
        MOG_DIVISION_NAME,
    )
    from report_generator import generate_quarterly_report, list_generated_reports
    from ai_assistant import generate_ai_outlook, AIAssistantError
except ImportError as e:
    st.error(f"❌ Module import error: {e}")
    st.stop()

# ------------------------------------------------------------------------------
# CACHED DATA ACCESS LAYER — defined early so every part of the script (the
# Control Console dialog included) can call .clear() on these right after a
# write, before falling back to the tab-rendering code lower in the file.
# Streamlit reruns this entire script on every click/keystroke; without
# caching, every interaction re-read the full SQLite tables and recomputed
# every summary from scratch. This was the single biggest performance cost
# in the app, especially as the price/news/developments tables grow.
# ------------------------------------------------------------------------------
@st.cache_data(ttl=60, show_spinner=False)
def load_dashboard_data():
    conn = get_connection()
    try:
        crude = pd.read_sql_query("SELECT * FROM crude_prices", conn)
        product = pd.read_sql_query("SELECT * FROM product_prices", conn)
        news = pd.read_sql_query("SELECT * FROM market_news ORDER BY id DESC LIMIT 5", conn)
        dev = pd.read_sql_query("SELECT * FROM market_developments ORDER BY id DESC", conn)
        return crude, product, news, dev
    finally:
        conn.close()


@st.cache_data(ttl=60, show_spinner=False)
def cached_crude_summary(crude_df: pd.DataFrame) -> pd.DataFrame:
    return crude_summary(crude_df) if not crude_df.empty else pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)
def cached_product_summary(product_df: pd.DataFrame) -> pd.DataFrame:
    return product_summary(product_df) if not product_df.empty else pd.DataFrame()


def invalidate_data_cache():
    """Call right after any write so the next read reflects it immediately,
    instead of waiting out the 60s TTL."""
    load_dashboard_data.clear()
    cached_crude_summary.clear()
    cached_product_summary.clear()


def render_price_tile(label: str, row: pd.DataFrame, label_suffix: str = "") -> str:
    """Builds one Fluent-style card for a benchmark/product price tile.
    Consolidating this into a single HTML block (vs. several stacked
    st.markdown calls) also cuts down on redundant DOM writes per render."""
    label_html = html.escape(f"{label}{label_suffix}")

    if not row.empty and pd.notna(row.iloc[0]["Latest Price"]) and row.iloc[0]["Source"] != "Source system didn't publish":
        price_val = float(row.iloc[0]["Latest Price"])
        chg = row.iloc[0]["Daily Change"]
        chg_pct = row.iloc[0]["Daily Change %"]
        source_lbl = html.escape(str(row.iloc[0]["Source"]))

        change_html = ""
        if chg is not None and pd.notna(chg):
            color = "#107C10" if chg >= 0 else "#D13438"
            sign = "+" if chg >= 0 else ""
            change_html = f"<div class='ms-tile-change' style='color:{color};'>{sign}{chg:.2f} ({sign}{chg_pct:.2f}%)</div>"

        return (
            f'<div class="ms-tile">'
            f'<div class="stat-label-text">{label_html}</div>'
            f'<div class="stat-value-numeric">${price_val:.2f} <span class="ms-tile-unit">USD/bbl</span></div>'
            f'{change_html}'
            f'<span class="badge-source-tracker" title="{source_lbl}">📍 {source_lbl}</span>'
            f'</div>'
        )
    return (
        f'<div class="ms-tile">'
        f'<div class="stat-label-text">{label_html}</div>'
        f'<div style="margin-top:0.35rem;"><span class="badge-unpublished-system">Source system didn\'t publish</span></div>'
        f'<span class="badge-source-tracker">📍 Source: N/A</span>'
        f'</div>'
    )

# ------------------------------------------------------------------------------
# INJECT STYLES: REMOVE EMPTINESS, LEFT-ALIGN BANNER, HIDE OVERFLOWS
# ------------------------------------------------------------------------------
st.markdown("""
<style>
:root {
    --ms-blue: #0078D4;
    --ms-blue-hover: #106EBE;
    --ms-blue-pressed: #005A9E;
    --ms-blue-tint: #EFF6FC;
    --ms-blue-tint-strong: #C7E0F4;
    --ms-bg: #FAF9F8;
    --ms-surface: #FFFFFF;
    --ms-surface-alt: #F3F2F1;
    --ms-border: #E1DFDD;
    --ms-border-strong: #D2D0CE;
    --ms-text: #201F1E;
    --ms-text-secondary: #605E5C;
    --ms-text-tertiary: #8A8886;
    --ms-success: #107C10;
    --ms-success-tint: rgba(16,124,16,0.10);
    --ms-danger: #D13438;
    --ms-danger-tint: rgba(209,52,56,0.10);
    --ms-warning: #9D5D00;
    --ms-warning-tint: rgba(255,185,0,0.16);
    --ms-radius-sm: 4px;
    --ms-radius-md: 8px;
    --ms-shadow-2: 0 1.6px 3.6px rgba(0,0,0,0.11), 0 0.3px 0.9px rgba(0,0,0,0.09);
    --ms-shadow-8: 0 6.4px 14.4px rgba(0,0,0,0.11), 0 1.2px 3.6px rgba(0,0,0,0.08);
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background: linear-gradient(180deg, #FAF9F8 0%, #F6F4FB 100%) !important;
    font-family: 'Segoe UI Variable Text', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    color: var(--ms-text) !important;
}

[data-testid="stMainBlockContainer"] {
    padding-top: 0rem !important;
    padding-bottom: 2rem !important;
    margin-top: 0rem !important;
}

[data-testid="stHeader"], .stAppDeployButton, header {
    display: none !important;
    height: 0px !important;
}

[data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] {
    display: none !important;
}

/* ---- Command-bar style banner (Fluent "Card" surface + brand accent rule) ---- */
.executive-banner-box {
    position: relative;
    background: var(--ms-surface);
    padding: 1.5rem 1.75rem;
    border-radius: var(--ms-radius-md);
    border: 1px solid var(--ms-border);
    margin-top: 0.5rem;
    margin-bottom: 1.75rem;
    box-shadow: var(--ms-shadow-2);
    text-align: left;
    overflow: hidden;
}
.executive-banner-box::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #0078D4, #00B7C3, #8764B8);
}

.system-headline-title {
    margin: 0 !important;
    font-size: 1.75rem !important;
    font-weight: 600 !important;
    color: var(--ms-text) !important;
    letter-spacing: -0.01em !important;
    text-align: left !important;
}
.system-sub-headline {
    margin: 0.35rem 0 0 0 !important;
    color: var(--ms-text-secondary) !important;
    font-size: 0.92rem !important;
    font-weight: 400 !important;
    text-align: left !important;
}
.system-live-clock {
    margin: 0.6rem 0 0 0 !important;
    color: var(--ms-blue) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    text-align: left !important;
}

.section-title {
    color: var(--ms-text) !important;
    font-weight: 600;
    letter-spacing: 0.01em;
    margin-bottom: 1.1rem;
    text-transform: none;
    font-size: 1.05rem;
    padding-left: 0.7rem;
    border-left: 3px solid var(--ms-blue);
}

.stat-label-text {
    font-size: 0.78rem;
    color: var(--ms-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
    margin-bottom: 0.25rem;
    margin-top: 0;
}
.stat-value-numeric {
    font-size: 1.6rem;
    font-weight: 600;
    color: var(--ms-text);
    margin: 0.1rem 0;
}
.ms-tile-unit {
    font-size: 0.85rem;
    color: var(--ms-text-tertiary);
    font-weight: 400;
}
.ms-tile-change {
    font-weight: 600;
    font-size: 0.85rem;
    margin-top: 0.1rem;
}

/* Fluent "Card" tile used for every price stat block */
.ms-tile {
    background: var(--ms-surface);
    border: 1px solid var(--ms-border);
    border-radius: var(--ms-radius-md);
    padding: 0.9rem 1rem;
    margin-bottom: 0.9rem;
    min-height: 128px;
    box-shadow: var(--ms-shadow-2);
    transition: box-shadow 0.15s ease-in-out, border-color 0.15s ease-in-out, transform 0.15s ease-in-out;
}
.ms-tile:hover {
    box-shadow: var(--ms-shadow-8);
    border-color: var(--ms-border-strong);
    transform: translateY(-2px);
}

/* Development / news feed items as flat list cards */
.ms-feed-card {
    background: var(--ms-surface);
    border: 1px solid var(--ms-border);
    border-left: 3px solid var(--ms-blue);
    border-radius: var(--ms-radius-sm);
    padding: 0.75rem 0.9rem;
    margin-bottom: 0.6rem;
}
.ms-feed-card.impact-high { border-left-color: var(--ms-danger); }
.ms-feed-card.impact-medium { border-left-color: var(--ms-warning); }
.ms-feed-card.impact-low { border-left-color: var(--ms-success); }

.badge-unpublished-system {
    background-color: var(--ms-danger-tint);
    color: var(--ms-danger);
    padding: 0.25rem 0.6rem;
    border-radius: var(--ms-radius-sm);
    font-size: 0.78rem;
    font-weight: 600;
    display: inline-block;
    border: 1px solid rgba(209,52,56,0.25);
    font-style: normal;
}
.badge-source-tracker {
    font-size: 0.78rem;
    color: var(--ms-text-tertiary);
    display: block;
    margin-top: 0.25rem;
    margin-bottom: 0.75rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.badge-impact-high { background: var(--ms-danger-tint); color: var(--ms-danger); border: 1px solid rgba(209,52,56,0.3); }
.badge-impact-medium { background: var(--ms-warning-tint); color: var(--ms-warning); border: 1px solid rgba(157,93,0,0.3); }
.badge-impact-low { background: var(--ms-success-tint); color: var(--ms-success); border: 1px solid rgba(16,124,16,0.3); }
.badge-impact-high, .badge-impact-medium, .badge-impact-low {
    padding: 0.15rem 0.55rem; border-radius: var(--ms-radius-sm); font-size: 0.7rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.04em; display: inline-block;
}
.badge-category {
    background: var(--ms-blue-tint); color: var(--ms-blue); border: 1px solid var(--ms-blue-tint-strong);
    padding: 0.15rem 0.55rem; border-radius: var(--ms-radius-sm); font-size: 0.7rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.04em; display: inline-block; margin-right: 0.4rem;
}

.news-feed-link {
    color: var(--ms-blue) !important;
    font-weight: 600;
    text-decoration: none !important;
    font-size: 0.92rem;
}
.news-feed-link:hover {
    color: var(--ms-blue-hover) !important;
    text-decoration: underline !important;
}

/* ---- Fluent-style primary buttons (subtle gradient for a richer feel) ---- */
div[data-testid="stForm"] button[kind="primaryFormSubmit"],
button[kind="primary"] {
    background: linear-gradient(135deg, #0078D4, #005A9E) !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border: 1px solid var(--ms-blue) !important;
    border-radius: var(--ms-radius-sm) !important;
    transition: box-shadow 0.15s ease-in-out, transform 0.1s ease-in-out !important;
}
div[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover,
button[kind="primary"]:hover {
    box-shadow: 0 4px 14px rgba(0,120,212,0.35) !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stForm"] button[kind="primaryFormSubmit"]:active,
button[kind="primary"]:active {
    background: linear-gradient(135deg, #106EBE, #005A9E) !important;
    transform: translateY(0) !important;
    box-shadow: none !important;
}

/* Secondary (default) buttons: Fluent outline style */
.stButton button[kind="secondary"], .stDownloadButton button {
    background-color: var(--ms-surface) !important;
    color: var(--ms-text) !important;
    border: 1px solid var(--ms-border-strong) !important;
    border-radius: var(--ms-radius-sm) !important;
    font-weight: 500 !important;
}
.stButton button[kind="secondary"]:hover, .stDownloadButton button:hover {
    background-color: var(--ms-surface-alt) !important;
    border-color: var(--ms-text-tertiary) !important;
    color: var(--ms-text) !important;
}

div[data-testid="stForm"] {
    background-color: var(--ms-surface) !important;
    border: 1px solid var(--ms-border) !important;
    border-radius: var(--ms-radius-md) !important;
    padding: 1.25rem !important;
    box-shadow: var(--ms-shadow-2) !important;
}

div.login-form-wrapper div[data-testid="stForm"] {
    border: 1px solid var(--ms-border) !important;
    background-color: var(--ms-surface) !important;
    padding: 1.75rem !important;
    box-shadow: var(--ms-shadow-8) !important;
}

/* Inputs: give every text/number/date/select box a visible surface and
   border. Previously only the CSS variables were referenced without an
   explicit background, so inputs on the white login/form cards had no
   visible boundary at all. */
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {
    background-color: var(--ms-surface-alt) !important;
    border: 1px solid var(--ms-border-strong) !important;
    border-radius: var(--ms-radius-sm) !important;
}
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
    background-color: transparent !important;
    color: var(--ms-text) !important;
}
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus {
    border-color: var(--ms-blue) !important;
    box-shadow: 0 0 0 1px var(--ms-blue) !important;
}
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within {
    border-color: var(--ms-blue) !important;
    box-shadow: 0 0 0 1px var(--ms-blue) !important;
}

/* Pivot-style tabs */
button[data-baseweb="tab"] {
    color: var(--ms-text-secondary) !important;
    font-weight: 500 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--ms-blue) !important;
    border-bottom-color: var(--ms-blue) !important;
    font-weight: 600 !important;
}
[data-baseweb="tab-highlight"] { background-color: var(--ms-blue) !important; }
[data-baseweb="tab-border"] { background-color: var(--ms-border) !important; }

/* Dataframes / tables as Fluent surfaces */
[data-testid="stDataFrame"], [data-testid="stTable"] {
    border: 1px solid var(--ms-border) !important;
    border-radius: var(--ms-radius-md) !important;
    overflow: hidden !important;
}

/* Dialog modal surface */
[role="dialog"] {
    border-radius: var(--ms-radius-md) !important;
}

hr { border-color: var(--ms-border) !important; }

.app-footer {
    margin-top: 4rem;
    padding: 1.5rem 0;
    border-top: 1px solid var(--ms-border);
    text-align: center;
    font-size: 0.82rem;
    color: var(--ms-text-tertiary);
}

/* Post-login splash — shown once while the data cache warms */
.splash-screen {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 65vh;
    text-align: center;
}
.splash-mark {
    font-size: 3.2rem;
    animation: splash-pulse 1.5s ease-in-out infinite;
}
.splash-title {
    margin-top: 1.1rem;
    font-size: 1.3rem;
    font-weight: 600;
    color: var(--ms-text);
    letter-spacing: -0.01em;
}
.splash-subtitle {
    margin-top: 0.5rem;
    font-size: 0.92rem;
    font-weight: 600;
    background: linear-gradient(90deg, #0078D4, #00B7C3, #8764B8, #0078D4);
    background-size: 300% 100%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: splash-shimmer 2.2s linear infinite;
}
@keyframes splash-pulse {
    0%, 100% { transform: scale(1); opacity: 0.85; }
    50% { transform: scale(1.15); opacity: 1; }
}
@keyframes splash-shimmer {
    0% { background-position: 0% 50%; }
    100% { background-position: 300% 50%; }
}
</style>
""", unsafe_allow_html=True)

try:
    init_db()
except Exception as ex:
    st.error(f"Database error initialized pipeline failed: {ex}")

# ------------------------------------------------------------------------------
# LOCK PRIVACY GATEWAY LEVEL ACCESS
# ------------------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    left_anim_col, right_login_col = st.columns([1.75, 1.25])

    with left_anim_col:
        st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
        animation_path = Path(__file__).resolve().parent / "animation.html"
        if animation_path.exists():
            # st.iframe reads local HTML files directly — no manual file
            # handling required, and it replaces the deprecated
            # st.components.v1.html call (scheduled for removal).
            st.iframe(str(animation_path), height=450)
        else:
            st.info("Gateway animation asset not found; continuing without it.")

    with right_login_col:
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #0078D4; margin-bottom: 1.5rem; width: 100%; font-size: 1.75rem; font-weight: 600; letter-spacing: -0.01em;'>KNPC BI Platform</h2>", unsafe_allow_html=True)
        st.markdown("<div class='login-form-wrapper'>", unsafe_allow_html=True)
        with st.form("security_login_gate"):
            user_input = st.text_input("username")
            pass_input = st.text_input("password", type="password")
            login_commit = st.form_submit_button("login")
            if login_commit:
                if user_input == "admin" and pass_input == "admin":
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Access authorization failed. Invalid security identifiers.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ------------------------------------------------------------------------------
# POST-LOGIN SPLASH — warms the data cache once, right after authentication,
# instead of letting the header render immediately while the rest of the
# page waits on cold database reads (which looked like a half-built page
# popping in piece by piece for a couple of seconds).
# ------------------------------------------------------------------------------
if "dashboard_warmed" not in st.session_state:
    st.markdown(
        '<div class="splash-screen">'
        '<div class="splash-mark">⛽</div>'
        '<div class="splash-title">KNPC Business Data Intelligence Platform</div>'
        '<div class="splash-subtitle">Preparing your workspace…</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    _warm_crude, _warm_product, _warm_news, _warm_dev = load_dashboard_data()
    cached_crude_summary(_warm_crude)
    cached_product_summary(_warm_product)
    st.session_state["dashboard_warmed"] = True
    st.rerun()

# ------------------------------------------------------------------------------
# TOP APP HEADER COMPONENT SECTION - LEFT-ALIGNED STRUCTURAL ROW
# ------------------------------------------------------------------------------
header_col, action_menu_col = st.columns([3.2, 1.8])

with header_col:
    clock_str = datetime.now().strftime("%A, %B %d, %Y • %H:%M:%S IST")
    st.markdown(
        f'<div class="executive-banner-box">'
        f'<h1 class="system-headline-title">KNPC Business Data Intelligence Platform</h1>'
        f'<p class="system-sub-headline">Market Intelligence • Crude Benchmark Tracking • Quarterly Reporting for {html.escape(MOG_DIVISION_NAME)}</p>'
        f'<p class="system-live-clock">⏱️ System Clock: {clock_str}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

@st.dialog("⚙️ Control Console Operations", width="large")
def show_control_console():
    st.markdown("<p style='color:#605E5C;'>Select an administrative operational pipeline request:</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color:#E1DFDD; margin:1rem 0;'>", unsafe_allow_html=True)

    st.markdown("### 1. Ingestion & Monitoring Loop")
    if st.button("⚡ Force Live Pipeline Loop", width="stretch", key="cc_force_pipeline"):
        try:
            with st.spinner("Invoking scraper orchestration & market intelligence monitoring loops..."):
                from collectors import run_all_collectors
                from exporter import export_daily_csv
                run_all_collectors()
                export_daily_csv()
                export_daily_excel()
            st.success("Ingestion & monitoring lifecycle completed successfully.")
            invalidate_data_cache()
            st.rerun()
        except Exception as ex:
            st.error(f"Failed to execute data scraping / monitoring loop routine: {str(ex)}")

    st.markdown("<br>### 2. Analytical Workbook Generation", unsafe_allow_html=True)
    if st.button("📦 Re-compile Excel Sheets", width="stretch", key="cc_recompile_excel"):
        try:
            with st.spinner("Regenerating master matrix tabs..."):
                export_daily_excel()
            st.success("Workbook matrix asset compiled safely.")
            st.rerun()
        except Exception as ex:
            st.error(f"Failed to recompile report documents: {str(ex)}")

    st.markdown("<br>### 3. File Distribution Asset Row", unsafe_allow_html=True)
    try:
        latest_file = latest_excel_file()
        if latest_file and Path(latest_file).exists():
            with open(latest_file, "rb") as f:
                st.download_button(
                    label="📥 Download Daily Excel Report Document",
                    data=f,
                    file_name=Path(latest_file).name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch",
                    key="cc_download_excel"
                )
        else:
            st.info("No compiled workbook files detected in storage path records.")
    except Exception as file_err:
        st.error(f"Error accessing localized file parameters: {str(file_err)}")

with action_menu_col:
    st.markdown("<div style='height: 22px;'></div>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns([2.4, 0.7, 1.3])
    with m1:
        if st.button("⚙️ Control Console", help="Click to open system actions overlay", width="stretch", key="top_control_console"):
            show_control_console()
    with m2:
        try:
            latest_file = latest_excel_file()
            if latest_file and Path(latest_file).exists():
                with open(latest_file, "rb") as f:
                    st.download_button(
                        label="📥",
                        data=f,
                        file_name=Path(latest_file).name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        width="stretch",
                        help="Download XLSX",
                        key="top_download_excel"
                    )
            else:
                st.button("📥", disabled=True, width="stretch", help="Download XLSX (no file yet)", key="top_download_excel_disabled")
        except Exception:
            st.button("📥", disabled=True, width="stretch", help="Download XLSX (unavailable)", key="top_download_excel_error")
    with m3:
        if st.button("🔒 Logout", width="stretch", key="top_logout"):
            st.session_state["authenticated"] = False
            st.session_state.pop("dashboard_warmed", None)
            st.rerun()

# ------------------------------------------------------------------------------
# DATABASE EXTRACTION INTEGRITY FOOTPRINT (cached — see load_dashboard_data
# definition near the top of the file for why)
# ------------------------------------------------------------------------------
try:
    crude_df, product_df, news_df, dev_df = load_dashboard_data()
except Exception as db_read_err:
    st.error(f"Error executing storage data extraction queries: {str(db_read_err)}")
    crude_df, product_df, news_df, dev_df = (pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

c_summary = cached_crude_summary(crude_df)
p_summary = cached_product_summary(product_df)

# ------------------------------------------------------------------------------
# MAIN NAVIGATION — BUSINESS DATA INTELLIGENCE PLATFORM MODULES
# ------------------------------------------------------------------------------
tab_overview, tab_intel, tab_benchmarks, tab_reports, tab_settings = st.tabs([
    "📊 Executive Overview",
    "🌍 Market Intelligence Monitoring",
    "📈 Benchmark Price Tracking",
    "🗂️ Quarterly Market Reports",
    "⚙️ Settings",
])

# ==============================================================================
# TAB 1 — EXECUTIVE OVERVIEW
# ==============================================================================
with tab_overview:
    st.markdown("<h3 class='section-title'>I. Petroleum Crude Oil Global Benchmarks</h3>", unsafe_allow_html=True)
    crude_benchmarks = ["Brent", "WTI", "Dubai", "Oman", "Kuwait Export Crude"]
    c_cols = st.columns(len(crude_benchmarks))

    for idx, bm in enumerate(crude_benchmarks):
        with c_cols[idx]:
            row = c_summary[c_summary["Benchmark"] == bm] if not c_summary.empty else pd.DataFrame()
            st.markdown(render_price_tile(bm, row, label_suffix=" Pricing Index"), unsafe_allow_html=True)

    st.markdown("<br><h3 class='section-title'>II. Singapore / Regional Refined Product Price Proxies</h3>", unsafe_allow_html=True)
    p_items = list(PRODUCT_PROXY_MAP.keys())
    p_cols = st.columns(4)

    for idx, prod in enumerate(p_items):
        col_target = p_cols[idx % 4]
        with col_target:
            row = p_summary[p_summary["Product"] == prod] if not p_summary.empty else pd.DataFrame()
            st.markdown(render_price_tile(prod, row, label_suffix=" Proxy Marker"), unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#E1DFDD; margin:1.5rem 0;'>", unsafe_allow_html=True)
    left_pane, right_pane = st.columns([2, 1])

    with left_pane:
        st.markdown(f"<h3 class='section-title'>III. Historical Volatility ({ANALYTICS_LOOKBACK_DAYS}-Day Window)</h3>", unsafe_allow_html=True)
        vol_tab1, vol_tab2 = st.tabs(["Global Crudes Trend Lines", "Refined Proxy Framework Spreads"])
        cutoff = pd.Timestamp(date.today()) - pd.Timedelta(days=ANALYTICS_LOOKBACK_DAYS)

        with vol_tab1:
            if not crude_df.empty:
                try:
                    c_chart = crude_df.copy()
                    c_chart["price_date"] = pd.to_datetime(c_chart["price_date"], errors="coerce")
                    c_chart = c_chart[(c_chart["price_date"] >= cutoff) & (c_chart["source"] != "Source system didn't publish")].dropna(subset=["price"])
                    if not c_chart.empty:
                        st.line_chart(c_chart.pivot_table(index="price_date", columns="benchmark", values="price"))
                    else:
                        st.error("Data Unavailable")
                except Exception:
                    st.error("Data Unavailable")
            else:
                st.error("Data Unavailable")

        with vol_tab2:
            if not product_df.empty:
                try:
                    p_chart = product_df.copy()
                    p_chart["price_date"] = pd.to_datetime(p_chart["price_date"], errors="coerce")
                    p_chart = p_chart[(p_chart["price_date"] >= cutoff) & (p_chart["source"] != "Source system didn't publish")].dropna(subset=["price"])
                    if not p_chart.empty:
                        st.line_chart(p_chart.pivot_table(index="price_date", columns="product", values="price"))
                    else:
                        st.error("Data Unavailable")
                except Exception:
                    st.error("Data Unavailable")
            else:
                st.error("Data Unavailable")

    with right_pane:
        st.markdown("<h3 class='section-title'>IV. Intelligence Feed</h3>", unsafe_allow_html=True)
        if not news_df.empty:
            for _, row in news_df.iterrows():
                headline = html.escape(str(row["headline"]))
                url = html.escape(str(row["url"]), quote=True)
                source = html.escape(str(row["source"]))
                news_date = html.escape(str(row["news_date"]))
                st.markdown(
                    f'<div class="ms-feed-card">'
                    f'<a class="news-feed-link" href="{url}" target="_blank">📌 {headline}</a>'
                    f'<div style="color:var(--ms-text-tertiary); font-size:0.78rem; margin-top:0.25rem;">Source: {source} • Logged {news_date}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No dynamic intelligence news fields gathered for today.")

    st.markdown("<hr style='border-color:#E1DFDD; margin:1.5rem 0;'>", unsafe_allow_html=True)
    st.markdown("<h3 class='section-title'>V. Operational Field Corrections Ledger</h3>", unsafe_allow_html=True)

    with st.form("executive_audit_form"):
        r1, r2, r3 = st.columns(3)
        f_date = r1.date_input("Target Input Evaluation Date", value=date.today())
        f_prod = r2.selectbox("Refined Product Framework Target Asset", list(PRODUCT_PROXY_MAP.keys()))
        f_price = r3.number_input("True Audited Field Price Value (USD/bbl)", min_value=0.0, step=0.01, format="%.2f")

        meta = PRODUCT_PROXY_MAP[f_prod]
        submitted = st.form_submit_button("Submit Operational Revision")

        if submitted:
            if f_price <= 0.0:
                st.error("Invalid Field Metric entry. Price value input row must exceed zero.")
            else:
                try:
                    insert_product_price(
                        price_date=str(f_date),
                        market=meta["market"],
                        product=f_prod,
                        price=float(f_price),
                        unit="USD/bbl",
                        source="Manual Entry",
                        status="manual_entry",
                        notes="Manual compliance override entry row due to endpoint data gap.",
                        proxy_type=meta["proxy_type"],
                        benchmark_basis=meta["benchmark_basis"]
                    )
                    st.success(f"Audit log updated successfully for asset row {f_prod}.")
                    invalidate_data_cache()
                    st.rerun()
                except Exception as write_err:
                    st.error(f"Failed to commit operational correction record: {str(write_err)}")

# ==============================================================================
# TAB 2 — MARKET INTELLIGENCE MONITORING
# ==============================================================================
with tab_intel:
    st.markdown("<h3 class='section-title'>Global Oil & Energy Market Developments</h3>", unsafe_allow_html=True)
    st.caption(
        "Follows major developments affecting crude oil and refined products markets — OPEC+, IEA and "
        "EIA publications, and geopolitical, economic, and industry events — with an impact assessment "
        "for each item so findings can be incorporated into market reports and intelligence activities."
    )

    mi_c1, mi_c2 = st.columns([1, 3])
    with mi_c1:
        if st.button("🔄 Run Monitoring Sweep Now", width="stretch", key="mi_run_sweep"):
            try:
                with st.spinner("Scanning OPEC+, IEA, EIA, and news sources..."):
                    from collectors import collect_market_developments
                    result = collect_market_developments()
                st.success(f"Monitoring sweep complete — {result.get('developments_logged', 0)} development(s) logged.")
                invalidate_data_cache()
                st.rerun()
            except Exception as ex:
                st.error(f"Monitoring sweep failed: {str(ex)}")

    st.markdown("<br>", unsafe_allow_html=True)

    filt_c1, filt_c2, filt_c3 = st.columns(3)
    category_options = ["All"] + list(DEVELOPMENT_CATEGORIES.keys())
    impact_options = ["All", "High", "Medium", "Low"]
    with filt_c1:
        sel_category = st.selectbox("Filter by Category", category_options, key="mi_filter_category")
    with filt_c2:
        sel_impact = st.selectbox("Filter by Impact Assessment", impact_options, key="mi_filter_impact")
    with filt_c3:
        sel_days = st.number_input("Lookback (days)", min_value=1, max_value=365, value=30, key="mi_filter_days")

    filtered_dev = dev_df.copy()
    if not filtered_dev.empty:
        filtered_dev["dev_date_parsed"] = pd.to_datetime(filtered_dev["dev_date"], errors="coerce")
        cutoff_dev = pd.Timestamp.today().normalize() - pd.Timedelta(days=int(sel_days))
        filtered_dev = filtered_dev[filtered_dev["dev_date_parsed"] >= cutoff_dev]
        if sel_category != "All":
            filtered_dev = filtered_dev[filtered_dev["category"] == sel_category]
        if sel_impact != "All":
            filtered_dev = filtered_dev[filtered_dev["impact"] == sel_impact]
        filtered_dev = filtered_dev.sort_values("dev_date_parsed", ascending=False)

    st.markdown(f"<h4 class='section-title' style='font-size:1rem; margin-top:1.5rem;'>Monitored Developments ({len(filtered_dev)})</h4>", unsafe_allow_html=True)

    if not filtered_dev.empty:
        for _, row in filtered_dev.iterrows():
            impact_val = str(row.get("impact", "Low")) or "Low"
            headline = html.escape(str(row.get("headline", "")))
            category = html.escape(str(row.get("category", "")))
            dev_date_str = html.escape(str(row.get("dev_date", "")))
            source = html.escape(str(row.get("source", "")))
            url = html.escape(str(row.get("url", "")), quote=True)
            summary = html.escape(str(row.get("summary", "") or ""))

            link_html = f"<a class='news-feed-link' href='{url}' target='_blank'>{headline}</a>" if url and url != "None" else headline
            summary_html = f"<div style='color:var(--ms-text-secondary); font-size:0.85rem; margin-top:0.3rem;'>{summary}</div>" if summary else ""
            st.markdown(
                f'<div class="ms-feed-card impact-{impact_val.lower()}">'
                f'<span class="badge-category">{category}</span>'
                f'<span class="badge-impact-{impact_val.lower()}">{html.escape(impact_val)} Impact</span>'
                f'<div style="margin-top:0.4rem;">{link_html}</div>'
                f'<div style="color:var(--ms-text-tertiary); font-size:0.78rem; margin-top:0.2rem;">{dev_date_str} • Source: {source}</div>'
                f'{summary_html}'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No developments match the current filters. Run a monitoring sweep or log a finding manually below.")

    st.markdown("<hr style='border-color:#E1DFDD; margin:1.5rem 0;'>", unsafe_allow_html=True)
    st.markdown("<h4 class='section-title' style='font-size:1rem;'>Log a Market Development Manually</h4>", unsafe_allow_html=True)
    st.caption("Use this to incorporate a finding an analyst has identified into the intelligence record, independent of the automated monitoring sweep.")

    with st.form("log_development_form"):
        d1, d2, d3 = st.columns(3)
        dev_date_input = d1.date_input("Development Date", value=date.today(), key="dev_form_date")
        dev_category_input = d2.selectbox("Category", list(DEVELOPMENT_CATEGORIES.keys()), key="dev_form_category")
        dev_impact_input = d3.selectbox("Impact Assessment", ["High", "Medium", "Low"], key="dev_form_impact")

        dev_headline_input = st.text_input("Headline / Development Title", key="dev_form_headline")
        dev_summary_input = st.text_area("Summary / Potential Market Impact", key="dev_form_summary")
        d4, d5 = st.columns(2)
        dev_source_input = d4.text_input("Source", value="Analyst Input", key="dev_form_source")
        dev_url_input = d5.text_input("Reference URL (optional)", key="dev_form_url")

        dev_submitted = st.form_submit_button("Log Development")
        if dev_submitted:
            if not dev_headline_input.strip():
                st.error("A headline / development title is required.")
            else:
                try:
                    insert_development(
                        dev_date=str(dev_date_input),
                        category=dev_category_input,
                        headline=dev_headline_input.strip(),
                        summary=dev_summary_input.strip(),
                        source=dev_source_input.strip() or "Analyst Input",
                        url=dev_url_input.strip(),
                        impact=dev_impact_input,
                        entered_by="Analyst",
                    )
                    st.success("Development logged to the market intelligence record.")
                    invalidate_data_cache()
                    st.rerun()
                except Exception as ex:
                    st.error(f"Failed to log development: {str(ex)}")

# ==============================================================================
# TAB 3 — BENCHMARK PRICE TRACKING
# ==============================================================================
with tab_benchmarks:
    st.markdown("<h3 class='section-title'>International Crude Benchmark Price Tracking</h3>", unsafe_allow_html=True)
    st.caption(
        "Tracks Brent, WTI, and Dubai (plus Oman and Kuwait Export Crude for regional context), monitors "
        "geopolitical and economic developments affecting crude markets, and follows up on daily and "
        "weekly price fluctuations and trends."
    )

    focus_benchmarks = ["Brent", "WTI", "Dubai"]
    bm_cols = st.columns(len(focus_benchmarks))
    for idx, bm in enumerate(focus_benchmarks):
        with bm_cols[idx]:
            row = c_summary[c_summary["Benchmark"] == bm] if not c_summary.empty else pd.DataFrame()
            st.markdown(render_price_tile(bm, row), unsafe_allow_html=True)

    st.markdown("<br><h4 class='section-title' style='font-size:1rem;'>Daily & Weekly Fluctuation Summary</h4>", unsafe_allow_html=True)
    st.markdown("**Daily change (latest vs. previous reading):**")
    if not c_summary.empty:
        st.dataframe(
            c_summary[["Benchmark", "Latest Date", "Latest Price", "Previous Price", "Daily Change", "Daily Change %", "Source"]],
            width="stretch",
            hide_index=True,
        )
    else:
        st.caption("No benchmark readings available yet.")

    st.markdown("**Weekly change (latest vs. ~7 days prior):**")
    weekly_df = weekly_benchmark_change(crude_df)
    if not weekly_df.empty:
        st.dataframe(weekly_df, width="stretch", hide_index=True)
    else:
        st.caption("Insufficient historical data to compute a weekly comparison yet.")

    st.markdown("<br><h4 class='section-title' style='font-size:1rem;'>Historical Benchmark Records</h4>", unsafe_allow_html=True)
    if not crude_df.empty:
        available_benchmarks = sorted(crude_df["benchmark"].dropna().unique())
        sel_benchmarks = st.multiselect("Select benchmarks to chart", available_benchmarks, default=[b for b in focus_benchmarks if b in available_benchmarks], key="bm_multiselect")
        hist = crude_df.copy()
        hist["price_date"] = pd.to_datetime(hist["price_date"], errors="coerce")
        hist = hist[hist["source"] != "Source system didn't publish"].dropna(subset=["price"])
        if sel_benchmarks:
            hist = hist[hist["benchmark"].isin(sel_benchmarks)]
        if not hist.empty:
            st.line_chart(hist.pivot_table(index="price_date", columns="benchmark", values="price"))
        else:
            st.caption("No historical readings for the selected benchmark(s) yet.")

        with st.expander("View full historical price record"):
            st.dataframe(
                crude_df.sort_values("price_date", ascending=False)[
                    ["price_date", "benchmark", "price", "unit", "source", "collected_at"]
                ],
                width="stretch",
                hide_index=True,
            )
    else:
        st.caption("No historical crude price records have been collected yet.")

# ==============================================================================
# TAB 4 — QUARTERLY MARKET REPORTS (MOG DIVISION KPI)
# ==============================================================================
with tab_reports:
    st.markdown("<h3 class='section-title'>Quarterly Market Reports — MOG Division</h3>", unsafe_allow_html=True)
    st.caption(
        "Individual KPI: publish market reports quarterly for the Marketing Operations Group (MOG) "
        "division. Reports compile the quarter's crude benchmark and refined product price movements "
        "alongside monitored market developments and analyst outlook commentary."
    )

    rep_c1, rep_c2 = st.columns(2)
    current_year = date.today().year
    current_quarter_num = (date.today().month - 1) // 3 + 1
    with rep_c1:
        sel_year = st.selectbox("Report Year", list(range(current_year - 3, current_year + 1))[::-1], key="report_year")
    with rep_c2:
        sel_quarter = st.selectbox("Report Quarter", list(QUARTER_MONTHS.keys()), index=current_quarter_num - 1, key="report_quarter")

    st.markdown("<h4 class='section-title' style='font-size:1rem; margin-top:1rem;'>Preview — Benchmark Movement</h4>", unsafe_allow_html=True)
    preview_b_stats = quarterly_benchmark_stats(crude_df, sel_year, sel_quarter)
    if not preview_b_stats.empty:
        st.dataframe(preview_b_stats, width="stretch", hide_index=True)
    else:
        st.caption(f"No benchmark readings recorded for {sel_quarter} {sel_year} yet.")

    st.markdown("<h4 class='section-title' style='font-size:1rem; margin-top:1rem;'>Preview — Refined Product Movement</h4>", unsafe_allow_html=True)
    preview_p_stats = quarterly_product_stats(product_df, sel_year, sel_quarter)
    if not preview_p_stats.empty:
        st.dataframe(preview_p_stats, width="stretch", hide_index=True)
    else:
        st.caption(f"No product readings recorded for {sel_quarter} {sel_year} yet.")

    preview_devs = developments_for_period(dev_df, sel_year, sel_quarter)
    st.markdown(f"<h4 class='section-title' style='font-size:1rem; margin-top:1rem;'>Preview — Market Developments ({len(preview_devs)})</h4>", unsafe_allow_html=True)
    if not preview_devs.empty:
        st.dataframe(
            preview_devs[["dev_date", "category", "headline", "impact", "source"]],
            width="stretch",
            hide_index=True,
        )
    else:
        st.caption("No developments logged for this quarter yet — visit the Market Intelligence Monitoring tab.")

    st.markdown("<br>", unsafe_allow_html=True)

    ai_col1, ai_col2 = st.columns([1, 3])
    with ai_col1:
        if st.button("✨ Generate outlook with AI", width="stretch", key="ai_generate_outlook_btn"):
            configured_key = get_setting("ai_assistant_api_key")
            if not configured_key:
                st.error("No AI assistant API key is configured yet. Add one on the ⚙️ Settings tab first.")
            else:
                try:
                    with st.spinner("Drafting outlook commentary..."):
                        draft_text = generate_ai_outlook(
                            configured_key, sel_quarter, sel_year,
                            preview_b_stats, preview_p_stats, preview_devs,
                        )
                    st.session_state["report_outlook_notes"] = draft_text
                    st.rerun()
                except AIAssistantError as ex:
                    st.error(str(ex))
    with ai_col2:
        st.caption("Drafts a starting point from this quarter's data — review and edit before publishing.")

    outlook_notes = st.text_area(
        "Outlook & Analyst Notes (included in the published report)",
        placeholder="e.g., Demand outlook for next quarter, refinery maintenance schedule impacts, key risks to monitor...",
        key="report_outlook_notes",
    )
    generated_by_input = st.text_input("Prepared By", value="MOG Analyst", key="report_generated_by")

    if st.button("📄 Generate & Publish Quarterly Report", type="primary", key="report_generate_btn"):
        try:
            with st.spinner(f"Compiling {sel_quarter} {sel_year} report for {MOG_DIVISION_NAME}..."):
                report_path = generate_quarterly_report(
                    crude_df, product_df, dev_df,
                    year=sel_year, quarter=sel_quarter,
                    outlook_notes=outlook_notes,
                    generated_by=generated_by_input or "MOG Analyst",
                )
            st.success(f"Report published: {Path(report_path).name}")
            st.rerun()
        except Exception as ex:
            st.error(f"Failed to generate quarterly report: {str(ex)}")

    st.markdown("<hr style='border-color:#E1DFDD; margin:1.5rem 0;'>", unsafe_allow_html=True)
    st.markdown("<h4 class='section-title' style='font-size:1rem;'>Published Report Archive</h4>", unsafe_allow_html=True)
    generated_reports = list_generated_reports()
    if generated_reports:
        for report_file in generated_reports:
            rc1, rc2 = st.columns([4, 1])
            with rc1:
                st.markdown(f"📄 **{report_file.name}**")
                st.caption(f"Generated {datetime.fromtimestamp(report_file.stat().st_mtime).strftime('%d %b %Y, %H:%M')}")
            with rc2:
                with open(report_file, "rb") as f:
                    st.download_button(
                        "Download",
                        data=f,
                        file_name=report_file.name,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"download_report_{report_file.name}",
                        width="stretch",
                    )
    else:
        st.caption("No quarterly reports have been published yet.")

# ==============================================================================
# TAB 5 — SETTINGS
# ==============================================================================
with tab_settings:
    st.markdown("<h3 class='section-title'>Platform Settings</h3>", unsafe_allow_html=True)

    st.markdown("<h4 class='section-title' style='font-size:1rem;'>AI Assistant</h4>", unsafe_allow_html=True)
    st.caption(
        "Used to draft the Outlook & Analyst Notes section of quarterly reports from that quarter's "
        "benchmark, product, and market development data. You can always edit or replace the draft "
        "before publishing — this never publishes anything on its own."
    )

    existing_key = get_setting("ai_assistant_api_key")
    key_status = "🟢 Configured" if existing_key else "⚪ Not configured"
    st.markdown(f"**Status:** {key_status}")

    with st.form("ai_settings_form"):
        new_key_input = st.text_input(
            "API Key",
            type="password",
            placeholder="Enter API key" if not existing_key else "•" * 20 + " (leave blank to keep current key)",
            key="ai_api_key_input",
        )
        s1, s2 = st.columns([1, 1])
        save_clicked = s1.form_submit_button("Save", type="primary", width="stretch")
        clear_clicked = s2.form_submit_button("Clear Key", width="stretch")

        if save_clicked:
            if new_key_input.strip():
                set_setting("ai_assistant_api_key", new_key_input.strip())
                st.success("API key saved.")
                st.rerun()
            else:
                st.warning("Enter a key before saving, or use Clear Key to remove the existing one.")

        if clear_clicked:
            delete_setting("ai_assistant_api_key")
            st.success("API key removed.")
            st.rerun()

    st.caption("The key is stored locally in this app's database and is never displayed once saved.")

# ------------------------------------------------------------------------------
# SYSTEM INFRASTRUCTURE MAPPING REGISTRY & SYSTEM OVERLAYS
# ------------------------------------------------------------------------------
@st.dialog("📋 Infrastructure Data Source Protocols", width="large")
def show_sources_registry():
    st.markdown("### Upstream Mapping & Web Scraping Endpoints")
    source_items = [{"System Tracker Identifier": k, "Target Network URL Link": v} for k, v in SOURCES.items()]
    st.table(pd.DataFrame(source_items))
    st.markdown("---")
    st.caption("All queries fallback to 'Source system didn't publish' if validation parameters are missed.")

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
footer_c1, footer_c2, footer_c3 = st.columns([1, 2, 1])
with footer_c2:
    st.markdown("<div class='app-footer'>", unsafe_allow_html=True)
    if st.button("🔗 View Upstream System Sources Protocol", help="Click to view full data routing maps", key="footer_sources_btn"):
        show_sources_registry()
    st.markdown("<p style='margin-top:0.6rem;'>KNPC Business Data Intelligence Platform v5.0 • Secure Node</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
