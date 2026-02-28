import json
import shutil
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest


def _wait_for_url(url: str, timeout_seconds: int = 90) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=5) as response:
                if response.status == 200:
                    return
        except URLError:
            time.sleep(1)
    raise AssertionError(f"Timed out waiting for {url}")


def _published_port(container_id: str) -> int:
    output = subprocess.check_output(
        ["docker", "port", container_id, "8501/tcp"],
        text=True,
    ).strip()
    return int(output.rsplit(":", 1)[-1])


def test_container_smoke() -> None:
    if shutil.which("docker") is None:
        pytest.skip("docker not available")

    project_root = Path(__file__).resolve().parents[2]
    image_tag = f"local-tts-smoke:{int(time.time())}"

    subprocess.run(["docker", "build", "-t", image_tag, "."], cwd=project_root, check=True)
    container_id = subprocess.check_output(
        [
            "docker",
            "run",
            "-d",
            "--rm",
            "-p",
            "0:8501",
            "-e",
            "TTS_DEVICE_MODE=cpu",
            "-e",
            "HF_MODEL_ID=Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
            image_tag,
        ],
        text=True,
    ).strip()

    try:
        port = _published_port(container_id)
        _wait_for_url(f"http://127.0.0.1:{port}")

        health_output = subprocess.check_output(
            [
                "docker",
                "exec",
                container_id,
                "python",
                "-c",
                "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).read().decode())",
            ],
            text=True,
        ).strip()
        health_payload = json.loads(health_output)
        assert health_payload["status"] == "ok"
        assert "device" in health_payload
    finally:
        subprocess.run(["docker", "rm", "-f", container_id], check=False)
