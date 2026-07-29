from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth import get_current_admin
from app.models import Item, Source, ScrapeLog, ScrapeSetting
from app.schemas import (
    ItemOut, ItemCreate, SourceOut, SourceCreate, SourceUpdate,
    ScrapeLogOut, ScrapeSettingOut, ScrapeSettingUpdate,
    AICredentialsOut, AICredentialsUpdate,
)
from app.scraper.runner import run_full_scrape, scrape_item
from app.scraper import scheduler as scrape_scheduler
from app.services import get_item_by_code_or_404, get_ai_credentials_row

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])


# --- Items ---

@router.get("/items", response_model=List[ItemOut])
def list_items(db: Session = Depends(get_db)):
    return db.query(Item).order_by(Item.category, Item.name).all()


@router.post("/items", response_model=ItemOut)
def create_item(body: ItemCreate, db: Session = Depends(get_db)):
    if db.query(Item).filter(Item.code == body.code.upper()).first():
        raise HTTPException(status_code=409, detail="Item code already exists")
    item = Item(**{**body.model_dump(), "code": body.code.upper()})
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/items/{item_id}")
def deactivate_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.active = False
    db.commit()
    return {"ok": True}


# --- Sources ---

@router.post("/sources", response_model=SourceOut)
def create_source(body: SourceCreate, db: Session = Depends(get_db)):
    if not db.get(Item, body.item_id):
        raise HTTPException(status_code=404, detail="Item not found")
    source = Source(**body.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.patch("/sources/{source_id}", response_model=SourceOut)
def update_source(source_id: int, body: SourceUpdate, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(source, key, value)
    db.commit()
    db.refresh(source)
    return source


@router.delete("/sources/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()
    return {"ok": True}


# --- Scrape control ---

@router.post("/scrape/run")
def run_now(db: Session = Depends(get_db)):
    results = run_full_scrape(db)
    return {"results": results}


@router.post("/scrape/run/{code}")
def run_now_single(code: str, db: Session = Depends(get_db)):
    item = get_item_by_code_or_404(db, code)
    ok = scrape_item(db, item)
    return {"code": item.code, "success": ok}


@router.get("/scrape/settings", response_model=ScrapeSettingOut)
def get_settings(db: Session = Depends(get_db)):
    setting = db.query(ScrapeSetting).first()
    return ScrapeSettingOut(frequency_minutes=setting.frequency_minutes if setting else 30)


@router.put("/scrape/settings", response_model=ScrapeSettingOut)
def update_settings(body: ScrapeSettingUpdate, db: Session = Depends(get_db)):
    if body.frequency_minutes < 1:
        raise HTTPException(status_code=422, detail="frequency_minutes must be >= 1")
    setting = db.query(ScrapeSetting).first()
    if not setting:
        setting = ScrapeSetting()
        db.add(setting)
    setting.frequency_minutes = body.frequency_minutes
    db.commit()
    scrape_scheduler.reschedule(body.frequency_minutes)
    return ScrapeSettingOut(frequency_minutes=body.frequency_minutes)


# --- Logs ---

@router.get("/logs", response_model=List[ScrapeLogOut])
def list_logs(limit: int = 200, db: Session = Depends(get_db)):
    return (
        db.query(ScrapeLog)
        .order_by(ScrapeLog.run_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/logs/plain", response_class=PlainTextResponse)
def list_logs_plain(limit: int = 500, db: Session = Depends(get_db)):
    rows = (
        db.query(ScrapeLog)
        .order_by(ScrapeLog.run_at.desc())
        .limit(limit)
        .all()
    )
    lines = []
    for r in rows:
        ts = r.run_at.strftime("%Y-%m-%d %H:%M:%S")
        item = r.item_code or "-"
        source = r.source_name or "-"
        lines.append(f"[{ts}] {r.status.upper():7s} item={item:12s} source={source:20s} {r.message or ''}")
    return "\n".join(lines) if lines else "No scrape runs logged yet."


# --- AI credentials ---

@router.get("/ai-credentials", response_model=AICredentialsOut)
def get_ai_credentials(db: Session = Depends(get_db)):
    row = get_ai_credentials_row(db)
    return AICredentialsOut(
        deepseek_configured=bool(row.deepseek_api_key),
        claude_configured=bool(row.claude_api_key),
    )


@router.put("/ai-credentials", response_model=AICredentialsOut)
def update_ai_credentials(body: AICredentialsUpdate, db: Session = Depends(get_db)):
    row = get_ai_credentials_row(db)
    # Empty string clears the key; omitted (None) leaves it untouched.
    if body.deepseek_api_key is not None:
        row.deepseek_api_key = body.deepseek_api_key.strip() or None
    if body.claude_api_key is not None:
        row.claude_api_key = body.claude_api_key.strip() or None
    db.commit()
    db.refresh(row)
    return AICredentialsOut(
        deepseek_configured=bool(row.deepseek_api_key),
        claude_configured=bool(row.claude_api_key),
    )
