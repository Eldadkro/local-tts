import os

import httpx


DEFAULT_API_BASE_URL = os.getenv("LOCAL_TTS_API_BASE_URL", "http://127.0.0.1:8000")


def build_synthesize_payload(
    text: str,
    voice_mode: str,
    voice_id: str | None,
    cloned_voice_id: str | None,
) -> dict:
    return {
        "text": text,
        "voice_mode": voice_mode,
        "voice_id": voice_id,
        "cloned_voice_id": cloned_voice_id,
    }


def get_voices(api_base_url: str = DEFAULT_API_BASE_URL) -> dict:
    response = httpx.get(f"{api_base_url}/voices", timeout=30)
    response.raise_for_status()
    return response.json()


def clone_voice(
    file_name: str,
    content: bytes,
    content_type: str,
    api_base_url: str = DEFAULT_API_BASE_URL,
) -> str:
    files = {"reference_audio": (file_name, content, content_type)}
    response = httpx.post(f"{api_base_url}/voices/clone", files=files, timeout=60)
    response.raise_for_status()
    return response.json()["voice_id"]


def synthesize(payload: dict, api_base_url: str = DEFAULT_API_BASE_URL) -> bytes:
    response = httpx.post(f"{api_base_url}/synthesize", json=payload, timeout=120)
    response.raise_for_status()
    return response.content
