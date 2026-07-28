import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.db import SessionLocal
from app.models import ScrapeSetting
from app.scraper.runner import run_full_scrape
from app.config import DEFAULT_SCRAPE_FREQUENCY_MINUTES

logger = logging.getLogger("knpc.scheduler")

_scheduler = BackgroundScheduler()
_JOB_ID = "scrape_all"


def _job():
    db = SessionLocal()
    try:
        run_full_scrape(db)
    finally:
        db.close()


def _current_frequency_minutes() -> int:
    db = SessionLocal()
    try:
        setting = db.query(ScrapeSetting).first()
        return setting.frequency_minutes if setting else DEFAULT_SCRAPE_FREQUENCY_MINUTES
    finally:
        db.close()


def start():
    if _scheduler.running:
        return
    minutes = _current_frequency_minutes()
    _scheduler.add_job(
        _job, IntervalTrigger(minutes=minutes), id=_JOB_ID,
        replace_existing=True, next_run_time=None,
    )
    _scheduler.start()
    logger.info("Scheduler started, interval=%s minutes", minutes)


def reschedule(minutes: int):
    """Called by the admin panel when the scrape frequency is changed."""
    if _scheduler.get_job(_JOB_ID):
        _scheduler.reschedule_job(_JOB_ID, trigger=IntervalTrigger(minutes=minutes))
    else:
        _scheduler.add_job(_job, IntervalTrigger(minutes=minutes), id=_JOB_ID, replace_existing=True)
    logger.info("Scheduler rescheduled, interval=%s minutes", minutes)


def trigger_now():
    """Manual 'scrape now' from the admin panel — runs in the caller's thread."""
    _job()
