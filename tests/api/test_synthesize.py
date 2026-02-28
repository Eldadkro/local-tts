from fastapi.testclient import TestClient

from app.api.main import app


def test_synthesize_returns_audio_wav() -> None:
    client = TestClient(app)
    payload = {"text": "hello world", "voice_mode": "preset", "voice_id": "neutral_female"}
    res = client.post("/synthesize", json=payload)
    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/wav"
