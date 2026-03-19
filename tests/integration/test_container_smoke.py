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


def _process_table(container_id: str) -> str:
    return subprocess.check_output(["docker", "top", container_id], text=True)


def test_container_smoke() -> None:
    if shutil.which("docker") is None:
        pytest.skip("docker not available")

    project_root = Path(__file__).resolve().parents[2]
    model_dir = project_root / "model"
    model_dir.mkdir(exist_ok=True)
    prod_image_tag = f"local-tts-smoke-prod:{int(time.time())}"
    dev_image_tag = f"local-tts-smoke-dev:{int(time.time())}"

    subprocess.run(
        ["docker", "build", "--target", "prod", "-t", prod_image_tag, "."],
        cwd=project_root,
        check=True,
    )
    subprocess.run(
        ["docker", "build", "--target", "dev", "-t", dev_image_tag, "."],
        cwd=project_root,
        check=True,
    )

    prod_container_id = subprocess.check_output(
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
            "-e",
            "PRELOAD_MODEL_ON_STARTUP=0",
            "-e",
            "HF_HOME=/app/model",
            "-v",
            f"{model_dir}:/app/model",
            prod_image_tag,
        ],
        text=True,
    ).strip()

    dev_container_id = subprocess.check_output(
        [
            "docker",
            "run",
            "-d",
            "--rm",
            "-e",
            "HF_HOME=/app/model",
            "-v",
            f"{model_dir}:/app/model",
            dev_image_tag,
        ],
        text=True,
    ).strip()

    try:
        port = _published_port(prod_container_id)
        _wait_for_url(f"http://127.0.0.1:{port}")

        health_output = subprocess.check_output(
            [
                "docker",
                "exec",
                prod_container_id,
                "python",
                "-c",
                "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).read().decode())",
            ],
            text=True,
        ).strip()
        health_payload = json.loads(health_output)
        assert health_payload["status"] == "ok"
        assert "device" in health_payload

        dev_processes = _process_table(dev_container_id)
        assert "sleep" in dev_processes
        assert "supervisord" not in dev_processes
        assert "uvicorn" not in dev_processes
        assert "streamlit" not in dev_processes
    finally:
        subprocess.run(["docker", "rm", "-f", prod_container_id], check=False)
        subprocess.run(["docker", "rm", "-f", dev_container_id], check=False)
