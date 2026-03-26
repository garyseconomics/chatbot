"""Import vector_search traces from JSON files into SQLite database."""

import json
import logging
import sqlite3
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)


def _is_vector_search_trace(raw_input) -> bool:
    """Check if a trace's raw_input matches the vector_search format.

    Vector_search traces have input like:
      {"args": [{"question": "...", "user_id": "..."}], "kwargs": {}}
    Some older traces omit user_id but still have question.
    """
    if not isinstance(raw_input, dict) or "args" not in raw_input:
        return False
    args = raw_input["args"]
    if not isinstance(args, list) or len(args) == 0:
        return False
    first_arg = args[0]
    return isinstance(first_arg, dict) and "question" in first_arg


def _parse_vector_search_trace(trace: dict) -> dict:
    """Extract fields from a vector_search trace.

    Supports three formats:
    - Flat format (from separator): question at top level, trace_id, model_name, etc.
    - Raw export format (from export.py): id, input, output, userId (Langfuse field names).
    - Old format (from other_traces files): trace_id, raw_input, raw_output.
    """
    # Flat format: fields already extracted by the separator
    if "question" in trace:
        return {
            "trace_id": trace["trace_id"],
            "user_id": trace.get("user_id"),
            "question": trace["question"],
            "timestamp": trace.get("timestamp"),
            "latency": trace.get("latency"),
            "num_results": trace.get("num_results", 0),
            "model_name": trace.get("model_name"),
            "provider": trace.get("provider"),
        }

    # Raw export format uses "input"/"output"/"id"/"userId";
    # old format uses "raw_input"/"raw_output"/"trace_id"
    trace_input = trace.get("input") or trace.get("raw_input", {})
    trace_output = trace.get("output") or trace.get("raw_output", {})
    trace_id = trace.get("id") or trace.get("trace_id")

    first_arg = trace_input["args"][0]

    # Count results: output has {"context": [...documents...]}
    num_results = 0
    if isinstance(trace_output, dict) and "context" in trace_output:
        num_results = len(trace_output["context"])

    # Raw export has metadata with model/provider; old format doesn't
    metadata = trace.get("metadata") or {}

    return {
        "trace_id": trace_id,
        "user_id": first_arg.get("user_id"),
        "question": first_arg.get("question"),
        "timestamp": trace.get("timestamp"),
        "latency": trace.get("latency"),
        "num_results": num_results,
        "model_name": metadata.get("embedding_model") or metadata.get("model"),
        "provider": metadata.get("embedding_provider") or metadata.get("provider"),
    }


def trace_exists(cursor, trace_id: str) -> bool:
    """Check if a trace_id already exists in the vector_search_traces table."""
    cursor.execute(
        "SELECT COUNT(*) FROM vector_search_traces WHERE trace_id = ?",
        (trace_id,),
    )
    return cursor.fetchone()[0] > 0


def import_vector_search_traces(
    file_path: Path,
    db_path: str = None,
    user_id_prefix: str = None,
    default_model: str = None,
    default_provider: str = None,
) -> None:
    """Read traces from a JSON file, extract vector_search ones, and insert into SQLite.

    If user_id_prefix is given, only import traces whose user_id starts with that prefix.
    default_model and default_provider fill in missing metadata (e.g. for benchmark traces).
    """
    if db_path is None:
        db_path = settings.analytics_db_path

    with open(file_path) as f:
        traces = json.load(f)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        inserted = 0
        skipped = 0
        not_vector_search = 0

        for trace in traces:
            # Flat format has "question" at top level;
            # raw export uses "input", old format uses "raw_input"
            is_vs = (
                "question" in trace
                or _is_vector_search_trace(trace.get("input"))
                or _is_vector_search_trace(trace.get("raw_input"))
            )
            if not is_vs:
                not_vector_search += 1
                continue

            parsed = _parse_vector_search_trace(trace)

            if user_id_prefix and not (parsed["user_id"] or "").startswith(user_id_prefix):
                not_vector_search += 1
                continue

            if trace_exists(cursor, parsed["trace_id"]):
                skipped += 1
                continue

            cursor.execute(
                "INSERT INTO vector_search_traces "
                "(trace_id, user_id, question, timestamp, latency, "
                "num_results, model_name, provider) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    parsed["trace_id"],
                    parsed["user_id"],
                    parsed["question"],
                    parsed["timestamp"],
                    parsed["latency"],
                    parsed["num_results"],
                    parsed.get("model_name") or default_model,
                    parsed.get("provider") or default_provider,
                ),
            )
            inserted += 1

        conn.commit()
    finally:
        conn.close()

    logger.info(
        "Imported %d vector_search traces, skipped %d existing, "
        "ignored %d non-vector_search traces (from %s)",
        inserted,
        skipped,
        not_vector_search,
        file_path.name,
    )


if __name__ == "__main__":
    raw_data_dir = Path(__file__).parent / "raw_data"

    # Look for trace files: vector_search_traces_*, traces_*, or other_traces_*
    files = sorted(
        raw_data_dir.glob("vector_search_traces_*.json"),
        key=lambda f: f.stat().st_mtime,
    )
    if not files:
        files = sorted(
            raw_data_dir.glob("traces_*.json"),
            key=lambda f: f.stat().st_mtime,
        )
    if not files:
        files = sorted(
            raw_data_dir.glob("other_traces_*.json"),
            key=lambda f: f.stat().st_mtime,
        )
    if not files:
        print("No trace files found in", raw_data_dir)
    else:
        newest = files[-1]
        print(f"Importing from {newest.name}...")
        import_vector_search_traces(newest)
        print("Done.")
