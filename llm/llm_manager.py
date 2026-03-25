import logging
import urllib.error
import urllib.request

# BaseChatModel: common base for ChatOllama, ChatOpenAI, etc.
from langchain_core.language_models import BaseChatModel

# Base return type from .invoke() — covers AIMessage, HumanMessage, etc.
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langfuse import observe

from config import settings
from llm.langfuse_helpers import create_langfuse_client, update_and_flush_trace

logger = logging.getLogger(__name__)


class LLM_Client:
    def __init__(self):
        # Set after a successful chat() call to the provider that worked.
        # None means no successful call has been made yet.
        self.embeddings_provider_name = None
        self.embeddings_model = None
        self.chat_provider_name = None
        self.chat_model = None
        self.providers_errors = {}
        self.connection_attempts = 0
        self.max_attempts = len(settings.providers) * 3
        self.langfuse_client = create_langfuse_client()

    # Connection with providers
    @staticmethod
    def _is_host_reachable(host: str, timeout: float = 3.0) -> bool:
        """Check if a server is reachable by hitting its root endpoint."""
        try:
            urllib.request.urlopen(host, timeout=timeout)
            return True
        except (urllib.error.URLError, OSError, ValueError):
            return False

    def _mark_provider_failed(self, error):
        """Log the failure, record the error, and reset so the next iteration picks a new provider."""
        logger.warning("Provider %s failed on ainvoke: %s", self.chat_provider_name, error)
        self.providers_errors[self.chat_provider_name] = str(error)
        self.chat_provider_name = None
        self.chat_model = None

    async def _invoke_with_retry(self, prompt) -> BaseMessage:
        """Try each provider in priority order until one succeeds.
        If ainvoke() fails on one provider, tries the next.
        Raises ConnectionError if all providers are exhausted.
        """
        while True:
            try:
                if not self.chat_model:
                    self.get_chat_model()
                return await self.chat_model.ainvoke(prompt)
            # ConnectionError from _select_provider means all providers are exhausted.
            except ConnectionError:
                raise
            except Exception as e:
                self._mark_provider_failed(e)

    def has_provider_failed(self, provider_name) -> bool:
        return provider_name in self.providers_errors

    def _select_provider(self, model_type) -> str:
        """Return the first reachable provider for the given model type.

        model_type: "chat" or "embeddings"
        """
        if model_type == "chat":
            priority_list = settings.chat_provider_priority
        else:
            priority_list = settings.embeddings_provider_priority

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

    # Getting the models from the providers
    def get_embeddings_model(self):
        """Return an embeddings model from the first available embeddings provider."""
        if not self.embeddings_model:
            self.embeddings_provider_name = self._select_provider("embeddings")
            provider = settings.providers[self.embeddings_provider_name]
            self.embeddings_model = OllamaEmbeddings(
                model=settings.embeddings_model, base_url=provider["url"]
            )
            logger.info(
                "Using embedding model %s on %s (%s)",
                settings.embeddings_model,
                self.embeddings_provider_name,
                provider["url"],
            )
        return self.embeddings_model

    def get_chat_model(self) -> BaseChatModel:
        self.chat_provider_name = self._select_provider("chat")
        provider = settings.providers[self.chat_provider_name]
        logger.info(
            "Using LLM chat model %s on %s (%s)",
            provider["chat_model"],
            self.chat_provider_name,
            provider["url"],
        )
        kwargs: dict = {
            "model": provider["chat_model"],
            "base_url": provider["url"],
        }
        # Pass auth headers for cloud providers (e.g., Ollama Cloud)
        if provider["api_key"]:
            kwargs["client_kwargs"] = {
                "headers": {"Authorization": f"Bearer {provider['api_key']}"}
            }
        self.chat_model = ChatOllama(**kwargs)
        return self.chat_model

    # Langfuse
    def _send_trace(self, user_id, type="chat"):
        if self.langfuse_client:
            if type == "chat":
                model = self.chat_model.model
                provider = self.chat_provider_name
            else:
                model = self.embeddings_model.model
                provider = self.embeddings_provider_name
            update_and_flush_trace(self.langfuse_client, user_id, model, provider)

    # Calling the LLM
    @observe(name="ollama_request", as_type="generation", capture_input=True, capture_output=True)
    async def chat(self, prompt, user_id) -> BaseMessage:
        """Send a prompt to the LLM and return the response.
        """
        response = await self._invoke_with_retry(prompt)
        self._send_trace(user_id)
        return response
