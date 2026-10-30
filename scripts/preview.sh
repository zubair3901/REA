#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v python3 >/dev/null || { echo 'Install Python 3.12 or newer first.'; exit 1; }
command -v npm >/dev/null || { echo 'Install Node.js 22 or newer first.'; exit 1; }
if [ ! -x .venv-preview/bin/python ]; then
  python3 -m venv .venv-preview
fi
.venv-preview/bin/python -m pip install -r backend/requirements.txt -r backend/requirements-vision.txt
npm --prefix frontend ci
npm --prefix frontend run build
export PYTHONPATH=backend
export DATA_DIR="$PWD/backend/preview-data"
export DATABASE_URL="sqlite:///$DATA_DIR/marketplace.db"
export COOKIE_SECURE=false
export ENABLE_PROJECT_SALES=false
export ENABLE_AI_GENERATION=false
export ALLOW_DEMO_CATALOG=false
export ALLOW_LEGACY_PHOTOS=false
export REQUIRE_VERIFIED_EMAIL=false
export CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
.venv-preview/bin/python -m app.migrate
.venv-preview/bin/python -m app.prepare_vision
echo 'Open http://localhost:8080 in your browser. Stop with Ctrl+C.'
echo 'Temporary test mode: payments and AI disabled; email verification not required.'
exec .venv-preview/bin/python -m uvicorn app.preview:app --host 0.0.0.0 --port 8080
