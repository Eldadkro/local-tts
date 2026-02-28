# Qwen3-TTS Agent - Simple README

A lightweight agent for generating speech using **Qwen3-TTS** models (custom voices, voice design, or voice cloning).

---

## Dependencies

### System Requirements
- Python **3.10-3.12** (3.12 recommended)
- NVIDIA GPU recommended (CUDA support)
- PyTorch-compatible environment

### Python Packages

Install core dependencies:

```bash
pip install -U qwen-tts torch soundfile
```

(Optional - improves performance and reduces GPU memory)

```bash
pip install -U flash-attn --no-build-isolation
```

> FlashAttention 2 requires compatible GPU hardware and FP16/BF16 precision.

---

## Environment Setup (Recommended)

Create a clean environment:

```bash
conda create -n qwen3-tts python=3.12 -y
conda activate qwen3-tts
pip install -U qwen-tts torch soundfile
```

---

## How to Use

### 1. Load the Model

```python
import torch
from qwen_tts import Qwen3TTSModel

model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    device_map="cuda:0",      # use "cpu" if no GPU
    dtype=torch.bfloat16
)
```

---

### 2. Generate Speech (Default Voices)

```python
import soundfile as sf

wavs, sr = model.generate_custom_voice(
    text="Hello, this is a test of Qwen3 text to speech.",
    language="English",
    speaker="Ryan"   # default English voice
)

sf.write("output.wav", wavs[0], sr)
```

---

### 3. Available Default English Voices

```python
default_english_voices = [
    "Ryan",
    "Aiden"
]
```

You can list all supported speakers dynamically:

```python
model.get_supported_speakers()
```

---

## Agent Usage Pattern

Typical agent workflow:

1. Receive text input
2. Select speaker + language
3. Generate audio
4. Save or stream waveform

Example agent function:

```python
def speak(text, speaker="Ryan"):
    wavs, sr = model.generate_custom_voice(
        text=text,
        language="English",
        speaker=speaker
    )
    return wavs[0], sr
```

---

## Model Options

| Model         | Purpose                         |
| ------------- | ------------------------------- |
| `CustomVoice` | Use built-in voices (simplest)  |
| `VoiceDesign` | Create voices from descriptions |
| `Base`        | Clone voices from audio samples |

Recommended starting point:

```
Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice
```

---

## Run Local Demo UI (Optional)

```bash
qwen-tts-demo Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice --port 8000
```

Open:

```
http://localhost:8000
```

---

## Minimal Agent Checklist

- [ ] Install dependencies
- [ ] Load model once at startup
- [ ] Choose speaker
- [ ] Generate audio
- [ ] Save or stream output

---

## License and Credits

Qwen3-TTS by the Qwen team (Alibaba).
See official Hugging Face model page for details.

---
