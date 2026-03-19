import logging
import urllib.error
import urllib.request

from config import settings

logger = logging.getLogger(__name__)

def _is_host_reachable(host: str, timeout: float = 3.0) -> bool:
    """Check if a server is reachable by hitting its root endpoint."""
    try:
        urllib.request.urlopen(host, timeout=timeout)
        return True
    except (urllib.error.URLError, OSError, ValueError):
        return False


def select_llm_provider(provider_priority: list[str]) -> str:

    for provider_name in provider_priority:
        provider = settings.providers[provider_name]

        # Skip providers that need an API key but don't have one configured.
        # api_key=None means the provider doesn't need a key;
        # api_key="" means it needs one but it's missing.
        if provider["api_key"] is not None and not provider["api_key"]:
            logger.debug("Skipping %s: no API key configured", provider_name)
            continue

        # Check if provider is reachable
        if not _is_host_reachable(provider["url"]):
            logger.debug("Skipping %s: host unreachable at %s", provider_name, provider["url"])
            continue

        return provider_name

    raise ConnectionError(
        "No LLM provider available. Check your provider configuration and connectivity."
    )
