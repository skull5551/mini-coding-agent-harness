import asyncio

from src.tools.base import BaseTool, ToolResult

_COMMAND_TIMEOUT = 120


class ExecuteCommandTool(BaseTool):
    async def execute(self, params: dict) -> ToolResult:
        command = params.get("command", "")
        if not command:
            return ToolResult(stderr="no command provided", exit_code=1)
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=_COMMAND_TIMEOUT
            )
            return ToolResult(
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
            )
        except asyncio.TimeoutError:
            proc.kill()
            return ToolResult(stderr="command timed out", exit_code=124)
        except Exception as e:
            return ToolResult(stderr=str(e), exit_code=1)