import os
import uuid

from src.state.manager import StateManager


class TaskManager:
    def __init__(self, db_path: str, base_workspace: str | None = None):
        self.state = StateManager(db_path)
        self.base_workspace = base_workspace or os.path.join(os.getcwd(), "workspaces")

    def create_task(self, description: str, max_steps: int = 20) -> str:
        task_id = self.state.create_task(description, max_steps)
        workspace_path = os.path.join(self.base_workspace, task_id)
        os.makedirs(workspace_path, exist_ok=True)
        conn = self.state.db.connect()
        conn.execute(
            "UPDATE tasks SET workspace_path = ? WHERE id = ?",
            (workspace_path, task_id),
        )
        conn.commit()
        return task_id

    def get_task(self, task_id: str) -> dict | None:
        return self.state.get_task(task_id)

    def list_tasks(self) -> list[dict]:
        return self.state.list_tasks()

    def start_task(self, task_id: str):
        self.state.update_task_status(task_id, "running")

    def complete_task(self, task_id: str):
        self.state.update_task_status(task_id, "success")

    def fail_task(self, task_id: str):
        self.state.update_task_status(task_id, "failed")

    def pause_task(self, task_id: str):
        self.state.update_task_status(task_id, "paused")

    def get_steps(self, task_id: str) -> list[dict]:
        return self.state.get_steps(task_id)

    def mark_step(self, task_id: str, action: str, input_summary: str = "", output_summary: str = "") -> str:
        task = self.state.get_task(task_id)
        steps = self.state.get_steps(task_id)
        step_number = len(steps) + 1
        return self.state.create_step(task_id, step_number, action, input_summary, output_summary)