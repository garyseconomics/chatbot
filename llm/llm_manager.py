import logging
import urllib.error
import urllib.request

# BaseChatModel: common base for ChatOllama, ChatOpenAI, etc.
from langchain_core.language_models import BaseChatModel

# Base return type from .invoke() — covers AIMessage, HumanMessage, etc.
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langfuse import Langfuse, observe

from config import settings

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


class LLM_Client:
    def __init__(self):
        # Set after a successful chat() call to the provider that worked.
        # None means no successful call has been made yet.
        self.provider_name: str | None = None
        self.providers_errors = {}
        self.connection_attempts = 0
        self.max_attempts = len(settings.providers) * 3

    @observe(name="ollama_request", as_type="generation", capture_input=True, capture_output=True)
    async def chat(self, prompt, user_id) -> BaseMessage:
        """Send a prompt to the LLM and return the response.

        Tries each reachable chat provider in priority order.
        If ainvoke() fails on one provider, tries the next.
        """
        # Loop until a provider succeeds or _select_provider raises ConnectionError
        while True:
            self.provider_name = self._select_provider("chat")

            try:
                llm = self._create_chat_client()
                langfuse_client = get_langfuse_client()
                langfuse_client.update_current_trace(
                    name=settings.app_name,
                    user_id=user_id,
                    metadata={"model": llm.model, "provider": self.provider_name},
                )
                response = await llm.ainvoke(prompt)
                langfuse_client.flush()
                return response
            except Exception as e:
                logger.warning("Provider %s failed on ainvoke: %s", self.provider_name, e)
                self.providers_errors[self.provider_name] = str(e)
                self.provider_name = None

    def get_embedding_model(self):
        """Return an embedding model from the first available embedding provider."""
        provider_name = self._select_provider("embeddings")
        provider = settings.providers[provider_name]
        logger.info(
            "Using embedding model %s on %s (%s)",
            settings.embedding_model,
            provider_name,
            provider["url"],
        )
        return OllamaEmbeddings(model=settings.embedding_model, base_url=provider["url"])

    @property
    def chat_model(self) -> str | None:
        """Return the chat model name of the provider that handled the last request."""
        if self.provider_name is None:
            return None
        return settings.providers[self.provider_name]["chat_model"]

    def has_provider_failed(self, provider_name) -> bool:
        return provider_name in self.providers_errors

    def _select_provider(self, model_type) -> str:
        """Return the first reachable provider for the given model type.

        model_type: "chat" or "embeddings"
        """
        if model_type == "chat":
            priority_list = settings.chat_provider_priority
        else:
            priority_list = settings.embedding_provider_priority

        while True:
            for provider_name in priority_list:
                self.connection_attempts += 1
                provider = settings.providers[provider_name]
                # Checks if this provider is available, store error if it fails
                self._is_provider_available(provider_name, provider)
                if not self.has_provider_failed(provider_name):
                    return provider_name
            # Tried all providers, none worked — check if we can retry
            if self.connection_attempts >= self.max_attempts:
                raise ConnectionError(f"No LLM provider available. Errors: {self.providers_errors}")
            # Still have attempts left — reset errors and try again
            self.providers_errors = {}

    def _is_provider_available(self, provider_name, provider) -> bool:
        """Check if a provider is configured and reachable."""
        # Skip providers that need an API key but don't have one configured.
        # api_key=None means the provider doesn't need a key;
        # api_key="" means it needs one but it's missing.
        if provider["api_key"] is not None and not provider["api_key"]:
            self.providers_errors[provider_name] = "No API key configured"
            logger.debug("Skipping %s: no API key configured", provider_name)
            return False

        if not self._is_host_reachable(provider["url"]):
            self.providers_errors[provider_name] = "Host unreachable"
            logger.debug("Skipping %s: host unreachable at %s", provider_name, provider["url"])
            return False

        return True

    def _create_chat_client(self) -> BaseChatModel:
        provider = settings.providers[self.provider_name]
        logger.info(
            "Using LLM chat model %s on %s (%s)",
            provider["chat_model"],
            self.provider_name,
            provider["url"],
        )
        kwargs: dict = {
            "model": provider["chat_model"],
            "base_url": provider["url"],
            "num_predict": settings.max_tokens,
        }
        # Pass auth headers for cloud providers (e.g., Ollama Cloud)
        if provider["api_key"]:
            kwargs["client_kwargs"] = {
                "headers": {"Authorization": f"Bearer {provider['api_key']}"}
            }
        return ChatOllama(**kwargs)

    @staticmethod
    def _is_host_reachable(host: str, timeout: float = 3.0) -> bool:
        """Check if a server is reachable by hitting its root endpoint."""
        try:
            urllib.request.urlopen(host, timeout=timeout)
            return True
        except (urllib.error.URLError, OSError, ValueError):
            return False
