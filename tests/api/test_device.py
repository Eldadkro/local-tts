from app.api.device import resolve_device


def test_resolve_device_cpu(monkeypatch):
    monkeypatch.setenv("TTS_DEVICE_MODE", "cpu")
    assert resolve_device() == "cpu"
