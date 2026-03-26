"""Fetch traces from Langfuse and save as JSON."""

import json
import logging
from datetime import datetime
from pathlib import Path

from langfuse import Langfuse

# Importing config triggers load_dotenv(), which makes LANGFUSE_PUBLIC_KEY
# and LANGFUSE_SECRET_KEY available as environment variables.
import config  # noqa: F401

logger = logging.getLogger(__name__)


# Connects to Langfuse and downloads all traces, page by page.
# Returns the raw trace objects.
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


# Downloads all traces from Langfuse and saves them as a JSON file.
# Returns the path to the saved file.
def fetch_and_save_traces() -> Path:
    raw_traces = fetch_traces()

    # Serialize Langfuse trace objects to plain dicts
    serialized = [trace.dict() for trace in raw_traces]

    output_dir = Path(__file__).parent / "raw_data"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    file_path = output_dir / f"traces_{timestamp}.json"
    file_path.write_text(json.dumps(serialized, indent=2, default=str))
    print(f"Saved {len(serialized)} traces to {file_path}")
    return file_path


if __name__ == "__main__":
    fetch_and_save_traces()
