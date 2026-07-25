# collectors.py
from datetime import date, datetime
import logging
import re
import requests
from bs4 import BeautifulSoup

from config import (
    SOURCES,
    YAHOO_BENCHMARKS,
    PRODUCT_PROXY_MAP,
    PRODUCT_SOURCE_ORDER,
    DUBAI_SOURCE_ORDER,
    DUBAI_KEYWORDS,
    DEVELOPMENT_CATEGORIES,
    IMPACT_KEYWORDS,
)
from database import (
    insert_crude_price,
    insert_news,
    insert_product_price,
    insert_product_attempt,
    upsert_product_source_note,
    insert_development,
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def safe_get(url, timeout=25):
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response

def initialize_product_source_notes():
    for product, meta in PRODUCT_PROXY_MAP.items():
        upsert_product_source_note(
            product=product,
            market=meta["market"],
            proxy_type=meta["proxy_type"],
            benchmark_basis=meta["benchmark_basis"],
            notes=meta["notes"],
        )

def collect_yahoo_crude_benchmark(benchmark, symbol):
    # Multi-ticker fallback logic for volatile contracts like Oman
    symbols_to_try = [symbol]
    if benchmark == "Oman":
        symbols_to_try.extend(["QM=F", "O6=F", "O9=F"])

    for active_symbol in symbols_to_try:
        try:
            url = SOURCES["yahoo_chart"].format(symbol=active_symbol)
            res = safe_get(url).json()
            result = res.get("chart", {}).get("result", [])
            if result and "meta" in result[0]:
                price = result[0]["meta"].get("regularMarketPrice")
                if price is not None and float(price) > 10.0:
                    insert_crude_price(
                        price_date=str(date.today()),
                        benchmark=benchmark,
                        price=float(round(price, 2)),
                        unit="USD/bbl",
                        source=f"Yahoo Finance ({active_symbol})"
                    )
                    return {"status": "success", "benchmark": benchmark, "symbol": active_symbol}
        except Exception:
            continue

    # Fallback state if all tickers fail
    insert_crude_price(
        price_date=str(date.today()),
        benchmark=benchmark,
        price=None,
        unit="USD/bbl",
        source="Source system didn't publish"
    )
    return {"status": "manual_required", "benchmark": benchmark, "message": "Source system didn't publish"}

_KEC_MIN_PLAUSIBLE_PRICE = 20.0
_KEC_MAX_PLAUSIBLE_PRICE = 200.0
_KEC_WINDOW_CHARS = 250
_KEC_NUMBER_RE = re.compile(r"\d{1,4}\.\d{1,2}")


def _record_kec_failure(reason):
    logging.warning("KEC price collection failed: %s", reason)
    insert_crude_price(
        str(date.today()), "Kuwait Export Crude", None, "USD/bbl",
        f"Source system didn't publish ({reason})",
    )
    return {"status": "manual_required", "benchmark": "Kuwait Export Crude", "reason": reason}


def collect_kpc_kec_price():
    """Scrapes KPC's KEC crude price, anchored to text near the 'KEC' label
    (not just the first plausible number on the page) and with a wide
    sanity band so a normal market move can't cause a silent outage.
    Every failure path records a specific, non-silent reason."""
    url = SOURCES["kpc_oil_prices"]
    try:
        html = safe_get(url).text
    except Exception as e:
        return _record_kec_failure(f"network error: {e}")

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()

    kec_idx = text.upper().find("KEC")
    if kec_idx == -1:
        return _record_kec_failure(
            "'KEC' not found in static HTML — value is likely rendered "
            "client-side (AJAX/UpdatePanel); a plain requests.get() can't see it."
        )

    window = text[kec_idx: kec_idx + _KEC_WINDOW_CHARS]
    candidates = [float(n) for n in _KEC_NUMBER_RE.findall(window)]
    plausible = [p for p in candidates if _KEC_MIN_PLAUSIBLE_PRICE <= p <= _KEC_MAX_PLAUSIBLE_PRICE]

    if not plausible:
        return _record_kec_failure(f"'KEC' found, but no plausible price nearby (candidates: {candidates})")

    price = plausible[0]
    insert_crude_price(str(date.today()), "Kuwait Export Crude", price, "USD/bbl", "KPC Official")
    return {"status": "success", "benchmark": "Kuwait Export Crude"}

def collect_dubai_price():
    """Tracks the Dubai crude benchmark via public scrape sources, falling
    back to 'Source system didn't publish' (surfaced for manual entry) when
    no source confirms a plausible price — mirroring the KPC/KEC pattern."""
    today_str = str(date.today())

    for src_key in DUBAI_SOURCE_ORDER:
        try:
            url = SOURCES[src_key]
            html = safe_get(url).text
            soup = BeautifulSoup(html, "html.parser")

            for row in soup.find_all(["tr", "div", "p"]):
                row_text = row.get_text(" ", strip=True).lower()
                if any(kw in row_text for kw in DUBAI_KEYWORDS):
                    vals = re.findall(r"\b([3-9]\d\.\d{1,2}|1[0-2]\d\.\d{1,2})\b", row_text)
                    if vals:
                        price = float(vals[0])
                        insert_crude_price(today_str, "Dubai", price, "USD/bbl", f"Scraped ({src_key})")
                        return {"status": "success", "benchmark": "Dubai", "source": src_key}
        except Exception:
            continue

    insert_crude_price(today_str, "Dubai", None, "USD/bbl", "Source system didn't publish")
    return {"status": "manual_required", "benchmark": "Dubai", "message": "Source system didn't publish"}


def _classify_impact(headline: str) -> str:
    text = headline.lower()
    for keyword in IMPACT_KEYWORDS.get("High", []):
        if keyword in text:
            return "High"
    for keyword in IMPACT_KEYWORDS.get("Medium", []):
        if keyword in text:
            return "Medium"
    return "Low"


def _classify_category(headline: str) -> str:
    text = headline.lower()
    for category, meta in DEVELOPMENT_CATEGORIES.items():
        if any(kw in text for kw in meta["keywords"]):
            return category
    return "Industry"


def collect_market_developments(limit_per_source=8):
    """Monitors OPEC+, IEA, EIA, and geopolitical/economic/industry news to
    support the Market Intelligence Monitoring KPI. Every headline is
    auto-tagged with a category and a keyword-based impact estimate; a
    human analyst can re-tag anything from the Market Intelligence tab.
    Feeds that fail to parse (site structure changes, network issues, etc.)
    are skipped silently so one broken source never blocks the others —
    manual logging in the UI always remains available as a fallback."""
    today_str = str(date.today())
    logged = 0

    checked_sources = {meta["source_key"] for meta in DEVELOPMENT_CATEGORIES.values()}

    for src_key in checked_sources:
        try:
            url = SOURCES.get(src_key)
            if not url:
                continue
            html = safe_get(url).text

            # RSS/XML feeds (EIA) vs HTML pages need different parsers.
            parser = "xml" if url.endswith(".xml") else "html.parser"
            soup = BeautifulSoup(html, parser)

            count = 0
            candidates = soup.find_all("item") if parser == "xml" else soup.find_all("a", href=True)

            for node in candidates:
                if parser == "xml":
                    title_tag = node.find("title")
                    link_tag = node.find("link")
                    title = title_tag.get_text(strip=True) if title_tag else ""
                    href = link_tag.get_text(strip=True) if link_tag else url
                else:
                    title = node.get_text(" ", strip=True)
                    href = node["href"]
                    if href.startswith("/"):
                        href = re.sub(r"(https?://[^/]+).*", r"\1", url) + href

                if len(title) < 35 or "click here" in title.lower():
                    continue

                category = _classify_category(title)
                impact = _classify_impact(title)
                insert_development(
                    dev_date=today_str,
                    category=category,
                    headline=title,
                    summary="",
                    source=src_key,
                    url=href,
                    impact=impact,
                    entered_by="Auto-Monitor",
                )
                count += 1
                logged += 1
                if count >= limit_per_source:
                    break
        except Exception:
            # Fail soft: one unreachable/blocked source should not stop
            # the rest of the monitoring sweep from completing.
            continue

    return {"status": "success" if logged else "manual_required", "developments_logged": logged}


def collect_singapore_products():
    today_str = str(date.today())
    results = []

    for product, meta in PRODUCT_PROXY_MAP.items():
        acquired = False
        
        for src_key in PRODUCT_SOURCE_ORDER:
            try:
                url = SOURCES[src_key]
                html = safe_get(url).text
                soup = BeautifulSoup(html, "html.parser")

                # Strategy A: Scan specific table layouts for target keyword matches
                for row in soup.find_all(["tr", "div", "p"]):
                    row_text = row.get_text(" ", strip=True).lower()
                    if any(kw.lower() in row_text for kw in meta["keywords"]):
                        # Identify commodity values, avoiding small structural layout metrics (e.g., sizing numbers < 10)
                        vals = re.findall(r"\b([3-9]\d\.\d{1,2}|[1-9]\d{2,3}(?:\.\d{1,2})?)\b", row_text)
                        if vals:
                            price = float(vals[0])
                            insert_product_price(
                                price_date=today_str,
                                market=meta["market"],
                                product=product,
                                price=price,
                                unit="USD/bbl",
                                source=f"Scraped ({src_key})",
                                status="collected",
                                notes=meta["notes"],
                                proxy_type=meta["proxy_type"],
                                benchmark_basis=meta["benchmark_basis"]
                            )
                            insert_product_attempt(today_str, meta["market"], product, src_key, "success", f"Extracted price: {price}")
                            acquired = True
                            break
                if acquired:
                    break

            except Exception as e:
                insert_product_attempt(today_str, meta["market"], product, src_key, "error", str(e))

        if not acquired:
            # Clean audit line execution whenever public scrapers fall back
            insert_product_price(
                price_date=today_str,
                market=meta["market"],
                product=product,
                price=None,
                unit="USD/bbl",
                source="Source system didn't publish",
                status="manual_required",
                notes=meta["notes"],
                proxy_type=meta["proxy_type"],
                benchmark_basis=meta["benchmark_basis"]
            )
            results.append({"status": "manual_required", "product": product})
        else:
            results.append({"status": "success", "product": product})

    return results

def collect_market_news(limit=10):
    try:
        url = SOURCES["oilprice_news"]
        html = safe_get(url).text
        soup = BeautifulSoup(html, "html.parser")
        count = 0
        for a in soup.find_all("a", href=True):
            title = a.get_text(" ", strip=True)
            url_href = a["href"]
            if len(title) > 35 and "oilprice.com" in url_href and "click here" not in title.lower():
                if url_href.startswith("/"):
                    url_href = "https://oilprice.com" + url_href
                insert_news(str(date.today()), "OilPrice", title, url_href)
                count += 1
                if count >= limit:
                    break
    except Exception:
        pass

def run_all_collectors():
    initialize_product_source_notes()
    results = []
    
    # Run crudes
    results.append(collect_kpc_kec_price())
    for bm, sym in YAHOO_BENCHMARKS.items():
        results.append(collect_yahoo_crude_benchmark(bm, sym))
    results.append(collect_dubai_price())

    # Run refined products
    results.extend(collect_singapore_products())

    # Run market intelligence monitoring (OPEC+/IEA/EIA/geopolitical/economic/industry)
    results.append(collect_market_developments())
    collect_market_news()
    return results