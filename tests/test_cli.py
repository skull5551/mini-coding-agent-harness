import json
import pytest
from typer.testing import CliRunner
from src.cli.main import app


@pytest.fixture
def runner(tmp_path):
    db_path = str(tmp_path / "test.db")
    ws_path = str(tmp_path / "workspaces")
    return CliRunner(), db_path, ws_path


def test_cli_run(runner):
    r, db, ws = runner
    result = r.invoke(app, ["--db", db, "--workspace", ws, "run", "fix the bug"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "task_id" in data
    assert data["status"] == "pending"


def test_cli_status(runner):
    r, db, ws = runner
    import json
    create = r.invoke(app, ["--db", db, "--workspace", ws, "run", "test task"])
    task_id = json.loads(create.stdout)["task_id"]
    result = r.invoke(app, ["--db", db, "--workspace", ws, "status", task_id])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["id"] == task_id


def test_cli_status_not_found(runner):
    r, db, ws = runner
    result = r.invoke(app, ["--db", db, "--workspace", ws, "status", "nonexistent"])
    assert result.exit_code != 0


def test_cli_config_set_key(runner):
    r, db, ws = runner
    result = r.invoke(app, ["--db", db, "--workspace", ws, "config", "set-key", "openai", "sk-test"])
    assert result.exit_code == 0


def test_cli_config_list_keys(runner):
    r, db, ws = runner
    r.invoke(app, ["--db", db, "--workspace", ws, "config", "set-key", "openai", "sk-test"])
    result = r.invoke(app, ["--db", db, "--workspace", ws, "config", "list-keys"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data) >= 1
    assert data[0]["provider"] == "openai"


def test_cli_help(runner):
    r, db, ws = runner
    result = r.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "run" in result.stdout
    assert "status" in result.stdout