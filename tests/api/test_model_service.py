from __future__ import annotations

import numpy as np

from app.api.services.model_service import ModelService


class _FakePipeline:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def generate_custom_voice(self, **kwargs):
        self.calls.append(kwargs)
        return [np.zeros(1600, dtype=np.float32)], 16000


def test_model_service_initializes_with_model_id(monkeypatch) -> None:
    monkeypatch.setenv("HF_MODEL_ID", "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")
    svc = ModelService()
    assert svc.model_id == "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"


def test_model_service_preload_loads_pipeline(monkeypatch) -> None:
    svc = ModelService()
    fake_pipeline = _FakePipeline()
    monkeypatch.setattr(svc, "_load_pipeline", lambda: fake_pipeline)

    assert svc.is_loaded is False
    svc.preload()
    assert svc.is_loaded is True


def test_synthesize_returns_wav_bytes(monkeypatch) -> None:
    svc = ModelService()
    fake_pipeline = _FakePipeline()
    monkeypatch.setattr(svc, "_load_pipeline", lambda: fake_pipeline)

    audio = svc.synthesize("hello", "Ryan")

    assert audio[:4] == b"RIFF"
    assert b"WAVE" in audio[:16]
    assert fake_pipeline.calls == [{"text": "hello", "language": "English", "speaker": "Ryan"}]
