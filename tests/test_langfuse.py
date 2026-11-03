import asyncio
import os
import warnings

import pytest
from langchain_core.messages import HumanMessage
from langfuse import Langfuse, get_client
from langfuse.api import NotFoundError

from config import settings
from mcp_client.mcp_manager import answer_question


def is_langfuse_configured() -> bool:
    """True if tracing is switched on and the Langfuse keys are set."""
    # Read from the environment, as the Langfuse library does
    return all(
        [
            os.environ.get("LANGFUSE_TRACING_ENABLED", "false").lower() != "false",
            os.environ.get("LANGFUSE_PUBLIC_KEY"),
            os.environ.get("LANGFUSE_SECRET_KEY"),
        ]
    )


async def wait_for_trace(langfuse_client, trace_id):
    """Return the trace once Langfuse has stored it: try every 0.5 s, for up to 10 s."""
    for _ in range(20):
        await asyncio.sleep(0.5)
        try:
            trace = langfuse_client.api.trace.get(trace_id)
        except NotFoundError:
            continue  # Not stored yet, try again
        # Langfuse can return the trace before all its fields are filled in
        if trace.name:
            return trace
    pytest.fail("Langfuse didn't store the trace within 10 s")


langfuse_configured = is_langfuse_configured()

skip_reason = (
    "Langfuse tracing not enabled or not configured "
    "(LANGFUSE_TRACING_ENABLED, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)"
)


@pytest.mark.langfuse
@pytest.mark.skipif(not langfuse_configured, reason=skip_reason)
def test_langfuse_client_connects():
    langfuse_client = get_client()
    assert langfuse_client.auth_check()


@pytest.mark.langfuse
@pytest.mark.mcp_server
@pytest.mark.skipif(not langfuse_configured, reason=skip_reason)
@pytest.mark.asyncio
async def test_answer_question_sends_trace():
    """answer_question sends a trace with the app name, labelled with the test environment,
    and without the question or the answer."""
    if not settings.mcp_server_url:
        warnings.warn("MCP_SERVER_URL is not set — skipping the MCP query trace test")
        pytest.skip("MCP server not configured (MCP_SERVER_URL)")

    # langfuse_trace_id is a special argument: @observe takes it out and uses it as the
    # trace id, so answer_question never receives it.
    trace_id = Langfuse.create_trace_id()
    conversation = [HumanMessage(content="What is inflation?")]
    await answer_question(conversation, {}, client_type="pytest", langfuse_trace_id=trace_id)

    # Send the trace now, instead of waiting for the library's next batch
    langfuse_client = get_client()
    langfuse_client.flush()
    trace = await wait_for_trace(langfuse_client, trace_id)

    assert trace.name == settings.app_name
    # conftest.py labels every trace sent by the tests
    assert trace.environment == settings.langfuse_test_tracing_environment
    # conftest.py switches message tracing off for every test
    assert trace.input is None
    assert trace.output is None
