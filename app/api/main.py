from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Response, UploadFile

from app.api.device import resolve_device
from app.api.schemas import SynthesizeRequest
from app.api.services.model_service import ModelService
from app.api.voice_store import CLONED_VOICES, PRESET_VOICES

app = FastAPI(title="Local TTS API")

ALLOWED_AUDIO_TYPES = {"audio/wav", "audio/x-wav", "audio/mpeg"}
model_service = ModelService()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "device": resolve_device(), "model_loaded": False}


@app.get("/voices")
def get_voices() -> dict:
    return {"presets": PRESET_VOICES, "cloned": list(CLONED_VOICES)}


@app.post("/voices/clone")
def clone_voice(reference_audio: UploadFile = File(...)) -> dict:
    if reference_audio.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported audio type")

    voice_id = f"clone_{uuid4().hex[:8]}"
    CLONED_VOICES[voice_id] = reference_audio.filename or "uploaded"
    return {"voice_id": voice_id}


@app.post("/synthesize")
def synthesize(payload: SynthesizeRequest) -> Response:
    selected_voice_id = payload.voice_id or payload.cloned_voice_id or "neutral_female"
    audio = model_service.synthesize(payload.text, selected_voice_id)
    return Response(content=audio, media_type="audio/wav")
