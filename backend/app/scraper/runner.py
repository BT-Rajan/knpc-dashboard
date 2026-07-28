from datetime import datetime, date
import logging

from sqlalchemy.orm import Session

from app.models import Item, Source, PriceHistory, NewsItem, ScrapeLog
from app.scraper.base import fetch, extract_value, extract_news, ScrapeError

logger = logging.getLogger("knpc.scraper")


def _log(db: Session, item_code, source_name, status, message):
    db.add(ScrapeLog(item_code=item_code, source_name=source_name, status=status, message=message))
    logger.info("[%s] %s / %s: %s", status.upper(), item_code, source_name, message)


def scrape_item(db: Session, item: Item) -> bool:
    """Try each active source for this item, in priority order, until one
    succeeds. Returns True on success, False if every source failed
    (failure is logged either way)."""
    sources = sorted(
        [s for s in item.sources if s.active],
        key=lambda s: s.priority,
    )
    if not sources:
        _log(db, item.code, None, "error", "No active sources configured")
        return False

    last_error = None
    for source in sources:
        try:
            resp = fetch(source.url)
            price = extract_value(source, resp)

            today = date.today()
            existing = (
                db.query(PriceHistory)
                .filter(PriceHistory.item_id == item.id, PriceHistory.price_date == today)
                .first()
            )
            if existing:
                existing.price = price
                existing.source_id = source.id
                existing.collected_at = datetime.utcnow()
            else:
                db.add(PriceHistory(
                    item_id=item.id, source_id=source.id,
                    price_date=today, price=price,
                ))

            for headline in extract_news(source, resp):
                dup = (
                    db.query(NewsItem)
                    .filter(NewsItem.item_id == item.id, NewsItem.headline == headline["headline"])
                    .first()
                )
                if not dup:
                    db.add(NewsItem(
                        item_id=item.id, headline=headline["headline"],
                        url=headline["url"], source=source.name,
                    ))

            _log(db, item.code, source.name, "success", f"price={price}")
            db.commit()
            return True

        except Exception as exc:  # noqa: BLE001 - we want to log & fall through
            last_error = str(exc)
            db.rollback()
            _log(db, item.code, source.name, "error", last_error)
            db.commit()
            continue

    _log(db, item.code, None, "error", f"All sources failed. Last error: {last_error}")
    db.commit()
    return False


def run_full_scrape(db: Session):
    items = db.query(Item).filter(Item.active == True).all()  # noqa: E712
    results = {}
    for item in items:
        results[item.code] = scrape_item(db, item)
    return results
