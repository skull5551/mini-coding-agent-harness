from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.agent.loop import AgentLoop
from src.feedback.analyzer import FeedbackAnalyzer
from src.llm.litellm_provider import LiteLLMProvider
from src.task.manager import TaskManager
from src.tools.registry import ToolRegistry

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class CreateTaskRequest(BaseModel):
    description: str


_task_mgr: TaskManager | None = None


def init(task_mgr: TaskManager):
    global _task_mgr
    _task_mgr = task_mgr


@router.post("")
def create_task(body: CreateTaskRequest):
    task_id = _task_mgr.create_task(body.description)
    task = _task_mgr.get_task(task_id)
    return {"task_id": task_id, "status": task["status"]}


@router.get("")
def list_tasks():
    return _task_mgr.list_tasks()


@router.get("/{task_id}")
def get_task(task_id: str):
    task = _task_mgr.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@router.get("/{task_id}/steps")
def get_task_steps(task_id: str):
    task = _task_mgr.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return _task_mgr.get_steps(task_id)


class RunTaskRequest(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o"


@router.post("/{task_id}/run")
async def run_task(task_id: str, body: RunTaskRequest = RunTaskRequest()):
    task = _task_mgr.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")

    from src.llm import litellm_provider
    if litellm_provider.litellm is None:
        raise HTTPException(status_code=500, detail="litellm is required but not installed")

    api_key = _task_mgr.state.get_api_key(body.provider)
    if not api_key:
        raise HTTPException(status_code=400, detail=f"No API key configured for provider '{body.provider}'")

    llm = LiteLLMProvider(model=body.model, api_key=api_key)
    tool_registry = ToolRegistry(workspace=task["workspace_path"])
    feedback_analyzer = FeedbackAnalyzer()
    loop = AgentLoop(
        llm=llm,
        tool_registry=tool_registry,
        feedback_analyzer=feedback_analyzer,
        task_mgr=_task_mgr,
    )

    result = await loop.run(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "total_steps": result.total_steps,
        "final_message": result.final_message,
    }