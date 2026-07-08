import json
import logging

from src.agent.models import AgentDecision, AgentResult
from src.feedback.analyzer import FeedbackAnalyzer
from src.llm.base import LLMProvider
from src.task.manager import TaskManager
from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class AgentLoop:
    def __init__(
        self,
        llm: LLMProvider,
        tool_registry: ToolRegistry,
        feedback_analyzer: FeedbackAnalyzer,
        task_mgr: TaskManager,
    ):
        self.llm = llm
        self.tool_registry = tool_registry
        self.feedback_analyzer = feedback_analyzer
        self.task_mgr = task_mgr

    def _build_system_prompt(self) -> str:
        tools = self.tool_registry.list_tools()
        return (
            "You are a coding agent. You have access to the following tools:\n"
            + "\n".join(f"- {t}" for t in tools)
            + "\n\nRespond with JSON in one of these formats:\n"
            + '{"action": "tool_call", "tool": "<name>", "params": {...}}\n'
            + '{"action": "done", "reason": "..."}\n'
            + '{"action": "failed", "reason": "..."}'
        )

    def _parse_decision(self, response: str) -> AgentDecision:
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            return AgentDecision(action="failed", reason="invalid JSON from LLM")
        action = data.get("action", "")
        if action == "tool_call":
            return AgentDecision(
                action="tool_call",
                tool=data.get("tool", ""),
                params=data.get("params", {}),
            )
        if action == "done":
            return AgentDecision(action="done", reason=data.get("reason", ""))
        if action == "failed":
            return AgentDecision(action="failed", reason=data.get("reason", ""))
        return AgentDecision(action="failed", reason=f"unknown action: {action}")

    async def run(self, task_id: str, max_steps: int = 20) -> AgentResult:
        task = self.task_mgr.get_task(task_id)
        if task is None:
            return AgentResult(task_id=task_id, status="failed", total_steps=0, final_message="task not found")

        self.task_mgr.start_task(task_id)
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": f"Task: {task['description']}"},
        ]

        for step in range(1, max_steps + 1):
            try:
                response = self.llm.chat(messages)
            except StopIteration:
                return AgentResult(task_id=task_id, status="failed", total_steps=step - 1, final_message="LLM exhausted")

            decision = self._parse_decision(response)

            if decision.action == "done":
                self.task_mgr.complete_task(task_id)
                return AgentResult(task_id=task_id, status="success", total_steps=step, final_message=decision.reason)

            if decision.action == "failed":
                self.task_mgr.fail_task(task_id)
                return AgentResult(task_id=task_id, status="failed", total_steps=step, final_message=decision.reason)

            if decision.action == "tool_call":
                try:
                    tool = self.tool_registry.get(decision.tool)
                except KeyError:
                    error_msg = f"unknown tool: {decision.tool}"
                    messages.append({"role": "assistant", "content": response})
                    messages.append({"role": "user", "content": error_msg})
                    self.task_mgr.mark_step(task_id, action=decision.tool, input_summary=str(decision.params), output_summary=error_msg)
                    continue

                result = await tool.execute(decision.params)
                feedback = self.feedback_analyzer.analyze(result)

                self.task_mgr.mark_step(
                    task_id,
                    action=decision.tool,
                    input_summary=str(decision.params),
                    output_summary=result.stdout[:200] + result.stderr[:200],
                )

                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": json.dumps({
                        "success": feedback.success,
                        "error_type": feedback.error_type,
                        "detail": feedback.detail,
                        "stdout": result.stdout[:500],
                        "stderr": result.stderr[:500],
                    }),
                })

        self.task_mgr.fail_task(task_id)
        return AgentResult(task_id=task_id, status="failed", total_steps=max_steps, final_message="max steps reached")