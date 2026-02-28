#!/usr/bin/env sh
set -eu

exec uvicorn app.api.main:app --host 127.0.0.1 --port 8000
