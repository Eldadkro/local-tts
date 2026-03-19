# Docker Dev/Prod Model Cache Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the container setup support both prod and dev workflows while persisting the downloaded Hugging Face model under the local `model/` directory so repeat runs do not re-download it.

**Architecture:** Split the current single Docker image into shared `base` plus `prod` and `dev` targets. Keep runtime environment variables aligned across both targets, mount the host `model/` directory into the container as the Hugging Face cache path, and move startup behavior into target-specific defaults so prod auto-starts services while dev stays idle until the developer starts them manually.

**Tech Stack:** Docker multi-stage builds, Docker Compose, Python, FastAPI, Streamlit, supervisor, pytest.

---

## File Responsibilities

- `Dockerfile` - defines shared `base` image plus separate `prod` and `dev` targets with different default commands.
- `compose.yaml` - defines `prod` and `dev` services that share the same environment and mount `./model:/app/model`.
- `app/api/config.py` - defines runtime settings defaults for `HF_HOME` and `PRELOAD_MODEL_ON_STARTUP`.
- `app/api/main.py` - applies the startup preload toggle during FastAPI lifespan initialization.
- `app/api/services/model_service.py` - consumes the configured Hugging Face cache path when loading the model.
- `.gitignore` - keeps the local `model/` cache out of version control.
- `README.md` - documents dev/prod build/run commands and the local model cache workflow.
- `tests/api/test_config.py` - verifies settings defaults and environment overrides for model cache and preload behavior.
- `tests/api/test_health.py` - verifies the app startup lifecycle respects the preload toggle.
- `tests/integration/test_container_smoke.py` - verifies the `prod` image auto-starts services, the `dev` image stays idle by default, and both work with a local `model/` bind mount.
- `tests/docs/test_model_cache_docs.py` - verifies docs and gitignore capture the local cache workflow.

## Chunk 1: Test Coverage and Runtime Contract

### Task 1: Add settings and startup behavior tests

**Files:**
- Modify: `tests/api/test_config.py`
- Modify: `tests/api/test_health.py`
- Modify: `app/api/main.py`
- Modify: `app/api/config.py`

- [ ] **Step 1: Write the failing test**

```python
from app.api.config import Settings


def test_settings_default_to_local_model_cache(monkeypatch) -> None:
    monkeypatch.delenv("HF_HOME", raising=False)
    monkeypatch.delenv("PRELOAD_MODEL_ON_STARTUP", raising=False)

    settings = Settings()

    assert settings.hf_home == "/app/model"
    assert settings.preload_model_on_startup is True


def test_settings_allow_preload_disable(monkeypatch) -> None:
    monkeypatch.setenv("PRELOAD_MODEL_ON_STARTUP", "0")

    settings = Settings()

    assert settings.preload_model_on_startup is False
```

```python
from fastapi.testclient import TestClient

import app.api.main as api_main


def test_app_startup_skips_preload_when_disabled(monkeypatch) -> None:
    monkeypatch.setenv("PRELOAD_MODEL_ON_STARTUP", "0")
    calls = {"count": 0}

    def _fake_preload() -> None:
        calls["count"] += 1

    monkeypatch.setattr(api_main.model_service, "preload", _fake_preload, raising=False)

    with TestClient(api_main.app):
        pass

    assert calls["count"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_config.py tests/api/test_health.py -v`
Expected: FAIL because `Settings` does not provide the local cache default or preload toggle yet.

- [ ] **Step 3: Write minimal implementation**

```python
class Settings(BaseSettings):
    hf_home: str = "/app/model"
    preload_model_on_startup: bool = True


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.preload_model_on_startup:
        model_service.preload()
    yield
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_config.py tests/api/test_health.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/api/main.py app/api/config.py tests/api/test_config.py tests/api/test_health.py
git commit -m "feat: make model preload configurable"
```

### Task 2: Add container smoke coverage for prod runtime contract

**Files:**
- Modify: `tests/integration/test_container_smoke.py`
- Create: `compose.yaml`
- Modify: `Dockerfile`
- Modify: `README.md`

- [ ] **Step 1: Write the failing test**

Extend the smoke test so it first creates the local cache directory and then verifies both targets:

```python
model_dir = project_root / "model"
model_dir.mkdir(exist_ok=True)

subprocess.run(["docker", "build", "--target", "prod", "-t", image_tag, "."], cwd=project_root, check=True)
prod_container_id = subprocess.check_output(
    [
        "docker",
        "run",
        "-d",
        "--rm",
        "-p",
        "0:8501",
        "-e",
        "TTS_DEVICE_MODE=cpu",
        "-e",
        f"HF_HOME=/app/model",
        "-v",
        f"{model_dir}:/app/model",
        image_tag,
    ],
    text=True,
).strip()

subprocess.run(["docker", "build", "--target", "dev", "-t", dev_tag, "."], cwd=project_root, check=True)
dev_container_id = subprocess.check_output(
    [
        "docker",
        "run",
        "-d",
        "--rm",
        "-e",
        "HF_HOME=/app/model",
        "-v",
        f"{model_dir}:/app/model",
        dev_tag,
    ],
    text=True,
).strip()

dev_processes = subprocess.check_output(["docker", "top", dev_container_id], text=True)
assert "supervisord" not in dev_processes
assert "uvicorn" not in dev_processes
assert "streamlit" not in dev_processes
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_container_smoke.py -v`
Expected: FAIL because the current Dockerfile has no `prod` or `dev` targets and no persistent local cache contract.

- [ ] **Step 3: Write minimal implementation**

Create a multi-stage Dockerfile structure:

```dockerfile
FROM nvidia/cuda:12.6.0-cudnn-runtime-ubuntu24.04 AS base
ENV HF_HOME=/app/model
...

FROM base AS prod
CMD ["/usr/bin/supervisord", "-c", "/app/docker/supervisord.conf"]

FROM base AS dev
CMD ["sleep", "infinity"]
```

Add a `compose.yaml` with `prod` and `dev` services sharing `./model:/app/model` and common env.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_container_smoke.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add Dockerfile compose.yaml tests/integration/test_container_smoke.py README.md
git commit -m "feat: add dev and prod container targets"
```

## Chunk 2: Docker Runtime Scripts and Local Cache Workflow

### Task 3: Document local model cache and ignore it in git

**Files:**
- Create: `tests/docs/test_model_cache_docs.py`
- Modify: `.gitignore`
- Modify: `README.md`

- [ ] **Step 1: Write the failing test**

Create `tests/docs/test_model_cache_docs.py`:

```python
from pathlib import Path


def test_model_cache_workflow_documented() -> None:
    gitignore = Path(".gitignore").read_text()
    readme = Path("README.md").read_text()

    assert "model/" in gitignore
    assert "./model:/app/model" in readme
    assert "docker compose up prod" in readme
    assert "docker compose run --rm dev bash" in readme
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/docs/test_model_cache_docs.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

Document:
- `docker compose build dev`
- `docker compose build prod`
- `docker compose up prod`
- `docker compose run --rm dev bash`
- `model/` as the persistent local Hugging Face cache

Add `model/` to `.gitignore`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/docs/test_model_cache_docs.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .gitignore README.md tests/docs/test_model_cache_docs.py
git commit -m "docs: document local model cache workflow"
```

## Chunk 3: Final Verification

### Task 5: Run focused verification

**Files:**
- Modify: none
- Test: `tests/api/test_config.py`
- Test: `tests/api/test_model_service.py`
- Test: `tests/api/test_health.py`
- Test: `tests/docs/test_model_cache_docs.py`
- Test: `tests/integration/test_container_smoke.py`

- [ ] **Step 1: Run Python tests**

Run: `pytest tests/api/test_config.py tests/api/test_model_service.py tests/api/test_health.py tests/docs/test_model_cache_docs.py tests/integration/test_container_smoke.py -v`
Expected: PASS.

- [ ] **Step 2: Verify dev target stays idle**

Run: `docker build --target dev -t local-tts:dev . && docker run -d --rm --name local-tts-dev-check local-tts:dev && docker top local-tts-dev-check && docker rm -f local-tts-dev-check`
Expected: container starts with only the idle command and without `uvicorn`, `streamlit`, or `supervisord`.

- [ ] **Step 3: Verify prod target starts services with local cache mount**

Run: `mkdir -p model && docker build --target prod -t local-tts:prod . && docker run -d --rm --name local-tts-prod-check -p 8501:8501 -e TTS_DEVICE_MODE=cpu -v "$PWD/model:/app/model" local-tts:prod && python - <<'PY'
import urllib.request

body = urllib.request.urlopen('http://127.0.0.1:8501', timeout=30).read().decode()
assert 'Streamlit' in body
PY
docker exec local-tts-prod-check python - <<'PY'
import json
import urllib.request

health = urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=30).read().decode()
payload = json.loads(health)
assert payload['status'] == 'ok'
PY
python - <<'PY'
from pathlib import Path

files = [path for path in Path('model').rglob('*') if path.is_file()]
assert files, 'expected downloaded model cache files under model/'
PY
docker rm -f local-tts-prod-check && docker run -d --rm --name local-tts-prod-check-2 -p 8501:8501 -e TTS_DEVICE_MODE=cpu -v "$PWD/model:/app/model" local-tts:prod && docker exec local-tts-prod-check-2 python - <<'PY'
from pathlib import Path

files = [path for path in Path('/app/model').rglob('*') if path.is_file()]
assert files, 'expected reused model cache files mounted in container'
PY
docker rm -f local-tts-prod-check-2`
Expected: Streamlit loads, API health endpoint responds, cache files appear under `model/`, and the second run sees the existing mounted cache.

- [ ] **Step 4: Commit final polish if needed**

```bash
git add -A
git commit -m "chore: finalize container cache workflow"
```
