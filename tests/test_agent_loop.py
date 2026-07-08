import json
import pytest

from src.agent.models import AgentDecision, AgentResult
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


def test_agent_decision_models():
    d1 = AgentDecision(action="tool_call", tool="read_file", params={"path": "main.py"})
    assert d1.action == "tool_call"
    assert d1.tool == "read_file"

    d2 = AgentDecision(action="done", reason="completed")
    assert d2.action == "done"


def test_agent_result_models():
    r = AgentResult(task_id="abc", status="success", total_steps=3)
    assert r.status == "success"
    assert r.total_steps == 3


async def test_agent_loop_complete_flow(tmp_path):
    ws = _make_ws(tmp_path, {
        "main.py": "def add(a, b): return a * b",
        "test_main.py": "from main import add\ndef test_add(): assert add(1, 2) == 3",
    })
    responses = [
        json.dumps({"action": "tool_call", "tool": "read_file", "params": {"path": "main.py"}}),
        json.dumps({"action": "tool_call", "tool": "write_file", "params": {"path": "main.py", "content": "def add(a, b): return a + b"}}),
        json.dumps({"action": "tool_call", "tool": "run_test", "params": {"command": f"pytest {ws / 'test_main.py'}"}}),
        json.dumps({"action": "done", "reason": "bug fixed"}),
    ]
    db_path = tmp_path / "test.db"
    task_mgr = TaskManager(str(db_path), base_workspace=str(ws))
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


async def test_agent_loop_max_steps(tmp_path):
    ws = _make_ws(tmp_path, {"main.py": "x = 1"})
    responses = [
        json.dumps({"action": "tool_call", "tool": "read_file", "params": {"path": "main.py"}})
    ] * 25
    db_path = tmp_path / "test.db"
    task_mgr = TaskManager(str(db_path), base_workspace=str(ws))
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


async def test_agent_loop_explicit_fail(tmp_path):
    ws = _make_ws(tmp_path, {"main.py": "x = 1"})
    responses = [
        json.dumps({"action": "tool_call", "tool": "read_file", "params": {"path": "main.py"}}),
        json.dumps({"action": "failed", "reason": "cannot fix"}),
    ]
    db_path = tmp_path / "test.db"
    task_mgr = TaskManager(str(db_path), base_workspace=str(ws))
    loop = AgentLoop(
        llm=MockLLMProvider(responses=responses),
        tool_registry=ToolRegistry(workspace=str(ws)),
        feedback_analyzer=FeedbackAnalyzer(),
        task_mgr=task_mgr,
    )
    task_id = task_mgr.create_task("test")
    result = await loop.run(task_id, max_steps=10)
    assert result.status == "failed"
    assert result.total_steps == 2


async def test_agent_loop_records_steps(tmp_path):
    ws = _make_ws(tmp_path, {"main.py": "x = 1"})
    responses = [
        json.dumps({"action": "tool_call", "tool": "read_file", "params": {"path": "main.py"}}),
        json.dumps({"action": "done", "reason": "done"}),
    ]
    db_path = tmp_path / "test.db"
    task_mgr = TaskManager(str(db_path), base_workspace=str(ws))
    loop = AgentLoop(
        llm=MockLLMProvider(responses=responses),
        tool_registry=ToolRegistry(workspace=str(ws)),
        feedback_analyzer=FeedbackAnalyzer(),
        task_mgr=task_mgr,
    )
    task_id = task_mgr.create_task("test")
    await loop.run(task_id, max_steps=10)
    steps = task_mgr.get_steps(task_id)
    assert len(steps) >= 1
    assert steps[0]["action"] == "read_file"


async def test_agent_loop_invalid_tool_rejected(tmp_path):
    ws = _make_ws(tmp_path, {"main.py": "x = 1"})
    responses = [
        json.dumps({"action": "tool_call", "tool": "nonexistent_tool", "params": {}}),
        json.dumps({"action": "done", "reason": "stopped"}),
    ]
    db_path = tmp_path / "test.db"
    task_mgr = TaskManager(str(db_path), base_workspace=str(ws))
    loop = AgentLoop(
        llm=MockLLMProvider(responses=responses),
        tool_registry=ToolRegistry(workspace=str(ws)),
        feedback_analyzer=FeedbackAnalyzer(),
        task_mgr=task_mgr,
    )
    task_id = task_mgr.create_task("test")
    result = await loop.run(task_id, max_steps=10)
    assert result.status == "success"