"""
Central config. Hardcoded credentials live here on purpose (internal tool,
single admin + single viewer account, no self-signup).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
EXPORT_TMP_DIR = BASE_DIR / "tmp_exports"
EXPORT_TMP_DIR.mkdir(exist_ok=True)

# --- Auth (hardcoded, as requested) ---
USERS = {
    "admin": {"password": "Yellow#G0#", "role": "admin"},
    "user": {"password": "Blue#M1nt", "role": "viewer"},
}
SESSION_SECRET = os.getenv("SESSION_SECRET", "knpc-local-session-secret-change-me")
SESSION_TTL_HOURS = 12

# --- Database (MySQL) ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "knpc_dashboard")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4",
)

# --- Scraping ---
DEFAULT_SCRAPE_FREQUENCY_MINUTES = int(os.getenv("SCRAPE_FREQUENCY_MINUTES", 30))
SCRAPE_REQUEST_TIMEOUT = 15
SCRAPE_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# --- AI facility ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_API_URL = os.getenv("CLAUDE_API_URL", "https://api.anthropic.com/v1/messages")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")

# --- Item catalog (top-level nav: category -> items) ---
# Seeded into the DB on first boot; admins can add/disable further items
# and sources from the admin panel afterwards.
SEED_CATALOG = {
    "Crude": [
        {"code": "BRENT", "name": "Brent", "unit": "USD/bbl"},
        {"code": "WTI", "name": "WTI", "unit": "USD/bbl"},
        {"code": "OMAN", "name": "Oman", "unit": "USD/bbl"},
        {"code": "DUBAI", "name": "Dubai", "unit": "USD/bbl"},
        {"code": "KEC", "name": "Kuwait Export Crude", "unit": "USD/bbl"},
    ],
    "Products": [
        {"code": "NAPHTHA", "name": "Naphtha", "unit": "USD/ton"},
        {"code": "GASOLINE92", "name": "Gasoline 92", "unit": "USD/bbl"},
        {"code": "GASOLINE95", "name": "Gasoline 95", "unit": "USD/bbl"},
        {"code": "JETKERO", "name": "Jet Kerosene", "unit": "USD/bbl"},
        {"code": "GASOIL10", "name": "Gasoil 10ppm", "unit": "USD/bbl"},
        {"code": "FUELOIL180", "name": "Fuel Oil 180 CST", "unit": "USD/ton"},
        {"code": "FUELOIL380", "name": "Fuel Oil 380 CST", "unit": "USD/ton"},
        {"code": "LPG", "name": "LPG", "unit": "USD/ton"},
    ],
}

# --- Seed source data, carried over from github.com/BT-Rajan/knpc-dashboard
# (main branch) config.py SOURCES / YAHOO_BENCHMARKS / PRODUCT_PROXY_MAP /
# DUBAI_KEYWORDS. Same underlying websites, re-expressed as rows for this
# app's Source table (url + source_type + value_selector) instead of
# in-code collector functions. Pure data — consumed by app/seed.py, no
# scraper logic changes.
SOURCE_URLS = {
    "kpc_oil_prices": "https://eapp.kpc.com.kw/oilprices/oilprices.aspx",
    "oilprice_charts": "https://oilprice.com/oil-price-charts/",
    "oilprice_news": "https://oilprice.com/Latest-Energy-News/World-News/",
    "investing_commodities": "https://www.investing.com/commodities/",
    "tradingeconomics_energy": "https://tradingeconomics.com/commodities",
    "yahoo_chart": "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval=1d",
}

# Multi-ticker fallback per crude benchmark (Yahoo Finance), tried in order.
YAHOO_TICKERS = {
    "BRENT": ["BZ=F"],
    "WTI": ["CL=F"],
    "OMAN": ["O6=F", "QM=F", "O9=F"],
}

# Keyword-anchored fallback sources (used when a benchmark/product has no
# clean futures ticker, or as a secondary check behind Yahoo) — same
# public pages and keyword lists the old app scanned for a nearby price.
DUBAI_KEYWORDS = ["dubai crude", "dubai", "oman/dubai", "platts dubai"]
KEC_KEYWORDS = ["kec", "kuwait export crude"]
BRENT_KEYWORDS = ["brent"]
WTI_KEYWORDS = ["wti", "west texas intermediate"]
OMAN_KEYWORDS = ["oman crude", "oman"]

# Same public-page fallback chain the old app used for every refined
# product (oilprice.com charts -> investing.com -> tradingeconomics.com),
# and the same per-product keyword lists it searched for.
PRODUCT_SOURCE_ORDER = ["oilprice_charts", "investing_commodities", "tradingeconomics_energy"]
PRODUCT_KEYWORDS = {
    "NAPHTHA": ["naphtha", "japan naphtha", "singapore naphtha", "c&f japan"],
    "GASOLINE92": ["rbob gasoline", "gasoline 92", "singapore gasoline 92", "92 ron", "gasoline"],
    "GASOLINE95": ["gasoline 95", "95 ron", "premium gasoline", "gasoline", "motor gasoline"],
    "JETKERO": ["jet fuel", "kerosene", "aviation fuel", "jet", "jet/kerosene"],
    "GASOIL10": ["heating oil", "gasoil", "diesel", "singapore gasoil", "gasoil 10ppm"],
    "FUELOIL180": ["fuel oil", "180 cst", "high sulphur fuel oil", "hsfo", "fuel oil 180"],
    "FUELOIL380": ["fuel oil 380", "380 cst", "bunker fuel", "fuel oil", "hsfo 380"],
    "LPG": ["lpg", "propane", "butane", "mont belvieu", "aramco cp", "liquefied petroleum"],
}
