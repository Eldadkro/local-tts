from __future__ import annotations

import io
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import TYPE_CHECKING

import soundfile as sf
import torch

from app.api.config import Settings
from app.api.device import resolve_device

if TYPE_CHECKING:
    from qwen_tts import Qwen3TTSModel


class ModelService:
    def __init__(self) -> None:
        settings = Settings()
        self.model_id = settings.hf_model_id
        self.device = resolve_device()
        self.hf_home = settings.hf_home
        self.synthesis_timeout_seconds = settings.synthesis_timeout_seconds
        self._pipeline: Qwen3TTSModel | None = None

    @property
    def is_loaded(self) -> bool:
        return self._pipeline is not None

    def preload(self) -> None:
        self._ensure_pipeline()

    def _runtime_candidates(self) -> list[tuple[str, torch.dtype]]:
        candidates: list[tuple[str, torch.dtype]] = []

        allow_mps = self.device in {"auto", "mps"}
        allow_gpu = self.device in {"auto", "gpu"}
        allow_cpu = self.device in {"auto", "cpu"}

        if allow_mps and torch.backends.mps.is_available():
            candidates.extend(
                [
                    ("mps", torch.bfloat16),
                    ("mps", torch.float32),
                ]
            )

        if allow_gpu and torch.cuda.is_available():
            candidates.extend(
                [
                    ("cuda:0", torch.bfloat16),
                    ("cuda:0", torch.float32),
                ]
            )

        if allow_cpu:
            candidates.append(("cpu", torch.float32))

        if candidates:
            return candidates

        if self.device == "mps":
            raise RuntimeError("MPS device requested but not available")
        if self.device == "gpu":
            raise RuntimeError("GPU device requested but CUDA is not available")
        raise RuntimeError(f"No runtime candidates available for device mode: {self.device}")

    def _ensure_pipeline(self) -> None:
        if self._pipeline is None:
            self._pipeline = self._load_pipeline()

    def _load_pipeline(self):
        from qwen_tts import Qwen3TTSModel

        if self.hf_home:
            os.environ["HF_HOME"] = self.hf_home

        last_error: Exception | None = None
        for runtime_device, runtime_dtype in self._runtime_candidates():
            try:
                return Qwen3TTSModel.from_pretrained(
                    self.model_id,
                    device_map=runtime_device,
                    dtype=runtime_dtype,
                )
            except Exception as exc:  # pragma: no cover - backend dependent
                last_error = exc

        raise RuntimeError("Unable to load model on any runtime candidate") from last_error

    def _run_inference_with_timeout(self, text: str, voice_id: str):
        if self._pipeline is None:
            raise RuntimeError("Model pipeline is not loaded")

        timed_out = False
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(
            self._pipeline.generate_custom_voice,
            text=text,
            language="English",
            speaker=voice_id,
        )

        try:
            return future.result(timeout=self.synthesis_timeout_seconds)
        except FuturesTimeoutError as exc:
            timed_out = True
            future.cancel()
            executor.shutdown(wait=False, cancel_futures=True)
            raise TimeoutError("Synthesis timed out") from exc
        finally:
            if not timed_out:
                executor.shutdown(wait=True, cancel_futures=True)

    def synthesize(self, text: str, voice_id: str) -> bytes:
        try:
            self._ensure_pipeline()
            wavs, sample_rate = self._run_inference_with_timeout(text=text, voice_id=voice_id)
            if not wavs:
                raise RuntimeError("Model did not return audio samples")

            audio = wavs[0]
            if isinstance(audio, torch.Tensor):
                audio = audio.detach().cpu().numpy()

            wav_buffer = io.BytesIO()
            sf.write(wav_buffer, audio, sample_rate, format="WAV")
            return wav_buffer.getvalue()
        except TimeoutError:
            raise
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Synthesis failed") from exc
