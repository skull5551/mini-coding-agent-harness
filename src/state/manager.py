import uuid
from datetime import datetime, timezone

from src.state.database import Database
from src.state.models import CREATE_TABLES


class StateManager:
    def __init__(self, db_path: str):
        self.db = Database(db_path)
        self._init_db()

    def _init_db(self):
        conn = self.db.connect()
        conn.executescript(CREATE_TABLES)
        conn.commit()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # --- Task CRUD ---

    def create_task(self, description: str, max_steps: int = 20) -> str:
        task_id = str(uuid.uuid4())
        now = self._now()
        conn = self.db.connect()
        conn.execute(
            "INSERT INTO tasks (id, description, status, max_steps, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (task_id, description, "pending", max_steps, now, now),
        )
        conn.commit()
        return task_id

    def get_task(self, task_id: str) -> dict | None:
        conn = self.db.connect()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            return None
        return dict(row)

    def update_task_workspace(self, task_id: str, workspace_path: str):
        conn = self.db.connect()
        conn.execute(
            "UPDATE tasks SET workspace_path = ? WHERE id = ?",
            (workspace_path, task_id),
        )
        conn.commit()

    def update_task_status(self, task_id: str, status: str):
        now = self._now()
        conn = self.db.connect()
        conn.execute(
            "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, task_id),
        )
        conn.commit()

    def list_tasks(self) -> list[dict]:
        conn = self.db.connect()
        rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    # --- Step CRUD ---

    def create_step(self, task_id: str, step_number: int, action: str, input_summary: str = "", output_summary: str = "") -> str:
        step_id = str(uuid.uuid4())
        now = self._now()
        conn = self.db.connect()
        conn.execute(
            "INSERT INTO execution_steps (id, task_id, step_number, action, input_summary, output_summary, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (step_id, task_id, step_number, action, input_summary, output_summary, now),
        )
        conn.commit()
        return step_id

    def get_steps(self, task_id: str) -> list[dict]:
        conn = self.db.connect()
        rows = conn.execute(
            "SELECT * FROM execution_steps WHERE task_id = ? ORDER BY step_number",
            (task_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- ToolCall CRUD ---

    def create_tool_call(self, task_id: str, step_id: str, tool_name: str, tool_input: str = "", tool_output: str = "", exit_code: int = 0, status: str = "success") -> str:
        call_id = str(uuid.uuid4())
        conn = self.db.connect()
        conn.execute(
            "INSERT INTO tool_calls (id, task_id, step_id, tool_name, input, output, exit_code, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (call_id, task_id, step_id, tool_name, tool_input, tool_output, exit_code, status),
        )
        conn.commit()
        return call_id

    def get_tool_calls(self, task_id: str) -> list[dict]:
        conn = self.db.connect()
        rows = conn.execute(
            "SELECT * FROM tool_calls WHERE task_id = ? ORDER BY rowid",
            (task_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- ApiKey CRUD ---

    def save_api_key(self, provider: str, key_masked: str):
        conn = self.db.connect()
        existing = conn.execute(
            "SELECT id FROM api_keys WHERE provider = ?", (provider,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE api_keys SET key_masked = ? WHERE provider = ?",
                (key_masked, provider),
            )
        else:
            key_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO api_keys (id, provider, key_masked) VALUES (?, ?, ?)",
                (key_id, provider, key_masked),
            )
        conn.commit()

    def get_api_keys(self) -> list[dict]:
        conn = self.db.connect()
        rows = conn.execute("SELECT * FROM api_keys").fetchall()
        return [dict(r) for r in rows]

    def delete_api_key(self, provider: str):
        conn = self.db.connect()
        conn.execute("DELETE FROM api_keys WHERE provider = ?", (provider,))
        conn.commit()