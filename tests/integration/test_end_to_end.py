from fastapi.testclient import TestClient

from app.api.main import app


def test_end_to_end_preset_and_clone_flows() -> None:
    client = TestClient(app)

    voices = client.get("/voices")
    assert voices.status_code == 200
    assert voices.json()["presets"]

    preset_response = client.post(
        "/synthesize",
        json={"text": "hello", "voice_mode": "preset", "voice_id": "Ryan"},
    )
    assert preset_response.status_code == 200
    assert preset_response.headers["content-type"] == "audio/wav"

    clone_response = client.post(
        "/voices/clone",
        files={"reference_audio": ("sample.wav", b"RIFF....WAVE", "audio/wav")},
    )
    assert clone_response.status_code == 200
    cloned_voice_id = clone_response.json()["voice_id"]

    cloned_response = client.post(
        "/synthesize",
        json={"text": "hello from clone", "voice_mode": "clone", "cloned_voice_id": cloned_voice_id},
    )
    assert cloned_response.status_code == 200
    assert cloned_response.headers["content-type"] == "audio/wav"
