from fastapi.testclient import TestClient

from app.api.main import app


def test_synthesize_rejects_too_long_text() -> None:
    client = TestClient(app)
    long_text = "a" * 20001
    res = client.post(
        "/synthesize",
        json={"text": long_text, "voice_mode": "preset", "voice_id": "neutral_female"},
    )
    assert res.status_code == 422
