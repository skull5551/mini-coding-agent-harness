from src.llm.base import LLMProvider

try:
    import litellm
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False


class LiteLLMProvider(LLMProvider):
    def __init__(self, model: str = "gpt-4o", api_key: str = ""):
        self.model = model
        self.api_key = api_key

    def chat(self, messages: list) -> str:
        if not HAS_LITELLM:
            raise RuntimeError(
                "litellm is required but not available. "
                "Install it with: pip install 'litellm'"
            )
        response = litellm.completion(
            model=self.model,
            messages=messages,
            api_key=self.api_key or None,
        )
        return response.choices[0].message.content