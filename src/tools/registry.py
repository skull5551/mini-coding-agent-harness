from src.tools.base import BaseTool, ToolResult


class ToolRegistry:
    def __init__(self, workspace: str):
        self._tools: dict[str, BaseTool] = {}
        self._register_builtins(workspace)

    def _register_builtins(self, workspace: str):
        from src.tools.read_file import ReadFileTool
        from src.tools.write_file import WriteFileTool
        from src.tools.execute_command import ExecuteCommandTool
        from src.tools.run_test import RunTestTool

        self.register("read_file", ReadFileTool(workspace))
        self.register("write_file", WriteFileTool(workspace))
        self.register("execute_command", ExecuteCommandTool(workspace))
        self.register("run_test", RunTestTool(workspace))

    def register(self, name: str, tool: BaseTool):
        self._tools[name] = tool

    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise KeyError(f"unknown tool: {name}")
        return self._tools[name]

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())