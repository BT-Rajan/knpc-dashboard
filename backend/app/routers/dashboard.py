from collections import defaultdict
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import get_current_user
from app.models import Item
from app.schemas import NavCategory, NavItem, TickerEntry, ItemDetail, NewsOut
from app.services import get_item_by_code_or_404, price_series, trend_fields, recent_news

router = APIRouter(prefix="/api", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/nav", response_model=List[NavCategory])
def get_nav(db: Session = Depends(get_db)):
    items = db.query(Item).filter(Item.active == True).order_by(Item.category, Item.name).all()  # noqa: E712
    grouped = defaultdict(list)
    for item in items:
        grouped[item.category].append(NavItem(code=item.code, name=item.name))
    return [NavCategory(category=cat, items=items_) for cat, items_ in grouped.items()]


@router.get("/ticker", response_model=List[TickerEntry])
def get_ticker(db: Session = Depends(get_db)):
    items = db.query(Item).filter(Item.active == True).order_by(Item.category, Item.name).all()  # noqa: E712
    out = []
    for item in items:
        fields = trend_fields(db, item.id)
        out.append(TickerEntry(code=item.code, name=item.name, category=item.category, unit=item.unit, **fields))
    return out


@router.get("/items/{code}", response_model=ItemDetail)
def get_item_detail(code: str, db: Session = Depends(get_db)):
    item = get_item_by_code_or_404(db, code)
    fields = trend_fields(db, item.id)
    weekly = price_series(db, item.id, days=7)
    monthly = price_series(db, item.id, days=30)
    news = [NewsOut.model_validate(n) for n in recent_news(db, item.id)]
    return ItemDetail(
        code=item.code, name=item.name, category=item.category, unit=item.unit,
        weekly_series=weekly, monthly_series=monthly, news=news, **fields,
    )
