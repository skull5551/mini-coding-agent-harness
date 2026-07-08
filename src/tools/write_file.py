import os

from src.tools.base import BaseTool, ToolResult
from src.tools.utils import _is_safe_path, _resolve_path


class WriteFileTool(BaseTool):
    async def execute(self, params: dict) -> ToolResult:
        path = params.get("path", "")
        content = params.get("content", "")
        if not _is_safe_path(self.workspace, path):
            return ToolResult(stderr="path traversal detected", exit_code=1)
        full_path = _resolve_path(self.workspace, path)
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(stdout=f"written {len(content)} bytes", exit_code=0)
        except Exception as e:
            return ToolResult(stderr=str(e), exit_code=1)