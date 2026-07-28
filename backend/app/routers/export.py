import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import get_current_admin
from app.models import Item, Source, PriceHistory, NewsItem, ScrapeLog, ScrapeSetting

router = APIRouter(prefix="/api/admin/export", tags=["export"], dependencies=[Depends(get_current_admin)])

TABLES = {
    "items": Item,
    "sources": Source,
    "price_history": PriceHistory,
    "news_items": NewsItem,
    "scrape_log": ScrapeLog,
    "scrape_settings": ScrapeSetting,
}


@router.get("/tables")
def list_tables():
    """Which raw tables can be exported."""
    return {"tables": list(TABLES.keys())}


@router.get("/tables/{table_name}.csv")
def export_table_csv(table_name: str, db: Session = Depends(get_db)):
    model = TABLES.get(table_name)
    if not model:
        raise HTTPException(status_code=404, detail=f"Unknown table '{table_name}'")

    columns = [c.key for c in inspect(model).columns]
    rows = db.query(model).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(columns)
    for row in rows:
        writer.writerow([getattr(row, col) for col in columns])
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={table_name}.csv"},
    )
