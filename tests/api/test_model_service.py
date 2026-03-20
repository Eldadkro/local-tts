from __future__ import annotations

import sys
import types

import numpy as np

from app.api.services.model_service import ModelService


class _FakePipeline:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def generate_custom_voice(self, **kwargs):
        self.calls.append(kwargs)
        return [np.zeros(1600, dtype=np.float32)], 16000


class _FakeQwen3TTSModel:
    calls: list[tuple[str, dict[str, object]]] = []

    @classmethod
    def from_pretrained(cls, model_ref: str, **kwargs):
        cls.calls.append((model_ref, kwargs))
        return _FakePipeline()


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
    assert fake_pipeline.calls == [
        {"text": "hello", "language": "English", "speaker": "Ryan"}
    ]


def test_load_pipeline_uses_local_model_folder_when_present(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.chdir(tmp_path)
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "config.json").write_text("{}")

    fake_module = types.SimpleNamespace(Qwen3TTSModel=_FakeQwen3TTSModel)
    _FakeQwen3TTSModel.calls = []

    svc = ModelService()
    monkeypatch.setattr(svc, "_runtime_candidates", lambda: [("cpu", "fp32")])
    monkeypatch.setitem(sys.modules, "qwen_tts", fake_module)

    svc._load_pipeline()

    model_ref, kwargs = _FakeQwen3TTSModel.calls[0]
    assert model_ref == str(model_dir)
    assert kwargs["device_map"] == "cpu"
    assert kwargs["dtype"] == "fp32"
    assert "cache_dir" not in kwargs


def test_load_pipeline_downloads_to_model_folder_when_missing(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.chdir(tmp_path)

    fake_module = types.SimpleNamespace(Qwen3TTSModel=_FakeQwen3TTSModel)
    _FakeQwen3TTSModel.calls = []

    svc = ModelService()
    monkeypatch.setattr(svc, "_runtime_candidates", lambda: [("cpu", "fp32")])
    monkeypatch.setitem(sys.modules, "qwen_tts", fake_module)

    svc._load_pipeline()

    model_ref, kwargs = _FakeQwen3TTSModel.calls[0]
    assert model_ref == svc.model_id
    assert kwargs["cache_dir"] == str(tmp_path / "model")
    assert kwargs["device_map"] == "cpu"
    assert kwargs["dtype"] == "fp32"
