import pytest
from config import settings

langfuse_configured = all([
    settings.langfuse_public_key,
    settings.langfuse_secret_key,
])

skip_reason = "Langfuse env vars not configured (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)"


@pytest.mark.langfuse
@pytest.mark.skipif(not langfuse_configured, reason=skip_reason)
def test_langfuse_client_connects():
    from langfuse import Langfuse

    client = Langfuse()
    assert client.auth_check()


@pytest.mark.langfuse
@pytest.mark.skipif(not langfuse_configured, reason=skip_reason)
def test_langfuse_trace_and_span():
    from langfuse import Langfuse

    client = Langfuse()
    span = client.start_span(name="test-span", input={"ping": "pong"})
    span.update(output={"ok": True})
    span.end()
    client.flush()

    # If we got here without exceptions, the span was sent successfully
    assert span.id is not None
    assert span.trace_id is not None


@pytest.mark.langfuse
@pytest.mark.skipif(not langfuse_configured, reason=skip_reason)
def test_langfuse_observe_decorator():
    from langfuse import Langfuse, observe

    @observe()
    def ping(x: str) -> str:
        return f"pong:{x}"

    result = ping("test")
    assert result == "pong:test"

    client = Langfuse()
    client.flush()
