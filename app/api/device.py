import os


def resolve_device() -> str:
    mode = os.getenv("TTS_DEVICE_MODE", "auto").lower()
    if mode in {"cpu", "gpu", "mps"}:
        return mode
    return "auto"
