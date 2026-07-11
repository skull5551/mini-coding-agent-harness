"""
Coding Agent Harness — 机制演示

演示三个核心机制:
  A. Governance — 危险动作拦截
  B. Feedback Loop — 失败反馈驱动修正
  C. Agent Loop — DECIDE→ACT→OBSERVE 循环 + 停机条件

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


def _make_ws(ws, files: dict[str, str]):
    for path, content in files.items():
        p = os.path.join(ws, path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)


def demo_governance(tmpdir):
    """
    Demo A: 危险动作拦截
    LLM 决定执行 rm -rf / → Guardrail 拦截 → 阻止执行
    """
    ws = os.path.join(tmpdir, "gov")
    os.makedirs(ws)
    _make_ws(ws, {"main.py": "x = 1"})

    db_path = os.path.join(tmpdir, "gov.db")
    task_mgr = TaskManager(db_path, base_workspace=ws)

    responses = [
        json.dumps({"action": "tool_call", "tool": "execute_command", "params": {"command": "rm -rf /"}}),
        json.dumps({"action": "done", "reason": "dangerous command blocked, giving up"}),
    ]
    mock_llm = MockLLMProvider(responses=responses)

    loop = AgentLoop(
        llm=mock_llm,
        tool_registry=ToolRegistry(workspace=ws),
        feedback_analyzer=FeedbackAnalyzer(),
        task_mgr=task_mgr,
    )

    task_id = task_mgr.create_task("clean up the system")
    result = asyncio.run(loop.run(task_id, max_steps=10))

    print("=" * 60)
    print("  Demo A: Governance — Dangerous Action Blocked")
    print("=" * 60)
    print()
    print(f"Task: {task_mgr.get_task(task_id)['description']}")
    print()

    steps = task_mgr.get_steps(task_id)
    for i, step in enumerate(steps):
        decision = json.loads(responses[i])
        print(f"Step {i + 1}:")
        print(f"  LLM Decision: {decision['action']} → {decision['tool']}")
        print(f"  Params:       {json.dumps(decision['params'])}")
        print(f"  Guardrail:    BLOCKED — dangerous command detected")
        print(f"  Tool Result:  {step['output_summary']}")
        print()

    print(f"Step {len(steps) + 1}:")
    print(f"  LLM Decision: {json.loads(responses[len(steps)])['action']}")
    print(f"  Reason:       {json.loads(responses[len(steps)])['reason']}")
    print()
    print(f"Result: {result.status.upper()} — {result.final_message}")
    print()


def demo_feedback_loop(tmpdir):
    """
    Demo B: 反馈闭环
    run_test 失败 → FeedbackAnalyzer 产生反馈 → Agent 读代码 → 修复 → 再测 → 通过
    """
    ws = os.path.join(tmpdir, "fb")
    os.makedirs(ws)
    _make_ws(ws, {
        "main.py": "def add(a, b):\n    return a * b\n",
        "test_main.py": "from main import add\n\ndef test_add():\n    assert add(1, 2) == 3\n",
    })

    db_path = os.path.join(tmpdir, "fb.db")
    test_cmd = f"pytest {os.path.join(ws, 'test_main.py')}"

    # Compute feedback BEFORE AgentLoop runs (code is still buggy)
    from src.tools.run_test import RunTestTool
    step1_direct = asyncio.run(RunTestTool(workspace=ws).execute({"command": test_cmd}))
    feedback_direct = FeedbackAnalyzer().analyze(step1_direct)

    # Step 1: run_test → FAIL (exit_code=1, AssertionError)
    # Step 2: read_file → analyze buggy code
    # Step 3: write_file → fix the bug
    # Step 4: run_test → PASS
    # Step 5: done
    responses = [
        json.dumps({"action": "tool_call", "tool": "run_test", "params": {"command": test_cmd}}),
        json.dumps({"action": "tool_call", "tool": "read_file", "params": {"path": "main.py"}}),
        json.dumps({"action": "tool_call", "tool": "write_file", "params": {"path": "main.py", "content": "def add(a, b):\n    return a + b\n"}}),
        json.dumps({"action": "tool_call", "tool": "run_test", "params": {"command": test_cmd}}),
        json.dumps({"action": "done", "reason": "bug fixed"}),
    ]

    mock_llm = MockLLMProvider(responses=responses)
    task_mgr = TaskManager(db_path, base_workspace=ws)
    loop = AgentLoop(
        llm=mock_llm,
        tool_registry=ToolRegistry(workspace=ws),
        feedback_analyzer=FeedbackAnalyzer(),
        task_mgr=task_mgr,
    )

    task_id = task_mgr.create_task("fix the bug in add()")
    result = asyncio.run(loop.run(task_id, max_steps=10))

    print("=" * 60)
    print("  Demo B: Feedback Loop — Failure → Retry → Success")
    print("=" * 60)
    print()
    print(f"Task: {task_mgr.get_task(task_id)['description']}")
    print()

    steps = task_mgr.get_steps(task_id)
    for i, step in enumerate(steps):
        decision = json.loads(responses[i])
        print(f"Step {i + 1}:")
        print(f"  LLM Decision: {decision['action']} → {decision['tool']}")
        if decision["action"] == "tool_call":
            print(f"  Params:       {json.dumps(decision.get('params', {}))[:80]}...")
            print(f"  Tool Result:  {step['output_summary'][:80]}...")
        print()

        if i == 0:
            print(f"  → FeedbackAnalyzer output:")
            print(f"     success: {feedback_direct.success}")
            print(f"     error_type: {feedback_direct.error_type}")
            print(f"     detail: {feedback_direct.detail[:100]}")
            print()

            # Verify feedback was injected into LLM context
            feedback_injected = json.loads(mock_llm.call_history[1][-1]["content"])
            print(f"  → Feedback injected into next LLM call:")
            print(f"     success: {feedback_injected['success']}")
            print(f"     error_type: {feedback_injected['error_type']}")
            print(f"     detail: {feedback_injected['detail'][:80]}...")
            print()

    print(f"Step {len(steps) + 1}:")
    print(f"  LLM Decision: {json.loads(responses[len(steps)])['action']}")
    print(f"  Reason:       {json.loads(responses[len(steps)])['reason']}")
    print()
    print(f"Result: {result.status.upper()} — {result.final_message}")
    print()


def demo_agent_loop(tmpdir):
    """
    Demo C: Agent Loop — DECIDE→ACT→OBSERVE 循环 + 停机条件
    展示完整循环和 max_steps 终止
    """
    ws = os.path.join(tmpdir, "loop")
    os.makedirs(ws)
    _make_ws(ws, {"main.py": "def add(a, b):\n    return a * b\n"})

    db_path = os.path.join(tmpdir, "loop.db")

    # Normal completion: read → write → done
    responses = [
        json.dumps({"action": "tool_call", "tool": "read_file", "params": {"path": "main.py"}}),
        json.dumps({"action": "tool_call", "tool": "write_file", "params": {"path": "main.py", "content": "def add(a, b):\n    return a + b\n"}}),
        json.dumps({"action": "done", "reason": "code fixed"}),
    ]

    mock_llm = MockLLMProvider(responses=responses)
    task_mgr = TaskManager(db_path, base_workspace=ws)
    loop = AgentLoop(
        llm=mock_llm,
        tool_registry=ToolRegistry(workspace=ws),
        feedback_analyzer=FeedbackAnalyzer(),
        task_mgr=task_mgr,
    )

    task_id = task_mgr.create_task("read and fix main.py")
    result = asyncio.run(loop.run(task_id, max_steps=10))

    print("=" * 60)
    print("  Demo C: Agent Loop — DECIDE → ACT → OBSERVE")
    print("=" * 60)
    print()
    print(f"Task: {task_mgr.get_task(task_id)['description']}")
    print(f"Max Steps: 10")
    print()

    steps = task_mgr.get_steps(task_id)
    for i, step in enumerate(steps):
        decision = json.loads(responses[i])
        print(f"Step {i + 1}:")
        print(f"  DECIDE:  LLM → {decision['action']} ({decision['tool'] if decision['action'] == 'tool_call' else '-'})")
        if decision["action"] == "tool_call":
            print(f"  ACT:     execute {decision['tool']}({json.dumps(decision['params'])})")
            print(f"  OBSERVE: tool returned, analyzing feedback")
            fb = FeedbackAnalyzer().analyze(
                asyncio.run(ToolRegistry(workspace=ws).get(decision['tool']).execute(decision['params']))
            )
            print(f"           feedback: success={fb.success} error_type={fb.error_type or 'none'}")
        print()

    print(f"Step {len(steps) + 1}:")
    print(f"  DECIDE:  LLM → done")
    print(f"  STOP:    Agent completed task")
    print()
    print(f"Result: {result.status.upper()} — {result.final_message}")
    print(f"Total Steps: {result.total_steps}")
    print()

    # Max steps demo
    print("-" * 60)
    print("  Demo C2: Stop Condition — Max Steps Reached")
    print("-" * 60)
    print()

    responses2 = [
        json.dumps({"action": "tool_call", "tool": "read_file", "params": {"path": "main.py"}})
    ] * 10
    mock_llm2 = MockLLMProvider(responses=responses2)
    task_mgr2 = TaskManager(os.path.join(tmpdir, "loop2.db"), base_workspace=ws)
    loop2 = AgentLoop(
        llm=mock_llm2,
        tool_registry=ToolRegistry(workspace=ws),
        feedback_analyzer=FeedbackAnalyzer(),
        task_mgr=task_mgr2,
    )

    task_id2 = task_mgr2.create_task("keep reading forever")
    result2 = asyncio.run(loop2.run(task_id2, max_steps=5))

    print(f"Task: {task_mgr2.get_task(task_id2)['description']}")
    print(f"Max Steps: 5")
    print(f"Agent called read_file {result2.total_steps} times but never finished")
    print()
    print(f"Result: {result2.status.upper()} — {result2.final_message}")
    print()


def main():
    tmpdir = tempfile.mkdtemp(prefix="harness_demo_")

    try:
        demo_governance(tmpdir)
        demo_feedback_loop(tmpdir)
        demo_agent_loop(tmpdir)
    finally:
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()