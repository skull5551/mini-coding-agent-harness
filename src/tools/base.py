from dataclasses import dataclass


@dataclass
class ToolResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0

    @property
    def success(self) -> bool:
        return self.exit_code == 0


class BaseTool:
    def __init__(self, workspace: str):
        self.workspace = workspace

    async def execute(self, params: dict) -> ToolResult:
        raise NotImplementedError