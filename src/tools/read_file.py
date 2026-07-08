from src.tools.base import BaseTool, ToolResult
from src.tools.utils import _is_safe_path, _resolve_path


class ReadFileTool(BaseTool):
    async def execute(self, params: dict) -> ToolResult:
        path = params.get("path", "")
        if not _is_safe_path(self.workspace, path):
            return ToolResult(stderr="path traversal detected", exit_code=1)
        full_path = _resolve_path(self.workspace, path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return ToolResult(stdout=content, exit_code=0)
        except Exception as e:
            return ToolResult(stderr=str(e), exit_code=1)