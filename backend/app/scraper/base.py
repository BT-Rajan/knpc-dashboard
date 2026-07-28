import json
import re
import requests
from bs4 import BeautifulSoup

from app.config import SCRAPE_REQUEST_TIMEOUT, SCRAPE_USER_AGENT

NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*")


class ScrapeError(Exception):
    pass


def _to_float(text: str) -> float:
    match = NUMBER_RE.search(text.replace(",", ""))
    if not match:
        raise ScrapeError(f"No numeric value found in '{text[:80]}'")
    return float(match.group())


def fetch(url: str) -> requests.Response:
    headers = {"User-Agent": SCRAPE_USER_AGENT}
    resp = requests.get(url, headers=headers, timeout=SCRAPE_REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp


def extract_value(source, resp: requests.Response) -> float:
    """Extract a single numeric price given a Source row's type + selector."""
    if source.source_type == "css":
        soup = BeautifulSoup(resp.text, "html.parser")
        el = soup.select_one(source.value_selector)
        if not el:
            raise ScrapeError(f"CSS selector '{source.value_selector}' matched nothing")
        return _to_float(el.get_text())

    if source.source_type == "json_path":
        data = resp.json()
        node = data
        for part in source.value_selector.split("."):
            if part.isdigit():
                node = node[int(part)]
            else:
                node = node[part]
        return float(node)

    if source.source_type == "regex":
        match = re.search(source.value_selector, resp.text)
        if not match:
            raise ScrapeError(f"Regex '{source.value_selector}' did not match")
        return _to_float(match.group(1) if match.groups() else match.group())

    raise ScrapeError(f"Unknown source_type '{source.source_type}'")


def extract_news(source, resp: requests.Response, limit: int = 5):
    """Optional: pull headline+link pairs off the same page using news_selector
    (a CSS selector pointing at anchor tags)."""
    if not source.news_selector:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    out = []
    for a in soup.select(source.news_selector)[:limit]:
        headline = a.get_text(strip=True)
        href = a.get("href", "")
        if headline:
            out.append({"headline": headline, "url": href})
    return out
