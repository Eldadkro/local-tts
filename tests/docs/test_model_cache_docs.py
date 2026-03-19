from pathlib import Path


def test_model_cache_workflow_documented() -> None:
    gitignore = Path(".gitignore").read_text()
    readme = Path("README.md").read_text()

    assert "model/" in gitignore
    assert "./model:/app/model" in readme
    assert "docker compose up prod" in readme
    assert "docker compose run --rm dev bash" in readme
    assert "docker compose run --rm warm-model" in readme
