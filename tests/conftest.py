import os
import pytest


@pytest.fixture(autouse=True)
def _ensure_harness_secret_key():
    os.environ.setdefault("HARNESS_SECRET_KEY", "test-secret-key")


def make_ws(tmp_path, files: dict[str, str]):
    for path, content in files.items():
        p = tmp_path / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return tmp_path