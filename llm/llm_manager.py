import logging

# BaseChatModel: common base for ChatOllama, ChatOpenAI, etc.
from langchain_core.language_models import BaseChatModel

# Base return type from .invoke() — covers AIMessage, HumanMessage, etc.
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama
from langfuse import Langfuse, observe

from config import settings
from llm.llm_providers_helpers import select_llm_provider

logger = logging.getLogger(__name__)


# Lazy singleton: created on first use, reused across all calls.
_langfuse_client: Langfuse | None = None

# Tracks the provider selected by get_llm_client(), used in Langfuse metadata.
_provider_name: str = ""


def get_langfuse_client() -> Langfuse:
    """Return the shared Langfuse client, creating it on first use.
    Raises ValueError if credentials are not configured.
    """
    global _langfuse_client
    if _langfuse_client is None:
        if not settings.langfuse_public_key or not settings.langfuse_secret_key:
            raise ValueError(
                "Langfuse credentials are not configured. "
                "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env"
            )
        _langfuse_client = Langfuse()
    return _langfuse_client


def get_llm_client() -> BaseChatModel:
    """Return an LLM client from the first available provider in the priority list.

    Iterates through chat_provider_priority, skipping providers that are not reachable.
    Raises ConnectionError if none are available.
    """
    global _provider_name
    _provider_name = select_llm_provider(settings.chat_provider_priority)
    provider = settings.providers[_provider_name]
    logger.info(
        "Using LLM chat model %s on %s (%s)",
        provider["chat_model"], _provider_name, provider["url"],
    )

    kwargs: dict = {"model": provider["chat_model"], "base_url": provider["url"]}
    # Pass auth headers for cloud providers (e.g., Ollama Cloud)
    if provider["api_key"]:
        kwargs["client_kwargs"] = {
            "headers": {"Authorization": f"Bearer {provider['api_key']}"}
        }
    return ChatOllama(**kwargs)


@observe(name="ollama_request", as_type="generation", capture_input=True, capture_output=True)
def llm_chat(prompt, llm=None, user_id="tests") -> BaseMessage:
    if not llm:
        llm = get_llm_client()
    client = get_langfuse_client()
    client.update_current_trace(
        name=settings.app_name,
        user_id=user_id,
        metadata={"model": llm.model, "provider": _provider_name},
    )
    response = llm.invoke(prompt)
    client.flush()
    return response
