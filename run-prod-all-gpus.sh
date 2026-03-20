#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

IMAGE_NAME="${IMAGE_NAME:-local-tts:prod}"
CONTAINER_NAME="${CONTAINER_NAME:-local-tts-prod}"
MODEL_DIR="${MODEL_DIR:-${PROJECT_ROOT}/model}"

mkdir -p "$MODEL_DIR"

if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
  docker build --target prod -t "$IMAGE_NAME" "$PROJECT_ROOT"
fi

if docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
  docker rm -f "$CONTAINER_NAME" >/dev/null
fi

docker run -d --rm \
  --name "$CONTAINER_NAME" \
  --gpus all \
  -p 8000:8000 \
  -p 8501:8501 \
  -e TTS_DEVICE_MODE="${TTS_DEVICE_MODE:-gpu}" \
  -e HF_HOME="/app/model" \
  -v "${MODEL_DIR}:/app/model" \
  "$IMAGE_NAME" >/dev/null

echo "Started $CONTAINER_NAME from $IMAGE_NAME with --gpus all"
echo "UI:  http://localhost:8501"
echo "API: http://localhost:8000"
