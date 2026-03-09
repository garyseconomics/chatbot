import urllib.error
import urllib.request

from config import settings


def _is_host_reachable(host: str, timeout: float = 3.0) -> bool:
    """Check if an Ollama server is reachable by hitting its root endpoint."""
    try:
        urllib.request.urlopen(host, timeout=timeout)
        return True
    except (urllib.error.URLError, OSError):
        return False


def get_available_ollama_host() -> str:
    """Return the best available Ollama host: remote if reachable, otherwise local."""
    if settings.ollama_host_remote and _is_host_reachable(settings.ollama_host_remote):
        print(f"Using remote Ollama at {settings.ollama_host_remote}")
        return settings.ollama_host_remote

    print(f"Remote Ollama not available, using local at {settings.ollama_host_local}")
    return settings.ollama_host_local
