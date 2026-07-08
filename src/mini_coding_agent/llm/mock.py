"""Mock LLM Provider — 用于确定性单元测试。

每次调用按预设顺序返回响应，不依赖网络与真实 LLM。
"""

import json
from typing import Any

from .base import LLMProvider, LLMResponse


class MockLLMExhaustedError(Exception):
    """Mock 响应耗尽时抛出的异常。"""

    pass


class MockLLMProvider(LLMProvider):
    """Mock LLM Provider。

    接受预设的响应序列，每次调用 chat() 依次返回下一个响应。
    响应耗尽后抛出 MockLLMExhaustedError。

    Attributes:
        responses: 预设响应列表，每个元素为 dict 或 str。
        call_count: 已调用次数。
        call_history: 完整调用历史，记录每次传入的 messages。
    """

    def __init__(self, responses: list[dict[str, Any] | str]):
        self.responses = responses
        self.call_count: int = 0
        self.call_history: list[list[dict[str, str]]] = []

    def chat(self, messages: list[dict[str, str]]) -> LLMResponse:
        """返回预设序列中的下一个响应。"""
        self.call_history.append(messages)

        if self.call_count >= len(self.responses):
            raise MockLLMExhaustedError(
                f"Mock 响应已耗尽（共 {len(self.responses)} 个响应，"
                f"已调用 {self.call_count} 次）"
            )

        response = self.responses[self.call_count]
        self.call_count += 1

        if isinstance(response, str):
            return LLMResponse(content=response)
        elif isinstance(response, dict):
            content = response.get("content", json.dumps(response))
            tool_calls = response.get("tool_calls")
            return LLMResponse(
                content=content,
                raw=response,
                token_usage=len(content) // 4,
            )
        else:
            return LLMResponse(content=str(response))

    def reset(self) -> None:
        """重置响应计数到初始状态。"""
        self.call_count = 0
        self.call_history.clear()