#!/usr/bin/env python3
"""Toy script: download Qwen3-TTS and synthesize one sample sentence.

Intended for local experimentation on Apple Silicon first (MPS), with graceful
fallbacks when BF16 is not supported by the active backend.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

DEFAULT_MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
DEFAULT_TEXT = "Hello from a local toy Qwen3 TTS run on Apple Silicon."
DEFAULT_SPEAKER = "Ryan"


def runtime_candidates() -> list[tuple[str, torch.dtype]]:
    candidates: list[tuple[str, torch.dtype]] = []

    if torch.backends.mps.is_available():
        candidates.extend(
            [
                ("mps", torch.bfloat16),
                ("mps", torch.float32),
            ]
        )

    if torch.cuda.is_available():
        candidates.extend(
            [
                ("cuda:0", torch.bfloat16),
                ("cuda:0", torch.float32),
            ]
        )

    candidates.append(("cpu", torch.float32))
    return candidates


def load_model_with_fallbacks(model_id: str) -> tuple[Qwen3TTSModel, str, torch.dtype]:
    last_error: Exception | None = None

    for device, dtype in runtime_candidates():
        print(f"Trying model load on device={device}, dtype={dtype} ...")
        try:
            model = Qwen3TTSModel.from_pretrained(
                model_id,
                device_map=device,
                dtype=dtype,
            )
            print(f"Loaded model on device={device}, dtype={dtype}")
            return model, device, dtype
        except Exception as exc:  # pragma: no cover - runtime backend dependent
            last_error = exc
            print(
                f"Load failed on device={device}, dtype={dtype}: {exc}",
                file=sys.stderr,
            )

    raise RuntimeError("Unable to load model on any runtime candidate") from last_error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Toy Qwen3-TTS one-shot runner")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--text", default=DEFAULT_TEXT)
    parser.add_argument("--speaker", default=DEFAULT_SPEAKER)
    parser.add_argument("--language", default="English")
    parser.add_argument("--output", default="toy_output.wav")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    model, device, dtype = load_model_with_fallbacks(args.model_id)
    print(f"Generating audio with speaker={args.speaker}, device={device}, dtype={dtype}")

    wavs, sample_rate = model.generate_custom_voice(
        text=args.text,
        language=args.language,
        speaker=args.speaker,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), wavs[0], sample_rate)

    print(f"Saved audio to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
