from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    device: str
    model_loaded: bool


class VoiceCatalogResponse(BaseModel):
    presets: list[str]
    cloned: list[str]


class CloneVoiceResponse(BaseModel):
    voice_id: str


class SynthesizeRequest(BaseModel):
    text: str
    voice_mode: str
    voice_id: str | None = None
    cloned_voice_id: str | None = None
