import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db import Base, engine
from app.seed import seed
from app.scraper import scheduler as scrape_scheduler
from app.routers import auth, dashboard, admin, export, ai

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="KNPC Market Intelligence Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # single-tenant internal tool, served monolith in prod
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(export.router)
app.include_router(ai.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    seed()
    scrape_scheduler.start()


@app.get("/api/health")
def health():
    return {"status": "ok"}


# --- Serve the built React app (monolith deployment) ---
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
