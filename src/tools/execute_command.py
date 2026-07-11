import asyncio
import re

from src.tools.base import BaseTool, ToolResult

_COMMAND_TIMEOUT = 120

_DANGEROUS_COMMAND_PATTERNS = [
    (re.compile(r'rm\s+-[rf]+', re.IGNORECASE), "rm -rf / -fr"),
    (re.compile(r'curl\s+.*\|\s*sh', re.IGNORECASE), "curl | sh"),
    (re.compile(r'wget\s+.*\|\s*sh', re.IGNORECASE), "wget | sh"),
]


def _is_safe_command(command: str) -> bool:
    for pattern, _name in _DANGEROUS_COMMAND_PATTERNS:
        if pattern.search(command):
            return False
    return True


class ExecuteCommandTool(BaseTool):
    async def execute(self, params: dict) -> ToolResult:
        command = params.get("command", "")
        if not command:
            return ToolResult(stderr="no command provided", exit_code=1)
        if not _is_safe_command(command):
            return ToolResult(stderr="dangerous command blocked", exit_code=1)
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