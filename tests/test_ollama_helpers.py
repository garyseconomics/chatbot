import urllib.error
from unittest.mock import patch

from config import settings
from ollama_helpers import _is_host_reachable, get_available_ollama_host


# --- _is_host_reachable tests ---
# These mock urllib.request.urlopen to avoid real network calls.
# We test the three outcomes: success, URL error (bad host), and OS error (refused).


def test_is_host_reachable_returns_true_on_success():
    # When urlopen succeeds, the host is reachable
    with patch("ollama_helpers.urllib.request.urlopen"):
        assert _is_host_reachable("http://localhost:11434") is True


def test_is_host_reachable_returns_false_on_url_error():
    # URLError happens when the host can't be resolved (e.g. bad hostname)
    with patch(
        "ollama_helpers.urllib.request.urlopen",
        side_effect=urllib.error.URLError("unreachable"),
    ):
        assert _is_host_reachable("http://localhost:11434") is False


def test_is_host_reachable_returns_false_on_os_error():
    # OSError happens when the connection is refused (e.g. server not running)
    with patch(
        "ollama_helpers.urllib.request.urlopen",
        side_effect=OSError("connection refused"),
    ):
        assert _is_host_reachable("http://localhost:11434") is False


def test_is_host_reachable_passes_timeout():
    # Verify the timeout parameter is forwarded to urlopen
    with patch("ollama_helpers.urllib.request.urlopen") as mock_urlopen:
        _is_host_reachable("http://localhost:11434", timeout=5.0)
        mock_urlopen.assert_called_once_with("http://localhost:11434", timeout=5.0)


# --- get_available_ollama_host tests ---
# These mock _is_host_reachable to control which host appears available.
# The function should prefer remote, and fall back to local.


def test_returns_remote_when_configured_and_reachable():
    # Happy path: remote host is set and responds — use it
    with patch("ollama_helpers._is_host_reachable", return_value=True):
        assert get_available_ollama_host() == settings.ollama_host_remote


def test_returns_local_when_remote_unreachable():
    # Remote is configured but down — fall back to local
    with patch("ollama_helpers._is_host_reachable", return_value=False):
        assert get_available_ollama_host() == settings.ollama_host_local


def test_returns_local_when_remote_not_configured():
    # Remote host is empty string — skip it entirely, use local
    with patch.object(settings, "ollama_host_remote", ""):
        assert get_available_ollama_host() == settings.ollama_host_local


def test_does_not_ping_when_remote_not_configured():
    # When remote is empty, we shouldn't even try to ping it
    with (
        patch.object(settings, "ollama_host_remote", ""),
        patch("ollama_helpers._is_host_reachable") as mock_ping,
    ):
        get_available_ollama_host()
        mock_ping.assert_not_called()
