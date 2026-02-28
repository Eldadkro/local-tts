#!/usr/bin/env bash
set -euo pipefail

API_HOST="${LOCAL_TTS_API_HOST:-127.0.0.1}"
API_PORT="${LOCAL_TTS_API_PORT:-8000}"
API_RELOAD="${LOCAL_TTS_API_RELOAD:-1}"

if [[ "$API_RELOAD" == "1" ]]; then
  exec uvicorn app.api.main:app --host "$API_HOST" --port "$API_PORT" --reload
fi

exec uvicorn app.api.main:app --host "$API_HOST" --port "$API_PORT"
