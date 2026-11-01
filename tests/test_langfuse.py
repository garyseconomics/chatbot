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


@pytest.mark.langfuse
@pytest.mark.mcp_server
@pytest.mark.skipif(not langfuse_configured, reason=skip_reason)
@pytest.mark.asyncio
async def test_mcp_query_sends_trace_with_client_type():
    """MCP_query sends one trace with the app name and the client type."""
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

    assert len(response.data) == 1
    assert response.data[0].name == settings.app_name
    # conftest.py labels every trace sent by the tests
    assert response.data[0].environment == settings.langfuse_test_tracing_environment
