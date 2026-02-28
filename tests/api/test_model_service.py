from app.api.services.model_service import ModelService


def test_model_service_initializes_with_model_id(monkeypatch) -> None:
    monkeypatch.setenv("HF_MODEL_ID", "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")
    svc = ModelService()
    assert svc.model_id == "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
