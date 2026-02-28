# Qwen3 TTS + Streamlit Single-Container Design

Date: 2026-02-28
Status: Approved for planning

## Goals

- Build a reliable end-to-end TTS demo using `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice`.
- Provide a Streamlit frontend with both preset voices and uploaded reference-audio cloning.
- Package everything in one container image that can run on another computer later.
- Support runtime device selection via environment variable (`cpu`, `gpu`, `mps`, or `auto`).

## Non-Goals (v1)

- Real-time token-level audio streaming.
- Multi-replica orchestration or Kubernetes-native deployment.
- Advanced authentication and multi-tenant quotas.

## Architecture

Single Docker image, two internal processes:

1. `FastAPI` inference service (localhost only inside container)
2. `Streamlit` web UI (public exposed port)

`Streamlit` calls `FastAPI` over internal HTTP. The model is loaded only in the API service.

Why this design:

- Keeps one deployable artifact as requested.
- Preserves clean separation between UI and inference logic.
- Allows future split into two containers with minimal refactor.

## Components

### 1) Inference API (`FastAPI`)

Endpoints:

- `GET /health` - readiness/liveness and current device info.
- `POST /synthesize` - text + voice selection + optional controls; returns audio file bytes.
- `POST /voices/clone` - accepts short reference audio; returns temporary or persisted speaker profile ID.
- `GET /voices` - list presets and available cloned profiles.

Responsibilities:

- Model initialization and device routing (`cpu`, `gpu`, `mps`, `auto`).
- Hugging Face download/cache management.
- Audio post-processing (format normalization, sample-rate output).
- Request-level validation and timeout handling.

### 2) Frontend (`Streamlit`)

UI panels:

- Text input and synthesis controls.
- Voice mode selector: preset or upload reference clip.
- Audio player + downloadable output.
- System status widget (`/health` summary).

Responsibilities:

- Collect user inputs and call API.
- Show friendly error messages for invalid audio or model/device failures.
- Store lightweight session state (recent prompts, selected voice mode).

### 3) Container Runtime

- One image containing both app modules and dependencies.
- Process runner (for example `supervisord`) starts both `uvicorn` and `streamlit`.
- Expose Streamlit port; keep API bound to localhost.
- Mount persistent volumes for model cache and generated outputs.

## Data Flow

1. User opens Streamlit and enters text.
2. User chooses preset voice or uploads reference audio.
3. Streamlit sends request to API.
4. API ensures model is loaded on configured device.
5. API runs synthesis and returns generated WAV.
6. Streamlit plays audio and offers file download.

First startup:

- API pulls model from Hugging Face online.
- Artifacts are cached in mounted storage so later starts are faster and offline-capable (if cache remains).

## Environment Variables

- `TTS_DEVICE_MODE`: `auto|cpu|gpu|mps`
- `HF_MODEL_ID`: default `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice`
- `HF_HOME`: local cache path inside container
- `HF_TOKEN` (optional): needed only for gated/private model access
- `API_HOST`, `API_PORT`
- `STREAMLIT_PORT`
- `MAX_TEXT_CHARS`, `REQUEST_TIMEOUT_SEC`

Device behavior:

- `auto`: prefer CUDA, then MPS, then CPU.
- explicit `gpu|mps|cpu`: fail fast if requested backend is unavailable, unless optional fallback flag is enabled.

## Reliability and Error Handling

- Input validation: max text length, file type/size, minimum reference-audio duration.
- Graceful startup checks: clear error if model cannot download.
- Health endpoint reports model-loaded state and device.
- Bounded request timeout with user-facing retry guidance.
- Structured logs for request ID, latency, and backend device.

## Security and Hosting Considerations

- Keep API on localhost; expose only Streamlit externally.
- Avoid storing raw uploaded audio longer than needed unless explicitly configured.
- Load secrets (`HF_TOKEN`) from env vars, never hardcode.

## Test Strategy (v1)

- Unit tests for config parsing and device-selection logic.
- API contract tests for request validation and response shape.
- Smoke test in container: health check and one synthesis call.
- Manual UX test in Streamlit for both preset and upload flows.

## Deployment Model

- Build image once (`docker build`).
- Run on target machine with env vars and mounted cache/output volumes.
- Hosted machine can set `TTS_DEVICE_MODE=gpu` or `cpu`; local Apple Silicon dev can set `mps`.

## Future Extensions

- Split UI/API into separate containers (same APIs, minimal redesign).
- Add async job queue for heavy workloads.
- Add authentication and per-user voice profile management.
