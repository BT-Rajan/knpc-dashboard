# KNPC Market Intelligence — monolith (Python/FastAPI + MySQL + React)

## Setup

```
mysql -u root -p < backend/schema.sql
cp backend/.env.example backend/.env   # fill in DB_PASSWORD, DEEPSEEK_API_KEY, CLAUDE_API_KEY
```

## Dev

```
cd backend && pip install -r requirements.txt && python run.py     # :8000
cd frontend && npm install && npm run dev                          # :5173, proxies /api -> :8000
```

## Prod (single process serves API + built UI)

```
cd frontend && npm install && npm run build
cd backend && pip install -r requirements.txt && python run.py     # :8000
```

Login: `admin` / `Yellow#G0#` (full access) or `user` / `Blue#M1nt` (dashboard only) — set in `backend/app/config.py`.

Sources (what to scrape, and how) are configured per item from the Admin tab, not in code.
