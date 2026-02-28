from fastapi import FastAPI

from app.api.device import resolve_device

app = FastAPI(title="Local TTS API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "device": resolve_device(), "model_loaded": False}
