import json
import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.agent.loop import AgentLoop
from src.llm.mock import MockLLMProvider
from src.tools.registry import ToolRegistry
from src.feedback.analyzer import FeedbackAnalyzer
from src.task.manager import TaskManager


def _make_ws(tmp_path, files: dict[str, str]):
    for path, content in files.items():
        p = tmp_path / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return tmp_path


async def test_e2e_full_flow_bugfix(tmp_path):
    ws = _make_ws(tmp_path, {
        "main.py": "def add(a, b): return a * b",
        "test_main.py": "from main import add\ndef test_add(): assert add(1, 2) == 3",
    })
    responses = [
        json.dumps({"action": "tool_call", "tool": "read_file", "params": {"path": "main.py"}}),
        json.dumps({"action": "tool_call", "tool": "write_file", "params": {"path": "main.py", "content": "def add(a, b): return a + b"}}),
        json.dumps({"action": "tool_call", "tool": "run_test", "params": {"command": f"pytest {ws}/test_main.py"}}),
        json.dumps({"action": "done", "reason": "bug fixed"}),
    ]
    db_path = str(tmp_path / "test.db")
    task_mgr = TaskManager(db_path, base_workspace=str(ws))
    loop = AgentLoop(
        llm=MockLLMProvider(responses=responses),
        tool_registry=ToolRegistry(workspace=str(ws)),
        feedback_analyzer=FeedbackAnalyzer(),
        task_mgr=task_mgr,
    )
    task_id = task_mgr.create_task("fix the bug")
    result = await loop.run(task_id, max_steps=10)
    assert result.status == "success"
    assert result.total_steps == 4
    steps = task_mgr.get_steps(task_id)
    assert len(steps) == 3
    assert steps[0]["action"] == "read_file"
    assert steps[1]["action"] == "write_file"
    assert steps[2]["action"] == "run_test"
    task = task_mgr.get_task(task_id)
    assert task["status"] == "success"


async def test_e2e_task_through_api(tmp_path):
    ws = _make_ws(tmp_path, {"main.py": "x = 1"})
    db_path = str(tmp_path / "test.db")
    app = create_app(db_path=db_path, base_workspace=str(ws))
    with TestClient(app) as client:
        create_resp = client.post("/api/tasks", json={"description": "test task"})
        assert create_resp.status_code == 200
        task_id = create_resp.json()["task_id"]

        get_resp = client.get(f"/api/tasks/{task_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "pending"

        list_resp = client.get("/api/tasks")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 1

        steps_resp = client.get(f"/api/tasks/{task_id}/steps")
        assert steps_resp.status_code == 200
        assert steps_resp.json() == []


async def test_e2e_max_steps_termination(tmp_path):
    ws = _make_ws(tmp_path, {"main.py": "x = 1"})
    responses = [
        json.dumps({"action": "tool_call", "tool": "read_file", "params": {"path": "main.py"}})
    ] * 25
    db_path = str(tmp_path / "test.db")
    task_mgr = TaskManager(db_path, base_workspace=str(ws))
    loop = AgentLoop(
        llm=MockLLMProvider(responses=responses),
        tool_registry=ToolRegistry(workspace=str(ws)),
        feedback_analyzer=FeedbackAnalyzer(),
        task_mgr=task_mgr,
    )
    task_id = task_mgr.create_task("test")
    result = await loop.run(task_id, max_steps=20)
    assert result.status == "failed"
    assert result.total_steps == 20
    task = task_mgr.get_task(task_id)
    assert task["status"] == "failed"


async def test_e2e_api_key_flow(tmp_path):
    db_path = str(tmp_path / "test.db")
    app = create_app(db_path=db_path, base_workspace=str(tmp_path))
    with TestClient(app) as client:
        save_resp = client.post("/api/config/keys", json={"provider": "openai", "key": "sk-secret-key-123"})
        assert save_resp.status_code == 200

        get_resp = client.get("/api/config/keys")
        assert get_resp.status_code == 200
        keys = get_resp.json()
        assert len(keys) == 1
        assert keys[0]["provider"] == "openai"
        assert "****" in keys[0]["key_masked"]
        assert "sk-secret-key-123" not in keys[0]["key_masked"]

        delete_resp = client.delete("/api/config/keys/openai")
        assert delete_resp.status_code == 200
        assert len(client.get("/api/config/keys").json()) == 0