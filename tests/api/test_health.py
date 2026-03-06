from fastapi.testclient import TestClient

import app.api.main as api_main

app = api_main.app


def test_health_endpoint():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert "status" in body
    assert "device" in body


def test_app_startup_preloads_model(monkeypatch) -> None:
    calls = {"count": 0}

    def _fake_preload() -> None:
        calls["count"] += 1

    monkeypatch.setattr(api_main.model_service, "preload", _fake_preload, raising=False)

    with TestClient(api_main.app):
        pass

    assert calls["count"] == 1
