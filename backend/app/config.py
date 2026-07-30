"""
Central config. Hardcoded credentials live here on purpose (internal tool,
single admin + single viewer account, no self-signup).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

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

# --- Report Generation ---
QUARTER_MONTHS = {
    "Q1": (1, 3),
    "Q2": (4, 6),
    "Q3": (7, 9),
    "Q4": (10, 12),
}
REPORTS_DIR = BASE_DIR / "exports" / "quarterly_reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

MOG_DIVISION_NAME = "Marketing Operations Group (MOG)"

# Product metadata (proxy mapping from main branch)
PRODUCT_PROXY_MAP = {
    "NAPHTHA": {
        "market": "Singapore / Regional Proxy",
        "proxy_type": "Naphtha / regional naphtha proxy",
        "benchmark_basis": "Japan C&F Naphtha direction",
        "notes": "Japan C&F naphtha and regional naphtha prices are commonly used as proxies for Asian naphtha direction."
    },
    "GASOLINE92": {
        "market": "Singapore / Regional Proxy",
        "proxy_type": "Regional gasoline proxy",
        "benchmark_basis": "CME RBOB Gasoline / regional gasoline proxy",
        "notes": "Direct Singapore MoPS assessments are often paywalled. Public regional gasoline proxies are utilized."
    },
    "GASOLINE95": {
        "market": "Singapore / Regional Proxy",
        "proxy_type": "Premium gasoline proxy",
        "benchmark_basis": "Premium regional gasoline markers",
        "notes": "Tracks high-octane gasoline direction metrics and premium regional retail benchmark directionals."
    },
    "JETKERO": {
        "market": "Singapore / Regional Proxy",
        "proxy_type": "Jet fuel / kerosene proxy",
        "benchmark_basis": "US Gulf Coast Kerosene / regional proxy",
        "notes": "Tracking aviation component premium metrics via highly liquid regional public proxy channels."
    },
    "GASOIL10": {
        "market": "Singapore / Regional Proxy",
        "proxy_type": "Middle distillate proxy",
        "benchmark_basis": "ICE Gasoil / regional low-sulfur diesel proxy",
        "notes": "Tracking ultra-low sulfur gasoil regional trends against global low-sulfur indicators."
    },
    "FUELOIL180": {
        "market": "Singapore / Regional Proxy",
        "proxy_type": "Residual fuel proxy",
        "benchmark_basis": "Singapore fuel oil / high sulphur fuel oil proxy",
        "notes": "Direct Singapore 180 CST assessments are often paywalled. Public fuel oil proxies are used."
    },
    "FUELOIL380": {
        "market": "Singapore / Regional Proxy",
        "proxy_type": "Residual fuel proxy",
        "benchmark_basis": "ICE Singapore Fuel Oil 380 CST proxy",
        "notes": "ICE Singapore fuel oil 380 CST or public HSFO proxies are used where available."
    },
    "LPG": {
        "market": "Singapore / Regional Proxy",
        "proxy_type": "LPG proxy",
        "benchmark_basis": "Saudi Aramco CP / Mont Belvieu / regional LPG proxy",
        "notes": "LPG pricing is often represented through Saudi Aramco CP, Mont Belvieu, or public regional component metrics."
    }
}
