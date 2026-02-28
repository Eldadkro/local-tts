from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    tts_device_mode: str = "auto"
    hf_model_id: str = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
