# main.py
from database import init_db, log_run
from collectors import run_all_collectors
from exporter import export_daily_csv, export_daily_excel

def main():
    # Structural DB Footprint Initialization
    init_db()
    
    print("Executing Extraction Pipeline Run...")
    results = run_all_collectors()
    
    # Compile Production Output Formats
    csv_exports = export_daily_csv()
    excel_export = export_daily_excel()

    success_count = sum(1 for r in results if r.get("status") == "success")
    warning_count = sum(1 for r in results if r.get("status") == "warning")
    error_count = sum(1 for r in results if r.get("status") == "error")
    manual_count = sum(1 for r in results if r.get("status") == "manual_required")

    log_run(
        "completed", 
        f"Success={success_count}, Warning={warning_count}, Error={error_count}, ManualRequired={manual_count}, CSV={len(csv_exports)}, Excel=1"
    )

    dev_results = [r for r in results if "developments_logged" in r]
    dev_count = sum(r.get("developments_logged", 0) for r in dev_results)

    print("\n=======================================================")
    print("⚜️ Market Data & Intelligence Ingestion Pipeline Run Complete")
    print("=======================================================")
    for r in results:
        print(f" -> {r}")
    print(f"\nMarket developments logged this run: {dev_count}")

    print("\nGenerated CSV Storage Matrix Rows:")
    for f in csv_exports:
        print(f"  [+] {f}")

    print("\nGenerated Excel Production Analytical Workbook:")
    print(f"  [*] {excel_export}")

if __name__ == "__main__":
    main()