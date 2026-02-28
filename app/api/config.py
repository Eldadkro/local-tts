from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    tts_device_mode: str = "auto"
    hf_model_id: str = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
    hf_home: str | None = None
    synthesis_timeout_seconds: int = 120
    max_text_length: int = 20000
    max_reference_audio_bytes: int = 10 * 1024 * 1024
