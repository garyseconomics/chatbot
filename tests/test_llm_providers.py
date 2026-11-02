import warnings

import langchain_core
import pytest

from config import settings
from llm.llm_manager import LLM_Client

# Read when pytest imports this file, before any test changes settings.chat_provider_priority.
CHAT_PROVIDERS = settings.chat_provider_priority.copy()


def configuration_problem(provider) -> str:
    """Return what's missing in a provider's settings, or "" if nothing is."""
    if not provider["url"]:
        return "no url"
    if not provider["chat_model"]:
        return "no chat model"
    # api_key="" means the provider needs a key but it's missing.
    if provider["api_key"] == "":
        return "no API key"
    return ""


def failure_message(name, error) -> str:
    message = f"Chat provider {name} failed: {error}"
    # Both ollama.ResponseError and openai.APIStatusError carry the HTTP status code.
    status = getattr(error, "status_code", None)
    if status and status >= 500:
        message += f" (HTTP {status}: the LLM provider's server failed)"
    return message


@pytest.mark.asyncio
async def test_all_chat_providers_answer(monkeypatch):
    """Send "hi" to every provider in the chat priority list.

    A provider that isn't configured or reachable on this machine only gives a warning.
    A provider that is configured and reachable but doesn't answer fails the test.
    """
    for name in CHAT_PROVIDERS:
        provider = settings.providers[name]

        problem = configuration_problem(provider)
        if problem:
            warnings.warn(f"Chat provider {name} is not configured: {problem}")
            continue
        if not LLM_Client._is_host_reachable(provider["url"]):
            warnings.warn(f"Chat provider {name} is not reachable at {provider['url']}")
            continue

        # Use only this provider, so a failure can't be hidden by the fallback.
        # monkeypatch puts the original priority list back after the test.
        monkeypatch.setattr(settings, "chat_provider_priority", [name])
        chat_model = LLM_Client().get_chat_model()
        try:
            response = await chat_model.ainvoke("hi")
        except Exception as error:
            pytest.fail(failure_message(name, error))

        assert isinstance(response, langchain_core.messages.ai.AIMessage), name
        assert response.content, f"Chat provider {name} returned an empty answer"
