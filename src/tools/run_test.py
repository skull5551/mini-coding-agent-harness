from src.tools.base import BaseTool, ToolResult


class RunTestTool(BaseTool):
    async def execute(self, params: dict) -> ToolResult:
        from src.tools.execute_command import ExecuteCommandTool

        command = params.get("command", "")
        if not command:
            return ToolResult(stderr="no test command provided", exit_code=1)
        runner = ExecuteCommandTool(workspace=self.workspace)
        result = await runner.execute({"command": command})
        if result.exit_code != 0:
            summary = "test failure" if "fail" in result.stderr.lower() else "command error"
            return ToolResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
            )
        return result