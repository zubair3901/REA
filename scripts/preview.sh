#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v python3 >/dev/null || { echo 'Install Python 3.12 or newer first.'; exit 1; }
command -v npm >/dev/null || { echo 'Install Node.js 22 or newer first.'; exit 1; }
if [ ! -x .venv-preview/bin/python ]; then
  python3 -m venv .venv-preview
fi
.venv-preview/bin/python -m pip install -r backend/requirements.txt
# Neural matting is optional: ONNX wheels are not available for every Mac/Python.
if [ "${ROOM_PREVIEW_VISION:-false}" = true ]; then
  .venv-preview/bin/python -m pip install -r backend/requirements-vision.txt
else
  echo 'Preview mode: automatic background removal is disabled; use transparent PNG product photos.'
fi
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
if [ "${ROOM_PREVIEW_VISION:-false}" = true ]; then
  .venv-preview/bin/python -m app.prepare_vision
fi
echo 'Open http://localhost:8080 in your browser. Stop with Ctrl+C.'
echo 'Temporary test mode: payments and AI disabled; email verification not required.'
exec .venv-preview/bin/python -m uvicorn app.preview:app --host 0.0.0.0 --port 8080
