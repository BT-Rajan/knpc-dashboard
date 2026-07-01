# exporter.py
from datetime import date
from pathlib import Path
import sqlite3
import pandas as pd
from config import DATABASE_PATH, EXPORT_DIR
from analytics import crude_summary, product_summary

def _read_table(conn, table_name):
    try:
        return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    except Exception:
        return pd.DataFrame()

def latest_excel_file():
    """Finds the most recently compiled workbook file."""
    files = list(EXPORT_DIR.glob("*_market_data_collection.xlsx"))
    if not files:
        return None
    return max(files, key=lambda f: f.stat().st_mtime)

def export_daily_csv():
    today = str(date.today())
    tables = [
        "crude_prices",
        "product_prices",
        "product_source_notes",
        "product_collection_attempts",
        "market_news",
        "market_developments",
        "quarterly_reports",
        "run_log",
    ]
    exported_files = []

    conn = sqlite3.connect(DATABASE_PATH)
    for table in tables:
        df = _read_table(conn, table)
        output_path = EXPORT_DIR / f"{today}_{table}.csv"
        df.to_csv(output_path, index=False)
        exported_files.append(str(output_path))

    conn.close()
    return exported_files

def export_daily_excel():
    today = str(date.today())
    output_path = EXPORT_DIR / f"{today}_market_data_collection.xlsx"

    conn = sqlite3.connect(DATABASE_PATH)
    crude = _read_table(conn, "crude_prices")
    products = _read_table(conn, "product_prices")
    source_notes = _read_table(conn, "product_source_notes")
    attempts = _read_table(conn, "product_collection_attempts")
    news = _read_table(conn, "market_news")
    developments = _read_table(conn, "market_developments")
    reports_log = _read_table(conn, "quarterly_reports")
    logs = _read_table(conn, "run_log")
    conn.close()

    # Generate analytical summaries utilizing our fallback rules
    c_summary = crude_summary(crude)
    p_summary = product_summary(products)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        c_summary.to_excel(writer, sheet_name="Benchmark_Summary", index=False)
        crude.to_excel(writer, sheet_name="All_Benchmarks", index=False)

        if not crude.empty:
            for benchmark in sorted(crude["benchmark"].dropna().unique()):
                sheet_name = str(benchmark).replace("/", "_").replace("\\", "_")[:31]
                crude[crude["benchmark"] == benchmark].to_excel(writer, sheet_name=sheet_name, index=False)

        p_summary.to_excel(writer, sheet_name="Product_Summary", index=False)
        products.to_excel(writer, sheet_name="All_Products", index=False)

        if not products.empty:
            for product in sorted(products["product"].dropna().unique()):
                sheet_name = str(product).replace("/", "_").replace("\\", "_").replace(" ", "_")[:31]
                products[products["product"] == product].to_excel(writer, sheet_name=sheet_name, index=False)

        source_notes.to_excel(writer, sheet_name="Product_Source_Notes", index=False)
        attempts.to_excel(writer, sheet_name="Product_Attempts", index=False)
        news.to_excel(writer, sheet_name="Market_News", index=False)
        developments.to_excel(writer, sheet_name="Market_Developments", index=False)
        reports_log.to_excel(writer, sheet_name="Quarterly_Reports_Log", index=False)
        logs.to_excel(writer, sheet_name="Run_Log", index=False)

    return str(output_path)