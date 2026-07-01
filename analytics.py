# analytics.py
import pandas as pd

def prepare_time_series(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["date_parsed"] = pd.to_datetime(out[date_col], errors="coerce")
    return out

def crude_summary(crude: pd.DataFrame) -> pd.DataFrame:
    if crude.empty:
        return pd.DataFrame(columns=["Benchmark", "Latest Price", "Source"])

    df = prepare_time_series(crude, "price_date")
    df = df.sort_values(["benchmark", "date_parsed", "id"])
    rows = []

    for benchmark, group in df.groupby("benchmark"):
        # Explicit filtering matches our un-published rule assignment
        valid_group = group[group["source"] != "Source system didn't publish"].dropna(subset=["price"])
        
        if valid_group.empty:
            rows.append({
                "Benchmark": benchmark,
                "Latest Date": None,
                "Latest Price": None,
                "Previous Price": None,
                "Daily Change": None,
                "Daily Change %": None,
                "Source": "Source system didn't publish"
            })
            continue

        valid_group = valid_group.sort_values(["date_parsed", "id"])
        latest = valid_group.iloc[-1]
        previous = valid_group.iloc[-2] if len(valid_group) >= 2 else None

        latest_price = latest["price"]
        previous_price = previous["price"] if previous is not None else None
        change = latest_price - previous_price if previous_price is not None else None
        change_pct = (change / previous_price * 100) if previous_price not in [None, 0] else None

        rows.append({
            "Benchmark": benchmark,
            "Latest Date": latest["price_date"],
            "Latest Price": round(float(latest_price), 2),
            "Previous Price": None if previous_price is None else round(float(previous_price), 2),
            "Daily Change": None if change is None else round(float(change), 2),
            "Daily Change %": None if change_pct is None else round(float(change_pct), 2),
            "Source": latest["source"]
        })

    return pd.DataFrame(rows)

def product_summary(products: pd.DataFrame) -> pd.DataFrame:
    if products.empty:
        return pd.DataFrame(columns=["Product", "Latest Price", "Source"])

    df = prepare_time_series(products, "price_date")
    df = df.sort_values(["market", "product", "date_parsed", "id"])
    rows = []

    for (market, product), group in df.groupby(["market", "product"]):
        valid_group = group[group["source"] != "Source system didn't publish"].dropna(subset=["price"])
        
        if valid_group.empty:
            rows.append({
                "Market": market,
                "Product": product,
                "Proxy Type": "",
                "Benchmark Basis": "",
                "Latest Date": None,
                "Latest Price": None,
                "Previous Price": None,
                "Daily Change": None,
                "Daily Change %": None,
                "Status": "manual_required",
                "Notes": "Unpublished from origins",
                "Readings Count": 0,
                "Source": "Source system didn't publish"
            })
            continue

        valid_group = valid_group.sort_values(["date_parsed", "id"])
        latest = valid_group.iloc[-1]
        previous = valid_group.iloc[-2] if len(valid_group) >= 2 else None

        latest_price = latest["price"]
        previous_price = previous["price"] if previous is not None else None
        change = latest_price - previous_price if previous_price is not None else None
        change_pct = (change / previous_price * 100) if previous_price not in [None, 0] else None

        rows.append({
            "Market": market,
            "Product": product,
            "Proxy Type": latest.get("proxy_type", ""),
            "Benchmark Basis": latest.get("benchmark_basis", ""),
            "Latest Date": latest["price_date"],
            "Latest Price": round(float(latest_price), 2),
            "Previous Price": None if previous_price is None else round(float(previous_price), 2),
            "Daily Change": None if change is None else round(float(change), 2),
            "Daily Change %": None if change_pct is None else round(float(change_pct), 2),
            "Status": latest.get("status", "collected"),
            "Notes": latest.get("notes", ""),
            "Readings Count": int(len(valid_group)),
            "Source": latest["source"]
        })

    return pd.DataFrame(rows)

def series_history(df: pd.DataFrame, key_col: str, key_value: str, date_col: str = "price_date") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    out = prepare_time_series(df, date_col)
    filtered = out[(out[key_col] == key_value) & (out["source"] != "Source system didn't publish")]
    return filtered.sort_values("date_parsed")


# ------------------------------------------------------------------------------
# QUARTERLY MARKET REPORT ANALYTICS
# ------------------------------------------------------------------------------
from config import QUARTER_MONTHS


def quarter_date_range(year: int, quarter: str):
    """Returns (start_date, end_date) pandas Timestamps for a given Q1-Q4 label."""
    start_month, end_month = QUARTER_MONTHS[quarter]
    start = pd.Timestamp(year=year, month=start_month, day=1)
    end = (pd.Timestamp(year=year, month=end_month, day=1) + pd.offsets.MonthEnd(1))
    return start, end


def quarterly_benchmark_stats(crude_df: pd.DataFrame, year: int, quarter: str) -> pd.DataFrame:
    """Open/close/high/low/average and change for each crude benchmark within a quarter."""
    if crude_df.empty:
        return pd.DataFrame(columns=["Benchmark", "Open", "Close", "High", "Low", "Average", "Change", "Change %", "Readings"])

    start, end = quarter_date_range(year, quarter)
    df = prepare_time_series(crude_df, "price_date")
    df = df[(df["date_parsed"] >= start) & (df["date_parsed"] <= end)]
    df = df[df["source"] != "Source system didn't publish"].dropna(subset=["price"])

    rows = []
    for benchmark, group in df.groupby("benchmark"):
        group = group.sort_values(["date_parsed", "id"])
        if group.empty:
            continue
        open_price = float(group.iloc[0]["price"])
        close_price = float(group.iloc[-1]["price"])
        change = close_price - open_price
        change_pct = (change / open_price * 100) if open_price else None
        rows.append({
            "Benchmark": benchmark,
            "Open": round(open_price, 2),
            "Close": round(close_price, 2),
            "High": round(float(group["price"].max()), 2),
            "Low": round(float(group["price"].min()), 2),
            "Average": round(float(group["price"].mean()), 2),
            "Change": round(change, 2),
            "Change %": None if change_pct is None else round(change_pct, 2),
            "Readings": int(len(group)),
        })
    return pd.DataFrame(rows)


def quarterly_product_stats(product_df: pd.DataFrame, year: int, quarter: str) -> pd.DataFrame:
    """Open/close/high/low/average and change for each refined product within a quarter."""
    if product_df.empty:
        return pd.DataFrame(columns=["Product", "Open", "Close", "High", "Low", "Average", "Change", "Change %", "Readings"])

    start, end = quarter_date_range(year, quarter)
    df = prepare_time_series(product_df, "price_date")
    df = df[(df["date_parsed"] >= start) & (df["date_parsed"] <= end)]
    df = df[df["source"] != "Source system didn't publish"].dropna(subset=["price"])

    rows = []
    for product, group in df.groupby("product"):
        group = group.sort_values(["date_parsed", "id"])
        if group.empty:
            continue
        open_price = float(group.iloc[0]["price"])
        close_price = float(group.iloc[-1]["price"])
        change = close_price - open_price
        change_pct = (change / open_price * 100) if open_price else None
        rows.append({
            "Product": product,
            "Open": round(open_price, 2),
            "Close": round(close_price, 2),
            "High": round(float(group["price"].max()), 2),
            "Low": round(float(group["price"].min()), 2),
            "Average": round(float(group["price"].mean()), 2),
            "Change": round(change, 2),
            "Change %": None if change_pct is None else round(change_pct, 2),
            "Readings": int(len(group)),
        })
    return pd.DataFrame(rows)


def developments_for_period(dev_df: pd.DataFrame, year: int, quarter: str) -> pd.DataFrame:
    """Filters logged market developments to a given quarter, most recent first."""
    if dev_df.empty:
        return pd.DataFrame()
    start, end = quarter_date_range(year, quarter)
    df = prepare_time_series(dev_df, "dev_date")
    df = df[(df["date_parsed"] >= start) & (df["date_parsed"] <= end)]
    return df.sort_values("date_parsed", ascending=False)


def weekly_benchmark_change(crude_df: pd.DataFrame) -> pd.DataFrame:
    """Rolling 7-day change snapshot per benchmark, used for the weekly
    crude price fluctuation summary in the Benchmark Tracking tab."""
    if crude_df.empty:
        return pd.DataFrame(columns=["Benchmark", "Price 7d Ago", "Latest Price", "Weekly Change", "Weekly Change %"])

    df = prepare_time_series(crude_df, "price_date")
    df = df[df["source"] != "Source system didn't publish"].dropna(subset=["price"])
    cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=7)

    rows = []
    for benchmark, group in df.groupby("benchmark"):
        group = group.sort_values("date_parsed")
        if group.empty:
            continue
        latest_price = float(group.iloc[-1]["price"])
        older = group[group["date_parsed"] <= cutoff]
        base_price = float(older.iloc[-1]["price"]) if not older.empty else float(group.iloc[0]["price"])
        change = latest_price - base_price
        change_pct = (change / base_price * 100) if base_price else None
        rows.append({
            "Benchmark": benchmark,
            "Price 7d Ago": round(base_price, 2),
            "Latest Price": round(latest_price, 2),
            "Weekly Change": round(change, 2),
            "Weekly Change %": None if change_pct is None else round(change_pct, 2),
        })
    return pd.DataFrame(rows)