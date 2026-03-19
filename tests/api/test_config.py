from app.api.config import Settings


def test_settings_defaults():
    s = Settings()
    assert s.tts_device_mode == "auto"
    assert s.preload_model_on_startup is True


def test_settings_allow_preload_disable(monkeypatch) -> None:
    monkeypatch.setenv("PRELOAD_MODEL_ON_STARTUP", "0")

    settings = Settings()

    assert settings.preload_model_on_startup is False
