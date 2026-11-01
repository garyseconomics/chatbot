import asyncio
import uuid
import warnings

import pytest
from langfuse import Langfuse

from config import settings
from mcp_client.mcp_manager import MCP_query
from tracing.langfuse_helpers import create_langfuse_client, is_langfuse_configured

langfuse_configured = is_langfuse_configured()

skip_reason = (
    "Langfuse tracing not enabled or not configured "
    "(LANGFUSE_TRACING_ENABLED, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)"
)


@pytest.mark.langfuse
@pytest.mark.skipif(not langfuse_configured, reason=skip_reason)
def test_langfuse_client_connects():
    langfuse_client = create_langfuse_client()
    assert isinstance(langfuse_client, Langfuse)
    assert langfuse_client.auth_check()


async def query_and_get_traces() -> list:
    """Send a question through MCP_query and return the traces Langfuse stored for it."""
    if not settings.mcp_server_url:
        warnings.warn("MCP_SERVER_URL is not set — skipping the MCP query trace test")
        pytest.skip("MCP server not configured (MCP_SERVER_URL)")

    # A new id on every run, so we never find a trace left by an earlier run (see #58)
    client_type = f"test-{uuid.uuid4()}"
    await MCP_query("What is inflation?", client_type=client_type)

    # Wait for Langfuse to index the trace
    langfuse_client = create_langfuse_client()
    langfuse_client.flush()
    await asyncio.sleep(2)

    # client_type is stored in Langfuse's user_id field for now
    response = langfuse_client.api.trace.list(user_id=client_type)
    return response.data


@pytest.mark.langfuse
@pytest.mark.mcp_server
@pytest.mark.skipif(not langfuse_configured, reason=skip_reason)
@pytest.mark.asyncio
async def test_mcp_query_sends_trace_with_client_type():
    """MCP_query sends one trace with the app name and the client type."""
    traces = await query_and_get_traces()

    assert len(traces) == 1
    assert traces[0].name == settings.app_name
    # conftest.py labels every trace sent by the tests
    assert traces[0].environment == settings.langfuse_test_tracing_environment


@pytest.mark.langfuse
@pytest.mark.mcp_server
@pytest.mark.skipif(not langfuse_configured, reason=skip_reason)
@pytest.mark.asyncio
async def test_mcp_query_trace_has_no_question_or_answer():
    """With message tracing off, the question and the answer are not sent to Langfuse."""
    # conftest.py switches message tracing off for every test.
    # Not tested: that they are sent when LANGFUSE_MESSAGE_TRACING_ENABLED=true. The @observe
    # decorators read the flag only once, when Python imports their module, so changing it
    # inside a test has no effect. Testing it would need a separate Python process started
    # with the flag on.
    traces = await query_and_get_traces()

    assert traces[0].input is None
    assert traces[0].output is None
