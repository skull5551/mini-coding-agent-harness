from src.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    def __init__(self, responses: list[str]):
        if not responses:
            raise StopIteration("No responses configured")
        self.responses = responses
        self.call_count = 0
        self.call_history: list[list] = []

    def chat(self, messages: list) -> str:
        if self.call_count >= len(self.responses):
            raise StopIteration("MockLLMProvider exhausted")
        self.call_history.append(list(messages))
        response = self.responses[self.call_count]
        self.call_count += 1
        return response