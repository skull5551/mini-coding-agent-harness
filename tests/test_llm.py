import pytest
from src.llm.base import LLMProvider
from src.llm.mock import MockLLMProvider


def test_llm_provider_is_abstract():
    with pytest.raises(TypeError):
        LLMProvider()


def test_mock_llm_returns_preset_responses():
    provider = MockLLMProvider(responses=["tool: read_file", "tool: write_file"])
    assert provider.chat([]) == "tool: read_file"
    assert provider.chat([]) == "tool: write_file"


def test_mock_llm_exhausted_raises():
    provider = MockLLMProvider(responses=["only one"])
    provider.chat([])
    with pytest.raises(StopIteration):
        provider.chat([])


def test_mock_llm_resets_call_count():
    provider = MockLLMProvider(responses=["a", "b"])
    provider.chat([])
    provider.chat([])
    with pytest.raises(StopIteration):
        provider.chat([])


def test_mock_llm_empty_responses_raises_immediately():
    with pytest.raises(StopIteration):
        provider = MockLLMProvider(responses=[])
        provider.chat([])