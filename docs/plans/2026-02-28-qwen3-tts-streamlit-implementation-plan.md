# Qwen3 TTS Streamlit Container Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a reliable single-container app that serves Qwen3 TTS via FastAPI and a Streamlit frontend with preset and uploaded-clone voice flows.

**Architecture:** One Docker image runs two internal processes: FastAPI for inference and Streamlit for UI. Streamlit calls API over localhost. Model artifacts are pulled from Hugging Face on first startup and cached on a mounted volume.

**Tech Stack:** Python 3.11, FastAPI, Uvicorn, Streamlit, Pydantic, PyTorch, Hugging Face Hub/Transformers, pytest, Docker, supervisord.

---

### Task 1: Bootstrap Project and Test Harness

**Files:**
- Create: `pyproject.toml`
- Create: `app/api/__init__.py`
- Create: `app/ui/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `README.md`

**Step 1: Write the failing test**

```python
# tests/test_bootstrap_imports.py
def test_api_package_imports():
    import app.api  # noqa: F401


def test_ui_package_imports():
    import app.ui  # noqa: F401
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_bootstrap_imports.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app'`.

**Step 3: Write minimal implementation**

```toml
# pyproject.toml (core excerpt)
[project]
name = "local-tts"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["fastapi", "uvicorn", "streamlit", "pydantic", "pytest"]
```

Create package init files under `app/api` and `app/ui`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_bootstrap_imports.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add pyproject.toml app tests README.md
git commit -m "chore: bootstrap python package and test harness"
```

### Task 2: Configuration and Device Selection

**Files:**
- Create: `app/api/config.py`
- Create: `app/api/device.py`
- Test: `tests/api/test_config.py`
- Test: `tests/api/test_device.py`

**Step 1: Write the failing test**

```python
from app.api.config import Settings
from app.api.device import resolve_device


def test_settings_defaults():
    s = Settings()
    assert s.tts_device_mode == "auto"


def test_resolve_device_cpu(monkeypatch):
    monkeypatch.setenv("TTS_DEVICE_MODE", "cpu")
    assert resolve_device() == "cpu"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_config.py tests/api/test_device.py -v`
Expected: FAIL with import errors for missing modules.

**Step 3: Write minimal implementation**

```python
# app/api/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    tts_device_mode: str = "auto"
    hf_model_id: str = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
```

```python
# app/api/device.py
import os


def resolve_device() -> str:
    mode = os.getenv("TTS_DEVICE_MODE", "auto").lower()
    if mode in {"cpu", "gpu", "mps"}:
        return mode
    return "auto"
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_config.py tests/api/test_device.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add app/api/config.py app/api/device.py tests/api
git commit -m "feat: add runtime settings and device mode selection"
```

### Task 3: API App Skeleton and Health Endpoint

**Files:**
- Create: `app/api/main.py`
- Create: `app/api/schemas.py`
- Test: `tests/api/test_health.py`

**Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from app.api.main import app


def test_health_endpoint():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert "status" in body
    assert "device" in body
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_health.py -v`
Expected: FAIL because `/health` or app module does not exist.

**Step 3: Write minimal implementation**

```python
# app/api/main.py
from fastapi import FastAPI
from app.api.device import resolve_device

app = FastAPI(title="Local TTS API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "device": resolve_device(), "model_loaded": False}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_health.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add app/api/main.py app/api/schemas.py tests/api/test_health.py
git commit -m "feat: add fastapi app and health endpoint"
```

### Task 4: Voice Catalog and Clone Upload Endpoint

**Files:**
- Modify: `app/api/main.py`
- Modify: `app/api/schemas.py`
- Create: `app/api/voice_store.py`
- Test: `tests/api/test_voices.py`

**Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from app.api.main import app


def test_get_voices_returns_presets():
    client = TestClient(app)
    res = client.get("/voices")
    assert res.status_code == 200
    assert "presets" in res.json()


def test_clone_endpoint_rejects_non_audio():
    client = TestClient(app)
    res = client.post(
        "/voices/clone",
        files={"reference_audio": ("sample.txt", b"hello", "text/plain")},
    )
    assert res.status_code == 400
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_voices.py -v`
Expected: FAIL because endpoints are missing.

**Step 3: Write minimal implementation**

```python
# app/api/voice_store.py
PRESET_VOICES = ["neutral_female", "neutral_male"]
CLONED_VOICES: dict[str, str] = {}
```

Add `GET /voices` and `POST /voices/clone` with file type checks (`audio/wav`, `audio/x-wav`, `audio/mpeg`).

**Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_voices.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add app/api/main.py app/api/schemas.py app/api/voice_store.py tests/api/test_voices.py
git commit -m "feat: add preset voices and clone upload validation"
```

### Task 5: Synthesis Endpoint with Service Abstraction

**Files:**
- Create: `app/api/services/model_service.py`
- Modify: `app/api/main.py`
- Modify: `app/api/schemas.py`
- Test: `tests/api/test_synthesize.py`

**Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from app.api.main import app


def test_synthesize_returns_audio_wav(monkeypatch):
    client = TestClient(app)
    payload = {"text": "hello world", "voice_mode": "preset", "voice_id": "neutral_female"}
    res = client.post("/synthesize", json=payload)
    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/wav"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_synthesize.py -v`
Expected: FAIL because endpoint/service missing.

**Step 3: Write minimal implementation**

```python
# app/api/services/model_service.py
class ModelService:
    def synthesize(self, text: str, voice_id: str) -> bytes:
        return b"RIFF....WAVE"  # placeholder bytes for initial pass
```

Wire `POST /synthesize` to call `ModelService.synthesize` and return `Response(..., media_type="audio/wav")`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_synthesize.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add app/api/services/model_service.py app/api/main.py app/api/schemas.py tests/api/test_synthesize.py
git commit -m "feat: add synthesize endpoint with model service abstraction"
```

### Task 6: Integrate Qwen3 TTS Model Loader

**Files:**
- Modify: `app/api/services/model_service.py`
- Modify: `app/api/config.py`
- Test: `tests/api/test_model_service.py`

**Step 1: Write the failing test**

```python
from app.api.services.model_service import ModelService


def test_model_service_initializes_with_model_id(monkeypatch):
    monkeypatch.setenv("HF_MODEL_ID", "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")
    svc = ModelService()
    assert svc.model_id == "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_model_service.py -v`
Expected: FAIL because constructor fields/logic missing.

**Step 3: Write minimal implementation**

```python
class ModelService:
    def __init__(self):
        self.model_id = os.getenv("HF_MODEL_ID", "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")
        self.device = resolve_device()
        # lazy load pipeline/model on first synth call
```

Add lazy model loading and cache path support (`HF_HOME`). Keep synthesis timeout and clear exception mapping.

**Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_model_service.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add app/api/services/model_service.py app/api/config.py tests/api/test_model_service.py
git commit -m "feat: integrate qwen3 model loading with env-driven config"
```

### Task 7: Build Streamlit Frontend

**Files:**
- Create: `app/ui/streamlit_app.py`
- Create: `app/ui/api_client.py`
- Test: `tests/ui/test_api_client.py`

**Step 1: Write the failing test**

```python
from app.ui.api_client import build_synthesize_payload


def test_build_payload_for_preset_voice():
    payload = build_synthesize_payload("hello", "preset", "neutral_female", None)
    assert payload["text"] == "hello"
    assert payload["voice_mode"] == "preset"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/ui/test_api_client.py -v`
Expected: FAIL because module/function missing.

**Step 3: Write minimal implementation**

```python
# app/ui/api_client.py
def build_synthesize_payload(text, voice_mode, voice_id, cloned_voice_id):
    return {
        "text": text,
        "voice_mode": voice_mode,
        "voice_id": voice_id,
        "cloned_voice_id": cloned_voice_id,
    }
```

Create Streamlit UI with:
- text area
- preset vs upload selector
- upload widget for audio
- synth button and audio playback

**Step 4: Run test to verify it passes**

Run: `pytest tests/ui/test_api_client.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add app/ui/streamlit_app.py app/ui/api_client.py tests/ui/test_api_client.py
git commit -m "feat: add streamlit ui for preset and cloned voice flows"
```

### Task 8: Single-Container Runtime and Process Supervision

**Files:**
- Create: `Dockerfile`
- Create: `docker/supervisord.conf`
- Create: `docker/start-api.sh`
- Create: `docker/start-ui.sh`
- Create: `.dockerignore`
- Modify: `README.md`
- Test: `tests/integration/test_container_smoke.py`

**Step 1: Write the failing test**

```python
def test_container_smoke_placeholder():
    # replaced by real smoke script once image builds in CI/local
    assert False, "replace with docker run smoke check"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_container_smoke.py -v`
Expected: FAIL by design.

**Step 3: Write minimal implementation**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir .
RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*
CMD ["/usr/bin/supervisord", "-c", "/app/docker/supervisord.conf"]
```

Add supervisor config with two programs:
- API: `uvicorn app.api.main:app --host 127.0.0.1 --port 8000`
- UI: `streamlit run app/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0`

Replace placeholder integration test with script-backed smoke check:
- build image
- run container with env vars
- assert `/health` is reachable through Streamlit-linked workflow

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_container_smoke.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add Dockerfile docker .dockerignore tests/integration README.md
git commit -m "feat: containerize api and streamlit in single supervised image"
```

### Task 9: Reliability Guards and Final Verification

**Files:**
- Modify: `app/api/main.py`
- Modify: `app/api/config.py`
- Modify: `app/ui/streamlit_app.py`
- Test: `tests/api/test_validation_limits.py`
- Test: `tests/integration/test_end_to_end.py`

**Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from app.api.main import app


def test_synthesize_rejects_too_long_text():
    client = TestClient(app)
    long_text = "a" * 20001
    res = client.post("/synthesize", json={"text": long_text, "voice_mode": "preset", "voice_id": "neutral_female"})
    assert res.status_code == 422
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_validation_limits.py -v`
Expected: FAIL because limits are not yet enforced.

**Step 3: Write minimal implementation**

Add request size/text-length checks, request timeout handling, and UI-side guardrails before submit.

**Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_validation_limits.py tests/integration/test_end_to_end.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add app/api/main.py app/api/config.py app/ui/streamlit_app.py tests/api/test_validation_limits.py tests/integration/test_end_to_end.py
git commit -m "fix: enforce reliability limits and finalize end-to-end verification"
```

## Final Verification Checklist

Run all checks:

```bash
pytest -v
docker build -t local-tts:dev .
docker run --rm -p 8501:8501 -e TTS_DEVICE_MODE=cpu -e HF_MODEL_ID=Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice local-tts:dev
```

Expected:

- Test suite passes.
- Container starts both API and UI processes.
- Streamlit page loads on `http://localhost:8501`.
- Synthesis works with preset and uploaded reference audio flows.
