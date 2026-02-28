from fastapi.testclient import TestClient

from app.api.main import app


def test_get_voices_returns_presets() -> None:
    client = TestClient(app)
    res = client.get("/voices")
    assert res.status_code == 200
    assert "presets" in res.json()


def test_clone_endpoint_rejects_non_audio() -> None:
    client = TestClient(app)
    res = client.post(
        "/voices/clone",
        files={"reference_audio": ("sample.txt", b"hello", "text/plain")},
    )
    assert res.status_code == 400
