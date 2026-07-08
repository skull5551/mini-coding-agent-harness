from dataclasses import dataclass, field


@dataclass
class AgentDecision:
    action: str  # "tool_call", "done", "failed"
    tool: str = ""
    params: dict = field(default_factory=dict)
    reason: str = ""


@dataclass
class AgentResult:
    task_id: str
    status: str  # "success", "failed", "paused"
    total_steps: int
    final_message: str = ""