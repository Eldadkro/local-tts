from pydantic import BaseModel, Field


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
    text: str = Field(min_length=1, max_length=20000)
    voice_mode: str
    voice_id: str | None = None
    cloned_voice_id: str | None = None
