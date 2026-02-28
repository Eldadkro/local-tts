from app.api.config import Settings


def test_settings_defaults():
    s = Settings()
    assert s.tts_device_mode == "auto"
