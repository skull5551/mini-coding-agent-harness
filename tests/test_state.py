import pytest
from src.state.manager import StateManager


def test_create_and_query_task(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = StateManager(str(db_path))
    task_id = mgr.create_task("fix login bug")
    task = mgr.get_task(task_id)
    assert task["description"] == "fix login bug"
    assert task["status"] == "pending"


def test_create_task_auto_fields(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = StateManager(str(db_path))
    task_id = mgr.create_task("add feature")
    task = mgr.get_task(task_id)
    assert task["id"] is not None
    assert task["created_at"] is not None
    assert task["updated_at"] is not None
    assert task["max_steps"] == 20


def test_update_task_status(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = StateManager(str(db_path))
    task_id = mgr.create_task("test")
    mgr.update_task_status(task_id, "running")
    task = mgr.get_task(task_id)
    assert task["status"] == "running"


def test_get_nonexistent_task(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = StateManager(str(db_path))
    result = mgr.get_task("nonexistent-uuid")
    assert result is None


def test_create_and_query_step(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = StateManager(str(db_path))
    task_id = mgr.create_task("test")
    step_id = mgr.create_step(task_id, step_number=1, action="read_file", input_summary="read main.py")
    steps = mgr.get_steps(task_id)
    assert len(steps) == 1
    assert steps[0]["action"] == "read_file"
    assert steps[0]["task_id"] == task_id


def test_create_tool_call(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = StateManager(str(db_path))
    task_id = mgr.create_task("test")
    step_id = mgr.create_step(task_id, step_number=1, action="read_file")
    call_id = mgr.create_tool_call(task_id, step_id, tool_name="read_file", tool_input='{"path": "test.py"}')
    calls = mgr.get_tool_calls(task_id)
    assert len(calls) == 1
    assert calls[0]["tool_name"] == "read_file"
    assert calls[0]["status"] == "success"


def test_create_and_query_api_key(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = StateManager(str(db_path))
    mgr.save_api_key("openai", "sk-****1234")
    keys = mgr.get_api_keys()
    assert len(keys) == 1
    assert keys[0]["provider"] == "openai"
    assert keys[0]["key_masked"] == "sk-****1234"


def test_delete_api_key(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = StateManager(str(db_path))
    mgr.save_api_key("openai", "sk-****1234")
    mgr.delete_api_key("openai")
    keys = mgr.get_api_keys()
    assert len(keys) == 0


def test_database_reuses_connection(tmp_path):
    db_path = tmp_path / "test.db"
    mgr1 = StateManager(str(db_path))
    mgr1.create_task("first")
    mgr2 = StateManager(str(db_path))
    tasks = mgr2.list_tasks()
    assert len(tasks) >= 1


def test_list_tasks_returns_all(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = StateManager(str(db_path))
    mgr.create_task("task 1")
    mgr.create_task("task 2")
    tasks = mgr.list_tasks()
    assert len(tasks) == 2


def test_api_key_encrypted_in_db(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = StateManager(str(db_path))
    raw = "sk-test-secret"
    mgr.save_api_key("openai", raw)

    conn = mgr.db.connect()
    row = conn.execute(
        "SELECT key_value FROM api_keys WHERE provider = ?", ("openai",)
    ).fetchone()
    stored = row["key_value"]
    assert raw not in stored
    assert stored != raw

    retrieved = mgr.get_api_key("openai")
    assert retrieved == raw


def test_encryption_roundtrip(tmp_path):
    db_path = tmp_path / "test.db"
    mgr = StateManager(str(db_path))
    mgr.save_api_key("openai", "sk-secret-key-123")
    assert mgr.get_api_key("openai") == "sk-secret-key-123"


def test_no_secret_key_raises_error(tmp_path, monkeypatch):
    monkeypatch.delenv("HARNESS_SECRET_KEY", raising=False)
    db_path = tmp_path / "test.db"
    mgr = StateManager(str(db_path))
    with pytest.raises(ValueError, match="HARNESS_SECRET_KEY"):
        mgr.save_api_key("openai", "sk-test")