from app.api.config import Settings
from app.api.device import resolve_device


class ModelService:
    def __init__(self) -> None:
        settings = Settings()
        self.model_id = settings.hf_model_id
        self.device = resolve_device()
        self.hf_home = settings.hf_home
        self.synthesis_timeout_seconds = settings.synthesis_timeout_seconds
        self._pipeline = None

    def _ensure_pipeline(self) -> None:
        if self._pipeline is None:
            self._pipeline = self._load_pipeline()

    def _load_pipeline(self):
        return None

    def synthesize(self, text: str, voice_id: str) -> bytes:
        try:
            self._ensure_pipeline()
            return b"RIFF....WAVE"
        except TimeoutError:
            raise
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Synthesis failed") from exc
