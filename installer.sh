#!/usr/bin/env bash
set -euo pipefail

DB_HOST="localhost"
DB_PORT="3306"
DB_NAME="knpc"
DB_USER="app_user"
DB_PASSWORD="Chenani#44"
BACKEND_PORT="8000"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

fail() { echo "FAILED: $1" >&2; exit 1; }

for bin in mysql python3 npm pm2; do
  command -v "$bin" >/dev/null || fail "$bin not installed"
done

echo "==> [1/6] Verifying existing DB/user (no creation — assumed already set up)"
mysql -u "$DB_USER" -p"$DB_PASSWORD" -h "$DB_HOST" "$DB_NAME" -e "SELECT 1;" \
  || fail "cannot connect as $DB_USER to $DB_NAME — check credentials/grants"

echo "==> [2/6] Writing backend/.env"
SESSION_SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
cat > "$BACKEND_DIR/.env" <<ENV
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
SESSION_SECRET=${SESSION_SECRET}
SCRAPE_FREQUENCY_MINUTES=30
DEEPSEEK_API_KEY=
CLAUDE_API_KEY=
ENV

echo "==> [3/6] Confirming config.py actually loads .env (dotenv fix present)"
grep -q "load_dotenv" "$BACKEND_DIR/app/config.py" \
  || fail "backend/app/config.py has no load_dotenv() - pull the fixed branch first"

echo "==> [4/6] Python venv + deps"
cd "$BACKEND_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
python -c "import dotenv" || fail "python-dotenv not installed"
deactivate

echo "==> [5/6] Frontend build (served by FastAPI as static)"
cd "$FRONTEND_DIR"
npm install --silent
npm run build
[ -d "$FRONTEND_DIR/dist" ] || fail "frontend build did not produce dist/"

echo "==> [6/6] Starting pm2"
cd "$ROOT_DIR"
pm2 delete knpc-backend >/dev/null 2>&1 || true
pm2 start "$BACKEND_DIR/venv/bin/uvicorn" \
  --name knpc-backend \
  --cwd "$BACKEND_DIR" \
  --interpreter none \
  -- app.main:app --host 0.0.0.0 --port "$BACKEND_PORT"
pm2 save

sleep 2
echo "==> Health check"
curl -sf "http://127.0.0.1:${BACKEND_PORT}/api/health" \
  && echo -e "\nOK - serving on :${BACKEND_PORT}" \
  || fail "backend not responding - run: pm2 logs knpc-backend"

pm2 status
