"""Run vector searches, download traces from Langfuse, import to database.

Usage:
    python -m analytics.benchmark_vector_search
"""

import asyncio
import time

from config import settings
from analytics.export import fetch_and_save_traces
from analytics.setup_database import setup_database
from analytics.vector_search_importer import import_vector_search_traces
from analytics.questions_for_testing import questions
from llm.llm_manager import LLM_Client
from rag.langfuse_helpers import create_langfuse_client
from rag.rag_manager import retrieve

# A few questions to exercise the vector search step
BENCHMARK_QUESTIONS = questions["general"]


async def run_vector_searches(questions, provider_name) -> LLM_Client:
    """Run vector searches using only the specified embeddings provider.

    Returns the LLM_Client so the caller can read which provider was actually used.
    """
    # Force embeddings to use only this provider
    settings.embeddings_provider_priority = [provider_name]

    llm_client = LLM_Client()
    config = {"configurable": {"llm_client": llm_client}}

    for question in questions:
        print(f"Searching: {question}")
        state = {"question": question, "user_id": f"benchmark_{provider_name}"}
        result = await retrieve(state, config)
        print(f"  Got {len(result['context'])} results")

    return llm_client


if __name__ == "__main__":
    # Step 1 — Run vector searches
    print("=== Step 1: Running vector searches ===")
    #llm_client = asyncio.run(run_vector_searches(BENCHMARK_QUESTIONS, "ollama_self_hosted"))
    llm_client = asyncio.run(run_vector_searches(BENCHMARK_QUESTIONS, "ollama_local"))

    # Flush Langfuse traces and wait for them to be indexed
    langfuse_client = create_langfuse_client()
    if langfuse_client:
        langfuse_client.flush()
    print("Waiting for Langfuse to index traces...")
    time.sleep(5)

    # Step 2 — Download traces
    print("\n=== Step 2: Downloading traces ===")
    traces_file = fetch_and_save_traces()

    # Step 3 — Import vector_search traces to database
    print("\n=== Step 3: Importing to database ===")
    setup_database()
    import_vector_search_traces(
        traces_file,
        user_id_prefix="benchmark_",
        default_model=llm_client.embeddings_model.model,
        default_provider=llm_client.embeddings_provider_name,
    )
    print("Done.")
