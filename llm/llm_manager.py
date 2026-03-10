import logging

# LangChain type alias: covers strings, message lists, and PromptValue
from langchain_core.language_models import LanguageModelInput

# Base return type from .invoke() — covers AIMessage, HumanMessage, etc.
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama
from langfuse import Langfuse, observe

from config import settings
from llm.ollama_helpers import get_available_ollama_host

logger = logging.getLogger(__name__)


# Lazy singleton: created on first use, reused across all calls.
_langfuse_client: Langfuse | None = None


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


def get_default_model(host: str) -> str:
    """Return the default model for the given host: local or remote."""
    if host == settings.ollama_host_local:
        return settings.local_llm
    return settings.remote_llm


def get_llm_client(model_name: str = "") -> ChatOllama:
    host = get_available_ollama_host()
    if not model_name:
        model_name = get_default_model(host)
    logger.info("Using LLM %s at %s", model_name, host)
    return ChatOllama(model=model_name, base_url=host)


@observe(name="ollama_request", as_type="generation", capture_input=True, capture_output=True)
def llm_chat(
    prompt: LanguageModelInput,
    llm: ChatOllama | None = None,
    model_name: str = "",
    user_id: str = "not defined",
) -> BaseMessage:
    if not llm:
        llm = get_llm_client(model_name=model_name)
    client = get_langfuse_client()
    client.update_current_trace(
        name=settings.app_name,
        user_id=user_id,
        # Use llm.model instead of model_name param — it always has the
        # resolved model name, even when the caller doesn't pass one.
        metadata={"model": llm.model, "provider": settings.provider},
    )
    response = llm.invoke(prompt)
    client.flush()
    return response
