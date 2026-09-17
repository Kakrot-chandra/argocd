#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"
npm install
npm run build
cd "$ROOT/backend"
# shellcheck disable=SC1091
source .venv/bin/activate
export RAG_FRONTEND_DIST="$ROOT/frontend/dist"
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
