# LangChain type alias: covers strings, message lists, and PromptValue
from langchain_core.language_models import LanguageModelInput

# Base return type from .invoke() — covers AIMessage, HumanMessage, etc.
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama
from langfuse import Langfuse, observe

from config import settings
from llm.ollama_helpers import get_available_ollama_host


def get_default_model(host: str) -> str:
    """Return the default model for the given host: local or remote."""
    if host == settings.ollama_host_local:
        return settings.local_llm
    return settings.remote_llm


def get_llm_client(model_name: str = "") -> ChatOllama:
    host = get_available_ollama_host()
    if not model_name:
        model_name = get_default_model(host)
    print(f"Using LLM {model_name} at {host}")
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
    langfuse_client = Langfuse()
    try:
        langfuse_client.update_current_trace(
            name=settings.app_name,
            user_id=user_id,
            metadata={"model": model_name, "provider": settings.provider},
        )
        response = llm.invoke(prompt)
        return response
    finally:
        langfuse_client.flush()
