# local-tts

Local single-container text-to-speech app with FastAPI and Streamlit.

## Start Guide

### Prerequisites

- Python 3.11 or newer
- `pip`

### 1) Install dependencies

```bash
python3 -m pip install -e .
```

### 2) Start the API

```bash
uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3) Start the Streamlit UI

```bash
streamlit run app/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

### 4) Check health

```bash
curl http://127.0.0.1:8000/health
```

Expected response shape:

```json
{"status":"ok","device":"auto|cpu|gpu|mps","model_loaded":false}
```

## Configuration Guide

Configure runtime with environment variables:

- `TTS_DEVICE_MODE` (default: `auto`)
  - Allowed: `auto`, `cpu`, `gpu`, `mps`
  - Used by device resolution in the API.
- `HF_MODEL_ID` (default: `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice`)
  - Hugging Face model identifier for TTS model loading.

Example:

```bash
export TTS_DEVICE_MODE=cpu
export HF_MODEL_ID=Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice
uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload
```

## Run Tests

```bash
pytest -v
```

## Run With Docker

Build:

```bash
docker build -t local-tts:dev .
```

Run:

```bash
docker run --rm -p 8501:8501 -e TTS_DEVICE_MODE=cpu -e HF_MODEL_ID=Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice local-tts:dev
```

Then open `http://localhost:8501`.
