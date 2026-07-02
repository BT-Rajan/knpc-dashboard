# KNPC Business Data Intelligence Platform v5.0

A market intelligence, crude benchmark tracking, and quarterly reporting platform for KNPC — built with Python, Streamlit, and SQLite.

Originally a single-page price dashboard, this has been restructured into a four-module BI platform aligned to the following KPIs:

1. **Market Intelligence Monitoring** — follow major developments affecting crude oil and refined product markets; monitor OPEC+, IEA, EIA, and industry publications; track geopolitical/economic/industry events; assess potential market impact; and feed findings into reporting.
2. **Benchmark Price Tracking** — review, monitor, and follow up on Brent, WTI, and Dubai (plus Oman and Kuwait Export Crude for regional context), including daily/weekly fluctuation summaries and historical records.
3. **Quarterly Market Reports** — generate and publish a quarterly market report (Word document) for the Marketing Operations Group (MOG) division.
4. **Executive Overview** — the original consolidated dashboard (benchmarks, refined product proxies, volatility charts, live feed, manual correction ledger).

---

## One-Click Installer (recommended, Windows)

The easiest way to set this platform up on a new computer — no manual `pip install`, no terminal commands to remember, and no GUI toolkit dependency (earlier drafts used a Tkinter GUI, which isn't guaranteed to ship with every Python install — this version doesn't need it).

> **Note:** since this repository is private, `start.bat` sets up the copy of the project it's already sitting in rather than downloading anything from GitHub — you'll need to have cloned or downloaded this repo first (the usual way) before running it.

1. Clone or download this repository.
2. Double-click `start.bat` in the project folder.

`start.bat` checks that Python is installed and on your PATH (opening the official download page for you if it isn't), then runs `installer/setup_and_play.py`, a console program that:

1. Sets up its own isolated Python environment in this folder (won't conflict with anything else on your machine) and installs requirements
2. Runs the first data pull (`main.py`)
3. Starts the dashboard and opens it in your browser

All of that runs in the background — and while it does, you get a choice:

- **[P] Play a quick trivia game** — oil & energy market trivia (Q&A sourced from [`installer_game.txt`](installer_game.txt), which you can freely edit or add questions to; see the format guide at the top of that file). Questions are shuffled (never played twice in a row), and the game only ends the moment the dashboard server is confirmed up and responding — at which point it shows your final score as `correct/attempted` (e.g. `4/7`) and hands off to the finished dashboard.
- **[W] Wait quietly** — a simple live progress view, with raw pip/Python output translated into plain-language status lines instead of a wall of logs.

Re-running the installer at any time re-installs cleanly in place — handy for picking up updates.

## Manual Installation (alternative, all platforms)

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env` and edit as needed:

```
ANALYTICS_LOOKBACK_DAYS=7
```

> All other `.env` values are optional overrides for URL endpoints.

### 3. Run the data pipeline (first time)

```bash
python main.py
```

This initialises the database, scrapes live crude/product prices, runs the market intelligence monitoring sweep (OPEC+/IEA/EIA/geopolitical/economic/industry news), and generates the daily Excel report.

### 4. Launch the platform

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

**Default credentials:** `admin` / `admin`
(Change these in `app.py` before production deployment — see Security Notes below.)

---

## File Structure

```
knpc-dashboard/
├── app.py               — Streamlit BI platform (4-tab UI)
├── main.py               — CLI pipeline runner (prices + monitoring + exports)
├── collectors.py          — Web scrapers: benchmarks, products, market developments
├── analytics.py           — Summaries, quarterly stats, weekly change, history
├── database.py            — SQLite schema & insert helpers
├── exporter.py             — CSV/Excel export logic
├── report_generator.py     — Quarterly Word report builder (python-docx)
├── config.py               — Paths, URLs, product map, categories, quarters
├── .env                    — Environment variables
├── requirements.txt
├── data/
│   └── market_data.db     — Auto-created SQLite database
└── exports/
    ├── *.csv / *.xlsx      — Daily exports
    └── quarterly_reports/  — Published MOG quarterly reports (.docx)
```

---

## Data Model

In addition to the original `crude_prices`, `product_prices`, `product_source_notes`,
`product_collection_attempts`, `market_news`, and `run_log` tables, two tables were added:

- **`market_developments`** — logged developments (category, headline, summary, source, URL, impact assessment, who logged it). Populated automatically by the monitoring sweep and/or manually by analysts from the Market Intelligence tab.
- **`quarterly_reports`** — an audit trail of every generated quarterly report (quarter, year, file path, who generated it, when).

## Usage

| Action | How |
|--------|-----|
| Collect live prices + run monitoring sweep | **⚙️ Control Console → Force Live Pipeline Loop**, or `python main.py` |
| Run only the market intelligence sweep | **Market Intelligence Monitoring tab → Run Monitoring Sweep Now** |
| Log a development manually | **Market Intelligence Monitoring tab → Log a Market Development Manually** |
| Review benchmark daily/weekly moves | **Benchmark Price Tracking tab** |
| Generate & publish a quarterly report | **Quarterly Market Reports tab → Generate & Publish Quarterly Report** |
| Download Excel report | **📥 Excel** in the header |
| Enter a manual price correction | **Executive Overview → Operational Field Corrections Ledger** |
| View source endpoints | **View Data Source Registry** in the footer |

---

## Streamlit Fixes Applied in This Revision

- Replaced the deprecated `st.components.v1.html()` call (slated for removal) with `st.iframe()`.
- Replaced `use_container_width=True/False` (removed after 2025-12-31) with the current `width="stretch"/"content"` parameter across every button, download button, and dataframe.
- Hardened `database.py` connections with `check_same_thread=False` and a busy timeout, and wrapped every write in `try/finally` so a mid-transaction error can no longer leak an open SQLite connection.
- Escaped all scraped/user-supplied text (headlines, sources, URLs) with `html.escape()` before rendering via `unsafe_allow_html=True`, closing an HTML/script-injection gap in the news and intelligence feeds.
- Replaced the `import main; main.main()` re-import pattern in the Control Console with direct calls to `collectors.run_all_collectors()` / `exporter.export_daily_*()`.
- Added explicit, unique `key=` values to every button/widget so the new tabs can't collide with `DuplicateWidgetID` errors as the app grows.
- Fixed raw HTML tags (e.g. `<span class="badge-source-tracker">...`) showing as literal text on the price tiles, news feed, and developments feed. Cause: Streamlit's Markdown renderer treats a 4+ space indented line as a code block *before* it processes `unsafe_allow_html`, so the indented multi-line HTML strings used to build those cards were getting escaped instead of rendered. Fixed by flattening every generated HTML block to a single line.
- Removed dead code: `ui_assets.py` (an unused leftover dark-theme CSS module) and an unused `import sqlite3` in `app.py`.
- Fixed invisible login/form input boxes — inputs had no explicit background or border, so white-on-white made them disappear against the card behind them.

## Performance

Every widget interaction in Streamlit reruns the entire script, and the app was re-querying all four SQLite tables (and recomputing every summary) from scratch on every single click or keystroke. `load_dashboard_data()` and the two summary functions are now wrapped in `@st.cache_data(ttl=60)`, cutting a typical rerun from ~2.5s to ~0.3s in testing. The cache is invalidated immediately (`invalidate_data_cache()`) right after any write — manual price entry, monitoring sweep, pipeline run, development log — so you always see your own changes right away rather than waiting for the 60s TTL.

## UI

Restyled to Microsoft's Fluent Design language (Windows 11 / Office / Teams): light surfaces, Segoe UI, a single blue accent (`#0078D4`), and Fluent-style elevation. Price tiles, the news feed, and the market developments feed were also rebuilt as proper bordered/shadowed cards (`.ms-tile`, `.ms-feed-card`) instead of stacked plain text, and a `.streamlit/config.toml` theme file was added so native widgets (alerts, inputs, sliders) pick up the same palette automatically. A post-login splash screen now pre-warms the data cache before the dashboard renders, avoiding the piecemeal "popping in" look on first load.

## Settings & AI-Assisted Outlook Drafting

The **⚙️ Settings** tab lets you save an API key for the AI assistant used to draft the "Outlook & Analyst Notes" section of quarterly reports. Click **✨ Generate outlook with AI** on the Quarterly Market Reports tab to produce a starting draft from that quarter's benchmark, product, and development data — review and edit it before publishing, exactly like manually-typed notes. The key is stored locally in the app's database and is never displayed once saved.

---

## Deployment & Security Notes

- The app uses **SQLite** — no external database needed.
- For production, replace the hardcoded `admin/admin` credentials with a secrets manager, SSO, or environment-variable-based check — this was not in scope for this revision but should be addressed before any external exposure.
- To run continuously with auto-refresh, schedule `python main.py` via cron or Windows Task Scheduler (e.g., daily for prices, hourly for the monitoring sweep).
- The market intelligence and Dubai benchmark scrapers use best-effort public HTML/RSS scraping with graceful fallback to "Source system didn't publish" / manual entry, exactly like the original KPC and refined-product collectors — site structure changes on any one source will not break the others.
- Tested on Python 3.10+, Streamlit 1.58.
