import pytest
from unittest.mock import patch, MagicMock
from src.llm.litellm_provider import LiteLLMProvider


def test_litellm_provider_initialization():
    provider = LiteLLMProvider(model="gpt-4o", api_key="sk-test")
    assert provider.model == "gpt-4o"
    assert provider.api_key == "sk-test"


def test_litellm_provider_default_model():
    provider = LiteLLMProvider(api_key="sk-test")
    assert provider.model == "gpt-4o"


@patch("src.llm.litellm_provider.litellm")
def test_litellm_provider_chat_success(mock_litellm):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Hello!"
    mock_litellm.completion.return_value = mock_response

    provider = LiteLLMProvider(model="gpt-4o", api_key="sk-test")
    result = provider.chat([{"role": "user", "content": "Say hello"}])

    assert result == "Hello!"
    mock_litellm.completion.assert_called_once()
    call_kwargs = mock_litellm.completion.call_args[1]
    assert call_kwargs["model"] == "gpt-4o"
    assert call_kwargs["messages"] == [{"role": "user", "content": "Say hello"}]


@patch("src.llm.litellm_provider.litellm")
def test_litellm_provider_chat_with_system_message(mock_litellm):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Understood"
    mock_litellm.completion.return_value = mock_response

    provider = LiteLLMProvider(model="gpt-4o", api_key="sk-test")
    messages = [
        {"role": "system", "content": "You are a coding agent"},
        {"role": "user", "content": "Fix the bug"},
    ]
    result = provider.chat(messages)
    assert result == "Understood"
    assert mock_litellm.completion.call_args[1]["messages"] == messages


@patch("src.llm.litellm_provider.litellm")
def test_litellm_provider_api_error(mock_litellm):
    mock_litellm.completion.side_effect = Exception("AuthenticationError: Invalid API key")

    provider = LiteLLMProvider(model="gpt-4o", api_key="sk-bad")
    with pytest.raises(Exception, match="AuthenticationError"):
        provider.chat([{"role": "user", "content": "hi"}])


@patch("src.llm.litellm_provider.litellm")
def test_litellm_provider_rate_limit(mock_litellm):
    mock_litellm.completion.side_effect = Exception("RateLimitError: Rate limited")

    provider = LiteLLMProvider(model="gpt-4o", api_key="sk-test")
    with pytest.raises(Exception, match="RateLimitError"):
        provider.chat([{"role": "user", "content": "hi"}])


@patch("src.llm.litellm_provider.litellm")
def test_litellm_provider_empty_response(mock_litellm):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = ""
    mock_litellm.completion.return_value = mock_response

    provider = LiteLLMProvider(model="gpt-4o", api_key="sk-test")
    result = provider.chat([{"role": "user", "content": "say nothing"}])
    assert result == ""


@patch("src.llm.litellm_provider.litellm")
def test_litellm_provider_custom_model(mock_litellm):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "ok"
    mock_litellm.completion.return_value = mock_response

    provider = LiteLLMProvider(model="anthropic/claude-3-haiku", api_key="sk-test")
    provider.chat([{"role": "user", "content": "hi"}])
    assert mock_litellm.completion.call_args[1]["model"] == "anthropic/claude-3-haiku"