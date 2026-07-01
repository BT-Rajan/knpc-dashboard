# database.py
import sqlite3
from datetime import datetime
from config import DATABASE_PATH


def get_connection():
    """Establishes a resilient connection to the local database file footprint."""
    # check_same_thread=False: Streamlit's "Force Live Pipeline Loop" control
    # console action, and Streamlit's own script reruns, can execute DB calls
    # from different worker threads within the same process. A plain
    # sqlite3.connect() raises "SQLite objects created in a thread can only
    # be used in that same thread" in that scenario. A busy_timeout avoids
    # "database is locked" errors when two writers overlap briefly.
    conn = sqlite3.connect(DATABASE_PATH, timeout=30, check_same_thread=False)
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def _ensure_column(cur, table, column, definition):
    cur.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cur.fetchall()]
    if column not in columns:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    """Initializes and verifies table schematics for the workspace data grids."""
    conn = get_connection()
    try:
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS crude_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            price_date TEXT,
            benchmark TEXT,
            price REAL,
            previous_price REAL,
            daily_change REAL,
            daily_change_pct REAL,
            unit TEXT,
            source TEXT,
            collected_at TEXT,
            UNIQUE(price_date, benchmark, source)
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS product_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            price_date TEXT,
            market TEXT,
            product TEXT,
            price REAL,
            previous_price REAL,
            daily_change REAL,
            daily_change_pct REAL,
            unit TEXT,
            source TEXT,
            status TEXT,
            notes TEXT,
            proxy_type TEXT,
            benchmark_basis TEXT,
            collected_at TEXT,
            UNIQUE(price_date, market, product, source)
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS product_source_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT UNIQUE,
            market TEXT,
            proxy_type TEXT,
            benchmark_basis TEXT,
            notes TEXT,
            updated_at TEXT
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS product_collection_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_date TEXT,
            market TEXT,
            product TEXT,
            source TEXT,
            status TEXT,
            message TEXT,
            collected_at TEXT
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS market_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_date TEXT,
            source TEXT,
            headline TEXT,
            url TEXT,
            collected_at TEXT,
            UNIQUE(news_date, headline)
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS run_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_time TEXT,
            status TEXT,
            message TEXT
        )""")

        # Market Intelligence Monitoring: tracks major developments affecting
        # crude & refined product markets (OPEC+, IEA, EIA, geopolitical, etc.)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS market_developments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dev_date TEXT,
            category TEXT,
            headline TEXT,
            summary TEXT,
            source TEXT,
            url TEXT,
            impact TEXT,
            entered_by TEXT,
            created_at TEXT,
            UNIQUE(dev_date, headline)
        )""")

        # Quarterly Market Reports (MOG division) generation log
        cur.execute("""
        CREATE TABLE IF NOT EXISTS quarterly_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quarter TEXT,
            year INTEGER,
            file_path TEXT,
            generated_by TEXT,
            generated_at TEXT,
            notes TEXT
        )""")

        # Application settings (key/value) — used for the AI assistant API
        # key and any future configurable options, entered from the
        # Settings tab instead of being hardcoded in a file.
        cur.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT,
            updated_at TEXT
        )""")

        conn.commit()
    finally:
        conn.close()


def insert_crude_price(price_date, benchmark, price, unit, source):
    conn = get_connection()
    try:
        cur = conn.cursor()
        now_str = datetime.now().isoformat(timespec="seconds")
        cur.execute("""
            INSERT INTO crude_prices (price_date, benchmark, price, unit, source, collected_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(price_date, benchmark, source) DO UPDATE SET
                price=excluded.price,
                collected_at=excluded.collected_at
        """, (price_date, benchmark, price, unit, source, now_str))
        conn.commit()
    finally:
        conn.close()


def insert_product_price(price_date, market, product, price, unit, source, status="collected", notes="", proxy_type="", benchmark_basis=""):
    conn = get_connection()
    try:
        cur = conn.cursor()
        now_str = datetime.now().isoformat(timespec="seconds")
        cur.execute("""
            INSERT INTO product_prices (
                price_date, market, product, price, unit, source, status, notes, proxy_type, benchmark_basis, collected_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(price_date, market, product, source) DO UPDATE SET
                price=excluded.price,
                status=excluded.status,
                notes=excluded.notes,
                collected_at=excluded.collected_at
        """, (price_date, market, product, price, unit, source, status, notes, proxy_type, benchmark_basis, now_str))
        conn.commit()
    finally:
        conn.close()


def upsert_product_source_note(product, market, proxy_type, benchmark_basis, notes):
    conn = get_connection()
    try:
        cur = conn.cursor()
        now_str = datetime.now().isoformat(timespec="seconds")
        cur.execute("""
            INSERT INTO product_source_notes (product, market, proxy_type, benchmark_basis, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(product) DO UPDATE SET
                market=excluded.market,
                proxy_type=excluded.proxy_type,
                benchmark_basis=excluded.benchmark_basis,
                notes=excluded.notes,
                updated_at=excluded.updated_at
        """, (product, market, proxy_type, benchmark_basis, notes, now_str))
        conn.commit()
    finally:
        conn.close()


def insert_product_attempt(attempt_date, market, product, source, status, message):
    conn = get_connection()
    try:
        cur = conn.cursor()
        now_str = datetime.now().isoformat(timespec="seconds")
        cur.execute("""
            INSERT INTO product_collection_attempts (attempt_date, market, product, source, status, message, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (attempt_date, market, product, source, status, message, now_str))
        conn.commit()
    finally:
        conn.close()


def insert_news(news_date, source, headline, url):
    conn = get_connection()
    try:
        cur = conn.cursor()
        now_str = datetime.now().isoformat(timespec="seconds")
        cur.execute("""
            INSERT OR IGNORE INTO market_news (news_date, source, headline, url, collected_at)
            VALUES (?, ?, ?, ?, ?)
        """, (news_date, source, headline, url, now_str))
        conn.commit()
    finally:
        conn.close()


def insert_development(dev_date, category, headline, summary, source, url, impact, entered_by="System"):
    """Logs a market intelligence development (OPEC+/IEA/EIA/geopolitical/economic/industry)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        now_str = datetime.now().isoformat(timespec="seconds")
        cur.execute("""
            INSERT INTO market_developments (
                dev_date, category, headline, summary, source, url, impact, entered_by, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(dev_date, headline) DO UPDATE SET
                category=excluded.category,
                summary=excluded.summary,
                source=excluded.source,
                url=excluded.url,
                impact=excluded.impact
        """, (dev_date, category, headline, summary, source, url, impact, entered_by, now_str))
        conn.commit()
    finally:
        conn.close()


def log_quarterly_report(quarter, year, file_path, generated_by="System", notes=""):
    """Records a generated quarterly market report for the MOG division audit trail."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        now_str = datetime.now().isoformat(timespec="seconds")
        cur.execute("""
            INSERT INTO quarterly_reports (quarter, year, file_path, generated_by, generated_at, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (quarter, year, file_path, generated_by, now_str, notes))
        conn.commit()
    finally:
        conn.close()


def get_setting(key: str, default=None):
    """Reads a single app setting (e.g. the AI assistant API key)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT setting_value FROM app_settings WHERE setting_key = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else default
    finally:
        conn.close()


def set_setting(key: str, value: str):
    """Saves/updates a single app setting."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        now_str = datetime.now().isoformat(timespec="seconds")
        cur.execute("""
            INSERT INTO app_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value=excluded.setting_value,
                updated_at=excluded.updated_at
        """, (key, value, now_str))
        conn.commit()
    finally:
        conn.close()


def delete_setting(key: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM app_settings WHERE setting_key = ?", (key,))
        conn.commit()
    finally:
        conn.close()


def log_run(status, message):
    conn = get_connection()
    try:
        cur = conn.cursor()
        now_str = datetime.now().isoformat(timespec="seconds")
        cur.execute("INSERT INTO run_log (run_time, status, message) VALUES (?, ?, ?)", (now_str, status, message))
        conn.commit()
    finally:
        conn.close()
