# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Initialize core environmental parameter registries
load_dotenv()

# Structural Workspace Layout Infrastructure
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EXPORT_DIR = BASE_DIR / "exports"

# Verify platform directory footprints exist securely
DATA_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)

# Path to the SQLite local database file footprint
DATABASE_PATH = DATA_DIR / "market_data.db"

# Dynamic Lookback Constraints mapped to environmental variables
ANALYTICS_LOOKBACK_DAYS = int(os.getenv("ANALYTICS_LOOKBACK_DAYS", 7))

# Endpoint Asset Allocation Strategy Routes 
SOURCES = {
    "kpc_oil_prices": "https://eapp.kpc.com.kw/oilprices/oilprices.aspx",
    "oilprice_news": "https://oilprice.com/Latest-Energy-News/World-News/",
    "oilprice_charts": "https://oilprice.com/oil-price-charts/",
    "investing_commodities": "https://www.investing.com/commodities/",
    "tradingeconomics_energy": "https://tradingeconomics.com/commodities",
    "yahoo_chart": "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval=1d",
    # Market intelligence monitoring endpoints (OPEC+ / IEA / EIA / geopolitical & industry news)
    "opec_press": "https://www.opec.org/opec_web/en/press_room/28.htm",
    "iea_news": "https://www.iea.org/news",
    "eia_today_in_energy": "https://www.eia.gov/rss/todayinenergy.xml",
    "reuters_energy": "https://oilprice.com/Latest-Energy-News/World-News/",
}

# Primary Ticker Mappings for API Data Gathering Ingestion Layer
YAHOO_BENCHMARKS = {
    "Brent": "BZ=F",
    "WTI": "CL=F",
    "Oman": "O6=F"  # Monitored with multi-ticker safety nets inside collectors
}

# Dubai crude has no reliable public futures ticker, so it is tracked via
# web-scrape fallback (same precedence chain as refined products) with a
# manual-entry safety net, consistent with Kuwait Export Crude handling.
DUBAI_SOURCE_ORDER = ["tradingeconomics_energy", "oilprice_charts", "investing_commodities"]
DUBAI_KEYWORDS = ["dubai crude", "dubai", "oman/dubai", "platts dubai"]

# Source-Precedence Fallback Evaluation Hierarchy Matrix
PRODUCT_SOURCE_ORDER = ["oilprice_charts", "investing_commodities", "tradingeconomics_energy"]

# Market Intelligence Monitoring — development categories tracked for the
# "Monitor major developments in the global oil and energy industry" KPI.
DEVELOPMENT_CATEGORIES = {
    "OPEC+": {
        "source_key": "opec_press",
        "keywords": ["opec", "opec+", "production cut", "production quota", "output target"],
    },
    "IEA": {
        "source_key": "iea_news",
        "keywords": ["iea", "international energy agency", "oil market report"],
    },
    "EIA": {
        "source_key": "eia_today_in_energy",
        "keywords": ["eia", "energy information administration", "short-term energy outlook", "steo"],
    },
    "Geopolitical": {
        "source_key": "reuters_energy",
        "keywords": ["sanction", "war", "conflict", "strait of hormuz", "attack", "tension", "ceasefire", "houthi"],
    },
    "Economic": {
        "source_key": "reuters_energy",
        "keywords": ["inflation", "interest rate", "fed", "gdp", "recession", "demand outlook", "dollar"],
    },
    "Industry": {
        "source_key": "reuters_energy",
        "keywords": ["refinery", "pipeline", "tanker", "shipping", "outage", "maintenance", "capacity"],
    },
}

# Simple keyword-based impact heuristic used to pre-tag scraped developments.
# Analysts can always override this in the Market Intelligence tab.
IMPACT_KEYWORDS = {
    "High": ["war", "attack", "sanction", "strait of hormuz", "production cut", "supply disruption", "outage"],
    "Medium": ["opec+", "quota", "tension", "recession", "interest rate", "pipeline"],
}

# Quarter labels used across the Quarterly Market Reports module
QUARTER_MONTHS = {
    "Q1": (1, 3),
    "Q2": (4, 6),
    "Q3": (7, 9),
    "Q4": (10, 12),
}

REPORTS_DIR = BASE_DIR / "exports" / "quarterly_reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

MOG_DIVISION_NAME = "Marketing Operations Group (MOG)"

# Complete Production Asset Proxy Mapping Matrix
PRODUCT_PROXY_MAP = {
    "Naphtha": {
        "market": "Singapore / Regional Proxy",
        "proxy_type": "Naphtha / regional naphtha proxy",
        "benchmark_basis": "Japan C&F Naphtha direction",
        "keywords": ["naphtha", "japan naphtha", "singapore naphtha", "c&f japan"],
        "notes": "Japan C&F naphtha and regional naphtha prices are commonly used as proxies for Asian naphtha direction."
    },
    "Gasoline 92": {
        "market": "Singapore / Regional Proxy",
        "proxy_type": "Regional gasoline proxy",
        "benchmark_basis": "CME RBOB Gasoline / regional gasoline proxy",
        "keywords": ["rbob gasoline", "gasoline 92", "singapore gasoline 92", "92 ron", "gasoline"],
        "notes": "Direct Singapore MoPS assessments are often paywalled. Public regional gasoline proxies are utilized."
    },
    "Gasoline 95": {
        "market": "Singapore / Regional Proxy",
        "proxy_type": "Premium gasoline proxy",
        "benchmark_basis": "Premium regional gasoline markers",
        "keywords": ["gasoline 95", "95 ron", "premium gasoline", "gasoline", "motor gasoline"],
        "notes": "Tracks high-octane gasoline direction metrics and premium regional retail benchmark directionals."
    },
    "Jet Kerosene": {
        "market": "Singapore / Regional Proxy",
        "proxy_type": "Jet fuel / kerosene proxy",
        "benchmark_basis": "US Gulf Coast Kerosene / regional proxy",
        "keywords": ["jet fuel", "kerosene", "aviation fuel", "jet", "jet/kerosene"],
        "notes": "Tracking aviation component premium metrics via highly liquid regional public proxy channels."
    },
    "Gasoil 10ppm": {
        "market": "Singapore / Regional Proxy",
        "proxy_type": "Middle distillate proxy",
        "benchmark_basis": "ICE Gasoil / regional low-sulfur diesel proxy",
        "keywords": ["heating oil", "gasoil", "diesel", "singapore gasoil", "gasoil 10ppm"],
        "notes": "Tracking ultra-low sulfur gasoil regional trends against global low-sulfur indicators."
    },
    "Fuel Oil 180 CST": {
        "market": "Singapore / Regional Proxy",
        "proxy_type": "Residual fuel proxy",
        "benchmark_basis": "Singapore fuel oil / high sulphur fuel oil proxy",
        "keywords": ["fuel oil", "180 cst", "high sulphur fuel oil", "hsfo", "fuel oil 180"],
        "notes": "Direct Singapore 180 CST assessments are often paywalled. Public fuel oil proxies are used."
    },
    "Fuel Oil 380 CST": {
        "market": "Singapore / Regional Proxy",
        "proxy_type": "Residual fuel proxy",
        "benchmark_basis": "ICE Singapore Fuel Oil 380 CST proxy",
        "keywords": ["fuel oil 380", "380 cst", "bunker fuel", "fuel oil", "hsfo 380"],
        "notes": "ICE Singapore fuel oil 380 CST or public HSFO proxies are used where available."
    },
    "LPG": {
        "market": "Singapore / Regional Proxy",
        "proxy_type": "LPG proxy",
        "benchmark_basis": "Saudi Aramco CP / Mont Belvieu / regional LPG proxy",
        "keywords": ["lpg", "propane", "butane", "mont belvieu", "aramco cp", "liquefied petroleum"],
        "notes": "LPG pricing is often represented through Saudi Aramco CP, Mont Belvieu, or public regional component metrics."
    }
}