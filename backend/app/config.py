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
