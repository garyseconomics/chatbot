"""Fetch traces from Langfuse for analysis and storage."""

import logging

from langfuse import Langfuse

# Importing config triggers load_dotenv(), which makes LANGFUSE_PUBLIC_KEY
# and LANGFUSE_SECRET_KEY available as environment variables.
import config  # noqa: F401

logger = logging.getLogger(__name__)


# Tries to extract the user's question from the structured input.
# User traces have the question embedded in a prompt like:
#   "Question: <the actual question>\nReference material: ..."
# Returns None if the input doesn't match this format.
def _extract_question(raw_input) -> str | None:
    if not isinstance(raw_input, dict) or "args" not in raw_input:
        return None
    try:
        content = raw_input["args"][0]["messages"][0]["content"]
        if "Question: " not in content:
            return None
        return content.split("Question: ", 1)[1].split("\nReference material:")[0]
    except (KeyError, IndexError, TypeError):
        return None


# Tries to extract the answer text from the structured output.
# User traces have the answer in output["content"].
# Returns None if the output doesn't match this format.
def _extract_answer(raw_output) -> str | None:
    if isinstance(raw_output, dict) and "content" in raw_output:
        return raw_output["content"]
    return None


# Parses a user trace into a flat dict with the clean question and answer.
def _extract_user_trace(trace) -> dict:
    metadata = trace.metadata or {}
    return {
        "trace_id": trace.id,
        "user_id": trace.user_id,
        "question": _extract_question(trace.input),
        "answer": _extract_answer(trace.output),
        "timestamp": trace.timestamp,
        "model": metadata.get("model", "unknown"),
        "latency": trace.latency,
    }


# Takes a list of raw Langfuse traces and splits them into two lists:
# - user_traces: traces from real users, with parsed question and answer
# - other_traces: everything else (evaluators, etc.), kept as raw data
def classify_traces(raw_traces: list) -> tuple[list[dict], list[dict]]:
    user_traces: list[dict] = []
    other_traces: list[dict] = []

    for trace in raw_traces:
        question = _extract_question(trace.input)
        if question is not None:
            user_traces.append(_extract_user_trace(trace))
        else:
            other_traces.append({
                "trace_id": trace.id,
                "user_id": trace.user_id,
                "raw_input": trace.input,
                "raw_output": trace.output,
                "timestamp": trace.timestamp,
                "latency": trace.latency,
            })

    logger.info(
        "Classified %d traces: %d user, %d other",
        len(raw_traces),
        len(user_traces),
        len(other_traces),
    )
    return user_traces, other_traces


# Connects to Langfuse and downloads all traces, page by page.
# Returns the raw trace objects for classification.
def fetch_traces() -> list:
    client = Langfuse()
    results: list = []

    # Get the 1st page and the total number of pages
    response = client.api.trace.list(page=1)
    total_pages = getattr(response.meta, "total_pages", 1)
    # Loop through all the pages
    for page in range(1, total_pages + 1):
        results.extend(response.data)
        # Get the next page
        if page < total_pages:
            response = client.api.trace.list(page=page + 1)

    logger.info("Fetched %d traces from Langfuse", len(results))
    return results


if __name__ == "__main__":
    import json
    from datetime import datetime
    from pathlib import Path

    raw_traces = fetch_traces()
    user_traces, other_traces = classify_traces(raw_traces)

    output_dir = Path(__file__).parent / "raw_data"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    # Save user traces
    user_file = output_dir / f"user_traces_{timestamp}.json"
    user_file.write_text(json.dumps(user_traces, indent=2, default=str))
    print(f"Saved {len(user_traces)} user traces to {user_file}")

    # Save other traces
    other_file = output_dir / f"other_traces_{timestamp}.json"
    other_file.write_text(json.dumps(other_traces, indent=2, default=str))
    print(f"Saved {len(other_traces)} other traces to {other_file}")
