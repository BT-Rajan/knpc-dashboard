from datetime import date, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Item, PriceHistory, NewsItem, AICredentials
from app.config import DEEPSEEK_API_KEY, CLAUDE_API_KEY


def get_item_by_code_or_404(db: Session, code: str) -> Item:
    item = db.query(Item).filter(Item.code == code.upper()).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Unknown item code '{code}'")
    return item


def price_series(db: Session, item_id: int, days: int):
    since = date.today() - timedelta(days=days)
    rows = (
        db.query(PriceHistory)
        .filter(PriceHistory.item_id == item_id, PriceHistory.price_date >= since)
        .order_by(PriceHistory.price_date.asc())
        .all()
    )
    return [{"price_date": r.price_date, "price": r.price} for r in rows]


def latest_two_prices(db: Session, item_id: int):
    rows = (
        db.query(PriceHistory)
        .filter(PriceHistory.item_id == item_id)
        .order_by(PriceHistory.price_date.desc())
        .limit(2)
        .all()
    )
    current = rows[0] if len(rows) > 0 else None
    previous = rows[1] if len(rows) > 1 else None
    return current, previous


def trend_fields(db: Session, item_id: int):
    current, previous = latest_two_prices(db, item_id)
    if not current:
        return dict(current_price=None, previous_price=None, daily_change=None,
                    daily_change_pct=None, as_of=None)
    prev_price = previous.price if previous else None
    change = (current.price - prev_price) if prev_price is not None else None
    change_pct = (change / prev_price * 100) if change is not None and prev_price else None
    return dict(
        current_price=current.price,
        previous_price=prev_price,
        daily_change=round(change, 4) if change is not None else None,
        daily_change_pct=round(change_pct, 3) if change_pct is not None else None,
        as_of=current.price_date,
    )


def recent_news(db: Session, item_id: int, limit: int = 10):
    return (
        db.query(NewsItem)
        .filter(NewsItem.item_id == item_id)
        .order_by(NewsItem.collected_at.desc())
        .limit(limit)
        .all()
    )


def get_ai_credentials_row(db: Session) -> AICredentials:
    row = db.query(AICredentials).first()
    if not row:
        row = AICredentials()
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def resolve_ai_key(db: Session, provider: str) -> str:
    """DB-entered key wins; falls back to the env-var default from config.py."""
    row = get_ai_credentials_row(db)
    if provider == "deepseek":
        return row.deepseek_api_key or DEEPSEEK_API_KEY
    if provider == "claude":
        return row.claude_api_key or CLAUDE_API_KEY
    return ""
