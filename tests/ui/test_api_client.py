from app.ui.api_client import build_synthesize_payload


def test_build_payload_for_preset_voice() -> None:
    payload = build_synthesize_payload("hello", "preset", "neutral_female", None)
    assert payload["text"] == "hello"
    assert payload["voice_mode"] == "preset"
