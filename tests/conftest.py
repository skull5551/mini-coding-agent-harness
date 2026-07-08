import pytest


def make_ws(tmp_path, files: dict[str, str]):
    for path, content in files.items():
        p = tmp_path / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return tmp_path