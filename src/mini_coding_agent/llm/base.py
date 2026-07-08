"""LLM Provider 抽象接口。

定义统一的 LLM 调用接口，所有 Provider（Mock、OpenAI、Claude 等）必须实现此接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    """LLM 返回的响应结果。"""

    content: str
    """LLM 返回的文本内容（决策/工具调用指令）。"""

    raw: dict[str, Any] = field(default_factory=dict)
    """原始 API 响应（调试用）。"""

    token_usage: int = 0
    """本次调用消耗的 token 数。"""


class LLMProvider(ABC):
    """LLM Provider 抽象基类。

    定义了统一的 chat 接口，所有实现必须覆盖此方法。
    """

    @abstractmethod
    def chat(self, messages: list[dict[str, str]]) -> LLMResponse:
        """发送消息并获取 LLM 响应。

        Args:
            messages: 消息列表，格式为 [{"role": "system"|"user"|"assistant", "content": "..."}]

        Returns:
            LLMResponse 包含 LLM 的文本响应。
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """重置 Provider 的状态（如 Mock 的响应计数）。"""
        ...