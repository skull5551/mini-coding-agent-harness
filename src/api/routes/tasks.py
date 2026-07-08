from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.task.manager import TaskManager

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