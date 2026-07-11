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
    from src.state.manager import StateManager
    sm = StateManager(db)
    sm.save_api_key("openai", "sk-test-key")

    from unittest.mock import patch, MagicMock
    mock_llm = MagicMock()
    mock_llm.chat.return_value = json.dumps({"action": "done", "reason": "completed"})

    with patch("src.cli.main.LiteLLMProvider", return_value=mock_llm):
        result = r.invoke(app, [
            "run", "--db", db, "--workspace", ws,
            "--provider", "openai", "fix the bug"
        ])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "task_id" in data
    assert data["status"] == "success"
    assert "total_steps" in data


def test_cli_run_no_api_key(runner):
    r, db, ws = runner
    result = r.invoke(app, [
        "run", "--db", db, "--workspace", ws,
        "--provider", "openai", "fix the bug"
    ])
    assert result.exit_code != 0
    assert "API key" in result.stdout


def test_cli_status(runner):
    r, db, ws = runner
    from src.state.manager import StateManager
    sm = StateManager(db)
    task_id = sm.create_task("test task")
    result = r.invoke(app, ["status", "--db", db, "--workspace", ws, task_id])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["id"] == task_id


def test_cli_status_not_found(runner):
    r, db, ws = runner
    result = r.invoke(app, ["status", "--db", db, "--workspace", ws, "nonexistent"])
    assert result.exit_code != 0


def test_cli_config_set_key(runner):
    r, db, ws = runner
    from src.cli.main import set_key
    set_key(provider="openai", key="sk-test-12345", db=db, workspace=ws)
    from src.state.manager import StateManager
    sm = StateManager(db)
    keys = sm.get_api_keys()
    assert len(keys) == 1
    assert keys[0]["provider"] == "openai"
    assert "****" in keys[0]["key_masked"]
    raw = sm.get_api_key("openai")
    assert raw == "sk-test-12345"


def test_cli_config_set_key_hidden_input(runner):
    r, db, ws = runner
    result = r.invoke(
        app,
        ["config", "set-key", "--db", db, "--workspace", ws, "openai"],
        input="sk-hidden-test\n",
    )
    assert result.exit_code == 0
    from src.state.manager import StateManager
    sm = StateManager(db)
    raw = sm.get_api_key("openai")
    assert raw == "sk-hidden-test"


def test_cli_config_list_keys(runner):
    r, db, ws = runner
    set_result = r.invoke(app, ["config", "set-key", "--db", db, "--workspace", ws, "openai", "--key", "sk-test"])
    assert set_result.exit_code == 0
    result = r.invoke(app, ["config", "list-keys", "--db", db, "--workspace", ws])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data) == 1
    assert data[0]["provider"] == "openai"


def test_cli_help(runner):
    r, db, ws = runner
    result = r.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "run" in result.stdout
    assert "status" in result.stdout