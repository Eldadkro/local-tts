#!/usr/bin/env bash
set -euo pipefail

UI_HOST="${LOCAL_TTS_UI_HOST:-0.0.0.0}"
UI_PORT="${LOCAL_TTS_UI_PORT:-8501}"
API_HOST="${LOCAL_TTS_API_HOST:-127.0.0.1}"
API_PORT="${LOCAL_TTS_API_PORT:-8000}"

export LOCAL_TTS_API_BASE_URL="${LOCAL_TTS_API_BASE_URL:-http://${API_HOST}:${API_PORT}}"

exec streamlit run app/ui/streamlit_app.py --server.port "$UI_PORT" --server.address "$UI_HOST"
