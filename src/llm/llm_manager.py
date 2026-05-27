import logging
import urllib.error
import urllib.request

# BaseChatModel: common base for ChatOllama, ChatOpenAI, etc.
from langchain_core.language_models import BaseChatModel

# Base return type from .invoke() — covers AIMessage, HumanMessage, etc.
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langfuse import observe

from config import settings

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

    # Connection with providers
    @staticmethod
    def _is_host_reachable(host: str, timeout: float = 3.0) -> bool:
        """Check if a server is reachable by hitting its root endpoint."""
        try:
            urllib.request.urlopen(host, timeout=timeout)
            return True
        except (urllib.error.URLError, OSError, ValueError):
            return False

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
                logger.warning("Provider %s failed on ainvoke: %s", self.chat_provider_name, e)
                self.providers_errors[self.chat_provider_name] = str(e)
                self.chat_provider_name = None
                self.chat_model = None

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
                # checks that the provider has not given an invoke error then check is available
                if provider_name not in self.providers_errors and self._is_provider_available(provider_name, provider):
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
        if provider["type"] == "ollama":
            # Pass auth headers for Ollama Cloud
            if provider["api_key"]:
                kwargs["client_kwargs"] = {
                    "headers": {"Authorization": f"Bearer {provider['api_key']}"}
                }
            self.chat_model = ChatOllama(**kwargs)
        elif provider["type"] == "openai":
            kwargs["api_key"] = provider["api_key"]
            self.chat_model = ChatOpenAI(**kwargs)
        return self.chat_model

    # Calling the LLM
    @observe(name="llm_request", as_type="generation", capture_input=True, capture_output=True)
    async def chat(self, prompt, user_id) -> BaseMessage:
        """Send a prompt to the LLM and return the response.
        """
        response = await self._invoke_with_retry(prompt)
        return response
