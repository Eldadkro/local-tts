from __future__ import annotations

import pytest

import app.api.main as api_main


@pytest.fixture(autouse=True)
def _stub_api_model_service(monkeypatch):
    monkeypatch.setattr(api_main.model_service, "preload", lambda: None)
    monkeypatch.setattr(api_main.model_service, "synthesize", lambda text, voice_id: b"RIFF....WAVE")
