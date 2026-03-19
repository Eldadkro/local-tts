#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKERFILE="${DOCKERFILE:-${PROJECT_ROOT}/Dockerfile}"

PROD_IMAGE="${PROD_IMAGE:-local-tts:prod}"
DEV_IMAGE="${DEV_IMAGE:-local-tts:dev}"
PROD_CONTAINER="${PROD_CONTAINER:-local-tts-prod}"
DEV_CONTAINER="${DEV_CONTAINER:-local-tts-dev}"
MODEL_DIR="${MODEL_DIR:-${PROJECT_ROOT}/model}"

mkdir -p "$MODEL_DIR"

if [[ ! -f "$DOCKERFILE" ]]; then
  echo "Dockerfile not found at: $DOCKERFILE" >&2
  exit 1
fi

has_target() {
  local target="$1"
  grep -Eq "^[[:space:]]*FROM[[:space:]].*[[:space:]]AS[[:space:]]+${target}[[:space:]]*$" "$DOCKERFILE"
}

build_image() {
  local target="$1"
  local image="$2"

  if has_target "$target"; then
    docker build --target "$target" -t "$image" "$PROJECT_ROOT"
  else
    docker build -t "$image" "$PROJECT_ROOT"
  fi
}

if docker container inspect "$PROD_CONTAINER" >/dev/null 2>&1; then
  docker rm "$PROD_CONTAINER" >/dev/null
fi

if docker container inspect "$DEV_CONTAINER" >/dev/null 2>&1; then
  docker rm "$DEV_CONTAINER" >/dev/null
fi

build_image "prod" "$PROD_IMAGE"
build_image "dev" "$DEV_IMAGE"

docker create \
  --name "$PROD_CONTAINER" \
  -p 8000:8000 \
  -p 8501:8501 \
  -e TTS_DEVICE_MODE="${TTS_DEVICE_MODE:-gpu}" \
  -e HF_HOME="/app/model" \
  -v "${MODEL_DIR}:/app/model" \
  "$PROD_IMAGE" >/dev/null

docker create \
  --name "$DEV_CONTAINER" \
  -e TTS_DEVICE_MODE="${TTS_DEVICE_MODE:-gpu}" \
  -e HF_HOME="/app/model" \
  -v "${MODEL_DIR}:/app/model" \
  "$DEV_IMAGE" \
  sleep infinity >/dev/null

echo "Created containers: $PROD_CONTAINER, $DEV_CONTAINER"
echo "Start them with: docker start $PROD_CONTAINER $DEV_CONTAINER"
