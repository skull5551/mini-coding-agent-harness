"""
Coding Agent Harness — 机制演示

演示核心流程:
LLM Decision → Agent Loop → Tool Execution → Feedback → Next Decision → Success

使用 MockLLMProvider，不调用真实 LLM。
"""

import asyncio
import json
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.loop import AgentLoop
from src.llm.mock import MockLLMProvider
from src.tools.registry import ToolRegistry
from src.feedback.analyzer import FeedbackAnalyzer
from src.task.manager import TaskManager


def main():
    tmpdir = tempfile.mkdtemp(prefix="harness_demo_")
    ws = os.path.join(tmpdir, "project")
    os.makedirs(ws)

    with open(os.path.join(ws, "main.py"), "w") as f:
        f.write("def add(a, b):\n    return a * b\n")
    with open(os.path.join(ws, "test_main.py"), "w") as f:
        f.write("from main import add\n\ndef test_add():\n    assert add(1, 2) == 3\n")

    db_path = os.path.join(tmpdir, "harness.db")
    test_cmd = f"pytest {os.path.join(ws, 'test_main.py')}"

    responses = [
        json.dumps({"action": "tool_call", "tool": "read_file", "params": {"path": "main.py"}}),
        json.dumps({"action": "tool_call", "tool": "write_file", "params": {"path": "main.py", "content": "def add(a, b):\n    return a + b\n"}}),
        json.dumps({"action": "tool_call", "tool": "run_test", "params": {"command": test_cmd}}),
        json.dumps({"action": "done", "reason": "bug fixed"}),
    ]

    mock_llm = MockLLMProvider(responses=responses)
    task_mgr = TaskManager(db_path, base_workspace=ws)
    tool_registry = ToolRegistry(workspace=ws)
    feedback_analyzer = FeedbackAnalyzer()

    loop = AgentLoop(
        llm=mock_llm,
        tool_registry=tool_registry,
        feedback_analyzer=feedback_analyzer,
        task_mgr=task_mgr,
    )

    task_id = task_mgr.create_task("fix add function bug")
    result = asyncio.run(loop.run(task_id, max_steps=10))

    print("=" * 50)
    print("  Coding Agent Harness — Mechanism Demo")
    print("=" * 50)
    print()
    print(f"Task: {result.task_id}")
    print(f"      {task_mgr.get_task(task_id)['description']}")
    print()

    steps = task_mgr.get_steps(task_id)
    for i, step in enumerate(steps):
        print(f"Step {i + 1}:")
        decision = json.loads(responses[i])
        if decision["action"] == "tool_call":
            print(f"  LLM Decision: {decision['tool']}")
            print(f"  Params:       {json.dumps(decision.get('params', {}))}")
            print(f"  Tool Result:  {'success' if step['output_summary'] else 'executed'}")
        print()

    print(f"Step {len(steps) + 1}:")
    print(f"  LLM Decision: done")
    print(f"  Reason:       {result.final_message}")
    print()

    print("=" * 50)
    print(f"  Final Result: {result.status.upper()}")
    print(f"  Total Steps:  {result.total_steps}")
    print("=" * 50)

    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()