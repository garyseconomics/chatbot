"""Tests for fetching traces from Langfuse."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from analytics.export import classify_traces, fetch_traces


# Helper: builds a fake user trace matching the real Langfuse format.
# The input is a dict with the full LLM prompt (question + RAG context),
# and the output is a dict with the model's response in "content".
def _make_user_trace(
    trace_id: str = "trace-1",
    user_id: str = "telegram:123",
    question: str = "What is inflation?",
    answer: str = "Inflation is the rate at which prices rise.",
    timestamp: str = "2026-03-16T14:00:00Z",
    metadata: dict | None = None,
) -> SimpleNamespace:
    prompt_content = (
        f"You are a helpful economics assistant...\n\n"
        f"Question: {question}\n"
        f"Reference material: Some video transcript content here.\n"
        f"Answer:"
    )
    return SimpleNamespace(
        id=trace_id,
        user_id=user_id,
        input={
            "args": [
                {"messages": [{"content": prompt_content, "type": "human"}]}
            ],
            "kwargs": {"user_id": user_id},
        },
        output={"content": answer},
        timestamp=timestamp,
        metadata=metadata or {"model": "qwen3:32b", "provider": "ollama"},
        latency=1.5,
        tags=[],
    )


# Helper: builds a fake evaluator trace (like the Langfuse toxicity scorer).
# These have a different structure: input is a list of messages, user_id is None.
def _make_evaluator_trace(
    trace_id: str = "eval-1",
    timestamp: str = "2026-03-16T14:00:00Z",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=trace_id,
        user_id=None,
        input=[{"content": "Evaluate the toxicity...", "role": "user"}],
        output="SyntaxError: Unexpected token...",
        timestamp=timestamp,
        metadata=None,
        latency=6.0,
        tags=[],
    )


# Helper: wraps traces in the paginated response format that the API returns.
def _make_trace_list(traces: list) -> SimpleNamespace:
    return SimpleNamespace(data=traces, meta=SimpleNamespace(total_items=len(traces)))


# --- fetch_traces tests ---


# Simulates 2 pages of results and checks that fetch_traces collects
# traces from all pages, not just the first one.
@patch("analytics.export.Langfuse")
def test_fetch_traces_handles_multiple_pages(mock_langfuse_cls):
    client = MagicMock()
    mock_langfuse_cls.return_value = client

    page1 = SimpleNamespace(
        data=[_make_user_trace(trace_id="t1"), _make_user_trace(trace_id="t2")],
        meta=SimpleNamespace(total_items=3, page=1, total_pages=2),
    )
    page2 = SimpleNamespace(
        data=[_make_user_trace(trace_id="t3")],
        meta=SimpleNamespace(total_items=3, page=2, total_pages=2),
    )
    client.api.trace.list.side_effect = [page1, page2]

    results = fetch_traces()

    assert len(results) == 3
    assert client.api.trace.list.call_count == 2


# --- classify_traces tests ---


# classify_traces should parse user traces with clean question and answer.
@patch("analytics.export.Langfuse")
def test_classify_extracts_user_question_and_answer(mock_langfuse_cls):
    client = MagicMock()
    mock_langfuse_cls.return_value = client
    client.api.trace.list.return_value = _make_trace_list([_make_user_trace()])

    raw = fetch_traces()
    user_traces, other_traces = classify_traces(raw)

    assert len(user_traces) == 1
    assert len(other_traces) == 0
    trace = user_traces[0]
    assert trace["trace_id"] == "trace-1"
    assert trace["user_id"] == "telegram:123"
    assert trace["question"] == "What is inflation?"
    assert trace["answer"] == "Inflation is the rate at which prices rise."
    assert trace["timestamp"] == "2026-03-16T14:00:00Z"
    assert trace["model"] == "qwen3:32b"
    assert trace["latency"] == 1.5


# Evaluator traces should go into the "other" list with raw data preserved.
@patch("analytics.export.Langfuse")
def test_classify_puts_evaluator_traces_in_other(mock_langfuse_cls):
    client = MagicMock()
    mock_langfuse_cls.return_value = client
    client.api.trace.list.return_value = _make_trace_list(
        [_make_evaluator_trace()]
    )

    raw = fetch_traces()
    user_traces, other_traces = classify_traces(raw)

    assert len(user_traces) == 0
    assert len(other_traces) == 1
    trace = other_traces[0]
    assert trace["trace_id"] == "eval-1"
    assert trace["user_id"] is None
    assert trace["raw_input"] is not None
    assert trace["raw_output"] is not None


# Mixed traces should be split: user traces parsed, evaluator traces kept raw.
@patch("analytics.export.Langfuse")
def test_classify_splits_user_and_evaluator_traces(mock_langfuse_cls):
    client = MagicMock()
    mock_langfuse_cls.return_value = client
    client.api.trace.list.return_value = _make_trace_list(
        [_make_user_trace(trace_id="u1"), _make_evaluator_trace(trace_id="e1")]
    )

    raw = fetch_traces()
    user_traces, other_traces = classify_traces(raw)

    assert len(user_traces) == 1
    assert len(other_traces) == 1
    assert user_traces[0]["question"] == "What is inflation?"
    assert other_traces[0]["trace_id"] == "e1"


# When a user trace has no metadata, model should default to "unknown".
@patch("analytics.export.Langfuse")
def test_classify_handles_missing_metadata(mock_langfuse_cls):
    client = MagicMock()
    mock_langfuse_cls.return_value = client
    trace = _make_user_trace()
    trace.metadata = None
    client.api.trace.list.return_value = _make_trace_list([trace])

    raw = fetch_traces()
    user_traces, _ = classify_traces(raw)

    assert user_traces[0]["model"] == "unknown"


# An empty trace list should return two empty lists without errors.
def test_classify_handles_empty_trace_list():
    user_traces, other_traces = classify_traces([])

    assert user_traces == []
    assert other_traces == []
