# Completed tasks

Tasks moved from [TODO.md](../TODO.md) after completion.

## Answer quality

- [x] **Review new questions from real users for the test set** -- `analytics/new_questions_from_users.md` and `plan/phase_2/prompt/new_questions_from_users.md` collect questions from real user sessions organised by topic. Reviewed and added suitable ones to `analytics/questions_for_testing.py` under the appropriate categories.

## Planning Phase 2

- [x] **Plan to get to Phase 2** -- Review all open tasks, the Phase 1 report (`testing_phase_1/Phase_1_Report.md`), and the latency reports. Decide what must be done before Phase 2 (~3,000 Patreon users), what can wait, and what order to tackle things in. Key areas to consider: answer quality (prompt v3 issues, source material gaps), infrastructure scalability (cloud embedding provider via #41, Ollama Cloud limits), reliability (error handling, service monitoring), and new features (multi-turn conversations, temporal awareness).
- [x] **Review Q&A from prompt v3** (2026-03-21 04:13 to 2026-03-23 19:18) -- All 17 real user Q&As reviewed. Bot refused valid economics questions (Laffer curve, monopolies, rent control, etc.), hallucinated "competing for jobs", and accepted false premises due to no conversation memory. Documented in `plan/phase_2/prompt/prompt_v3.md`.
- [x] **Review Q&A from prompt v3.1** (2026-03-23 19:18 to 2026-03-28 ~17:50) -- March 23 to 28 reviewed: 33 real user questions plus developer tests. Issues found: financial advice, RAG internals leak, over-eager off-topic deflection on fascism/inequality. Documented in `plan/phase_2/prompt/prompt_v3_1.md`.
- [x] **Evaluate prompt v4** (2026-03-29) -- 97 questions tested with `qwen3-next:80b`. Dual run (with and without RAG context) due to empty database accident — turned out useful for comparison. Results: most Phase 1 issues confirmed fixed (off-topic, financial advice, personal life, manipulation, leading questions). New issues: identity over-correction on plain greetings, hallucinated date, without-context inconsistencies on sensitive topics, crypto stance still missing (source material gap). Documented in `plan/phase_2/prompt/prompt_v4.md` (summary) and `plan/phase_2/prompt/prompt_v4_2026-03-29.md` (full Q&A). Issues consolidated in `plan/phase_2/prompt/prompt_issues.md`.

## Bug fixes — Testing Phase 1

- [x] **Bot crashes when a user replies to a bot message in Discord** ([#23](https://github.com/garyseconomics/chatbot/issues/23)) -- When a user replies to one of the bot's messages, the bot crashes with the generic error message. Could not reproduce (2026-03-21): retested all four crash examples from the original report — bot handled all of them without errors. The original crashes were most likely caused by Discord's 2000-char message limit (#33) or intermittent Ollama Cloud 500 errors (#29), both of which have since been addressed.
- [x] **Investigate why the bot has been resetting so many times** ([#28](https://github.com/garyseconomics/chatbot/issues/28)) -- Check server logs to identify the root cause of frequent bot restarts during Phase 1 testing.
- [x] **Intermittent Ollama Cloud 500 errors** ([#29](https://github.com/garyseconomics/chatbot/issues/29)) -- Ollama Cloud sometimes returns `ResponseError: Internal Server Error (status code: 500)`. Root cause: Ollama Cloud enforces a strict concurrency limit — max 2 active requests + 5 queued (headers: `x-ratelimit-max-concurrent: 2`, `x-ratelimit-queue-limit: 5`). Requests beyond that get rejected (429/500). Reproduced with `debug_cloud_500.py` (10 concurrent requests, 3 rejected). Addressed by the `LLM_Client` refactor: `chat()` now falls back to the next provider when `invoke()` fails, and `_select_provider()` retries with error reset after exhausting all providers. Tests force self-hosted Ollama via `use_ollama_for_testing` fixture to avoid flaky cloud errors.
- [x] **Thinking models consume `num_predict` with thinking tokens** -- `qwen3-next:80b` (Ollama Cloud) uses a thinking mode where internal reasoning tokens count against the `num_predict` limit. With `max_tokens=500`, the model spent all tokens thinking and returned empty answers. **Fix:** removed `num_predict` / `max_tokens` entirely (2026-03-21). The message length problem (#33) should be solved on the sending side (split/truncate before sending to Discord/Telegram) instead of limiting the LLM output.

## Bug fixes — Testing Phase 0

- [x] **Fix video link parsing** ([#14](https://github.com/garyseconomics/chatbot/issues/14)) -- `video_links.py` uses `strip()` to remove a path prefix, but `strip()` removes *characters*, not a substring -- this is a bug that causes wrong video links (e.g., truncated YouTube IDs). Rewrite using `Path` operations for correct and robust parsing.

## Async RAG pipeline ([#38](https://github.com/garyseconomics/chatbot/issues/38))

- [x] **Make RAG_query async (Phase 1)** -- `RAG_query` is now `async def` and uses `graph.ainvoke()`. The internal functions (`retrieve`, `generate`, `llm_chat`) are still sync — LangGraph runs them in threads automatically. Error handling simplified to a single `except` block with configurable messages in `settings.error_messages`.
- [x] **Improve error messages** -- Error messages moved to `settings.error_messages` dict in `config.py`, keyed by exception class name. `RAG_query` looks up `type(e).__name__` and returns a user-facing message. Default message under `"DefaultError"` key.
- [x] **Make RAG_query async (Phase 2)** -- Pipeline is now fully async end-to-end. `retrieve()` uses `await vector_store.asimilarity_search()`, `generate()` uses `await client.chat()`, and `LLM_Client.chat()` uses `await llm.ainvoke()`. All LLM manager tests updated to async. No more sync functions running in LangGraph's thread pool.
- [x] **Update callers and tests for async RAG_query** -- All callers updated: Discord bot (`create_task`), Telegram bot (`await`), CLI chatbot (`asyncio.run`). All tests updated and simplified: `test_rag_manager.py` (3 tests, zero mocks), `test_chatbot.py` (1 test, 2 mocks), `test_telegram_bot.py` (2 tests, 2 mocks), `test_ask_questions.py` (async). Ruff clean. Final commit: 2d15125.

## LLM management

- [x] **Refactor LLM management into `LLM_Client` class** -- Consolidated all provider management (`llm_manager.py` + `llm_providers_helpers.py`) into a single `LLM_Client` class. `chat()` tries providers in priority order and falls back on invoke failure. `get_embedding_model()` returns an embedding model from the first available provider. `_select_provider()` handles both chat and embeddings with retry logic (do-while loop, error reset, `max_attempts` safety net). `providers_errors` dict tracks all failures. Callers (`rag_manager.py`, `vector_database_manager.py`) now use `LLM_Client` — no longer need to know about Ollama internals. `llm_providers_helpers.py` and its tests deleted. 12 tests including 3 error-path tests with `pytest.raises`.
- [x] **Embedding provider fallback** -- `get_embedding_model()` currently uses the first available provider with no invoke-level fallback. If a cloud embedding provider is added in the future, it should have the same retry/fallback logic as `chat()`.

## New functionality

- [x] **Chat sessions** -- `LLM_Client` is now created once per `RAG_query` call and passed via LangGraph config to both `retrieve` and `generate`, so the same instance (with its `provider_name` and model) is reused across the pipeline. For multi-turn conversations, the instance will need to persist across multiple `RAG_query` calls — that's part of the multi-turn implementation (#6).
- [x] **Discord bot DM support** ([#16](https://github.com/garyseconomics/chatbot/issues/16)) -- Added Direct Message support to the Discord bot. Uses `message.channel` instead of looking up the channel by name — works for both DMs and channel messages.

## Content database

- [x] **Separate content database scripts from the main application** -- Moved the import/management scripts (`import_documents.py`, `srt_splitter.py`, `collections_viewer.py`, `vector_database_manager.py`) out of `src/` into `content_database/scripts/`. These are host-only tools, not part of the bot runtime. The `data/` and `docs/` folders also moved under `content_database/`. Created a separate `content_database/config.py` that reads from `.env`. Shared variables (`EMBEDDINGS_MODEL`, `COLLECTION_NAME`, `DATABASE_PATH`, `VIDEO_IDS_SEPARATOR`) are configured in `.env` so both `src/config.py` and `content_database/config.py` stay in sync. The `src/vector_database/` module was reduced to a single `get_vector_database()` function and moved to `src/rag/vector_database.py`. Tests in `tests/` updated and passing.
- [x] **Review and test the content database importer scripts** -- (1) Removed the `LLM_Client` dependency from `vector_database_manager.py` — replaced with a local `get_embeddings_model()` function. (2) Verified all scripts run correctly (`import_documents.py`, `collections_viewer.py`). (3) Fixed test failures: removed missing `use_ollama_for_testing` fixture, moved `sample.srt` to `content_database/scripts/tests/`, added `__init__.py` files to make `content_database` a proper package. Also added `logging.basicConfig()` to `import_documents.py` so progress is visible, and deleted a stale `general` collection from the database.

## Analytics and tracing

- [x] **Fix importer for new trace format** ([#44](https://github.com/garyseconomics/chatbot/issues/44)) -- Rewrote the analytics pipeline: unified `traces` table replaces the old `user_traces` + `vector_search_traces` + `qa_test_results` tables. New `trace_importer.py` handles the new Langfuse format (plain string in `args[0]`). Old data preserved in `analytics_old.db`. See `analytics/private/database_status.md` for full details.
- [x] Store prompt versions in the analytics database -- Prompt text lives in `llm/prompt_versions.py`, selected by `llm/prompt_template.py` based on `config.prompt_version`. This is enough for testing different prompt+model combinations — each version is a Python constant and the config selects which one to use. No need for a SQLite table.
- [x] **Add prompt_version to Langfuse trace metadata** -- The chatbot now includes `prompt_version` in the metadata sent to Langfuse. The trace importer reads it from metadata and stores it in the DB. If a trace is missing `prompt_version` in metadata, the importer stores NULL so the problem is visible. Existing traces were backfilled: 4 pre-v4 traces set to v3.1, the rest to v4.
- [x] **Rework the QA testing pipeline** -- Done. `analytics/scripts/ask_questions.py` only asks questions (traces go to Langfuse), with support for filtering by category. The unified `trace_importer.py` imports all traces including `qa_test` ones, with vector search context stored in `search_result_documents`. Prompt version is recorded in Langfuse trace metadata.

## Analytics (metrics)

- [x] **Evaluate latency and stability with the new provider** ([#30](https://github.com/garyseconomics/chatbot/issues/30)) -- Measure latency and check if the bot crashes less after switching providers. Latency evaluated in testing_phase_1/latency_report_chat_model.md.
- [x] **Export traces from Langfuse** -- Fetch all traces from Langfuse, classify them as user or other, and store them as JSON files in `analytics/raw_data/`. Run with `python -m analytics.export`.
- [x] **Store user traces in database** -- Import clean user trace JSON files (from `analytics/raw_data/`) into a SQLite database for analysis. Script checks for duplicates before inserting. Run with `python -m analytics.setup_database` then `python -m analytics.user_trace_importer`. Originally built with MySQL, switched to SQLite (2026-03-20) — no server needed.
  - [x] Create the `user_traces` table in SQLite (trace_id, user_id, question, answer, timestamp, model, latency, prompt_version).
- [x] **Visualize metrics from Phase 1 day 1 session** ([#27](https://github.com/garyseconomics/chatbot/issues/27)) -- Pull metrics from Phase 1 day 1 testing session (Langfuse traces, latency, error rates, usage patterns).
- [x] **Analyze user traces** ([#32](https://github.com/garyseconomics/chatbot/issues/32)) -- Exported traces from Langfuse, imported into SQLite, and analyzed with Claude Code. This replaced the original plan of using Langfuse dashboards. Chat model latency report: `testing_phase_1/latency_report_chat_model.md`. Embedding latency report: `testing_phase_1/latency_report_embedding.md` (completed with per-provider benchmark data under [#40](https://github.com/garyseconomics/chatbot/issues/40)).
- [x] **Embedding model and provider decisions** ([#40](https://github.com/garyseconomics/chatbot/issues/40)) -- Reviewed 2026-03-22: `qwen3-embedding:8b` (MTEB 70.58) is still the best embedding model available on Ollama. Re-check in mid-2026. **Note:** Close #40 with a comment referencing the Phase 2 plan once it's written.
  - [x] **Investigate why `user_id` is null in vector_search traces** -- Fixed by propagating user_id from parent trace.
  - [x] **Record embedding model name and provider in vector_search Langfuse traces** -- Added model and provider to trace metadata.
  - [x] **Improve `analytics/export.py` to classify vector_search traces** -- `vector_search_importer.py` detects and imports vector_search traces into the `vector_search_traces` SQLite table. Supports three trace formats.
  - [x] **Benchmark embedding latency per provider** -- 97 questions, 127 MakeSpace traces, 103 Local traces. MakeSpace ~13x faster (0.18s vs 3.30s median warm). Report: `testing_phase_1/latency_report_embedding.md`.
  - [x] **Compare benchmark results with Phase 1 historical data** -- Updated embedding latency report with benchmark data. Production results consistent with benchmark findings.

## Deployment & Operations

- [x] **Fix Docker build after project restructure** ([#43](https://github.com/garyseconomics/chatbot/issues/43)) -- After the project restructure (`8f5038f`), the bots returned database errors because the volume mount in `docker-compose.yml` changed but the containers were never recreated. Additionally, the Docker build failed due to a stale `py-modules` in `pyproject.toml` and the Dockerfile `COPY` order not working with the `src` layout. Fixed all three issues. Incident report: `analytics/incident_2026-03-28_database_unreachable.md`.
- [x] **Redirect LLM requests from Ollama to another provider** ([#29](https://github.com/garyseconomics/chatbot/issues/29)) -- Added Ollama Cloud as a provider with config settings `ollama_cloud_url`, `ollama_cloud_api_key`, and chat model `qwen3-next:80b`. Replaced the remote/local fallback with a configurable `chat_provider_priority` list that tries providers in order. Embeddings use a separate `embedding_provider_priority`.
- [x] **Dockerize the application** ([#5](https://github.com/garyseconomics/chatbot/issues/5)) -- Create a Docker container with the application and all its dependencies to facilitate deployment on any server. Dockerfile and docker-compose.yml for Telegram bot. CI/CD workflow to build and push image to GHCR on every push. Restart policy (`unless-stopped`) so container recovers after server reset. Discord bot enabled in docker-compose. ~~Add MySQL service~~ — switched to SQLite, no service required. Auto-update containers tracked in [#42](https://github.com/garyseconomics/chatbot/issues/42).
- [x] **Improve Langfuse integration** ([#17](https://github.com/garyseconomics/chatbot/issues/17)) -- Enhanced observability setup. Dashboard visualization tracked in [#32](https://github.com/garyseconomics/chatbot/issues/32).
  - [x] Reuse Langfuse client in `llm_chat()` instead of creating a new one per call.
  - [x] Fix model name in trace metadata -- was always empty because `model_name` param wasn't passed by callers. Now reads `llm.model` which has the resolved name.
  - [x] Track retrieval step in Langfuse -- added `@observe` to `retrieve()` in `rag_manager.py` so vector search timing and results are visible.
  - [x] Raise error when Langfuse credentials are missing instead of silently failing.
  - [x] Replace `print()` with `logger.info()` in `get_llm_client()`.
  - [x] Propagate `user_id` from bot interfaces through the RAG pipeline to Langfuse traces.
  - [x] Verify on the Langfuse platform that traces show correct user IDs, model names, and retrieval steps.

## Project setup & cleanup

- [x] **Use pyproject.toml** -- Migrate from `requirements.txt` to `pyproject.toml` for project configuration and dependency management.
- [x] **Reorganize package structure** -- Review and improve the directory/module layout.
- [x] **Rethink configuration management** -- Migrated to `pydantic-settings`. All settings consolidated in a single `Settings` class in `config.py` with typed fields, defaults, and automatic `.env` loading. All modules now use `from config import settings`.
- [x] **Improve Ollama configuration for chatbot and embedding models** -- Unified with `ollama_helpers.get_available_ollama_host()`: pings remote first, falls back to local. Used by both LLM and embeddings. Removed `use_remote_llm` setting. Tests mock the connectivity check for reliable fallback testing.
- [x] **Clean up the code** -- Apply clean code practices following CLAUDE.md conventions (PEP 8, type hints, ruff, small functions, etc.).
  - [x] Fix typos in `rag_manager.py` ("querying", "technical").
  - [x] Move `ollama_helpers.py` into `llm/` package where it logically belongs.
  - [x] Run `ruff check --fix` and `ruff format` across the codebase -- fixed import sorting, tabs→spaces, trailing newlines, `== None`→`is None`, unused imports, consistent formatting (13 files reformatted).
  - [x] Fix long lines (E501) -- shortened comments in `telegram_bot.py` and `import_documents.py`, split long strings in `prompt_template.py` and `test_vector_database.py`.
  - [x] Replace star import in `test_vector_database.py` with explicit imports.
  - [x] Fix duplicate condition bug in `import_documents.py` (`answer == "y" or answer == "y"` → `answer.strip().lower() in ("y", "yes")`).
  - [x] Extract prompt string as `RAG_PROMPT_TEXT` constant in `prompt_template.py`.
  - [x] Add `if __name__ == "__main__":` guards to `import_documents.py`, `collections_viewer.py`, and `discord_bot.py` (they run code at import time).
  - [x] Add error handling to Discord bot `on_message` and `on_ready` handlers -- wrapped in try/except with `logger.exception()`, `on_message` sends a fallback error message to the user via `message.channel`. Also added `if __name__ == "__main__":` guard for testability.
  - [x] Add type hints to files that are missing them (`video_links.py`, `llm_manager.py`, interfaces).
  - [x] Replace `print()` with `logging` module throughout the codebase -- centralized `logging.basicConfig` in `config.py` (level driven by `show_logs`), each module uses `logging.getLogger(__name__)`, removed all `if settings.show_logs: print()` patterns.
  - [x] Improve generic `except Exception` in `RAG_query()` with more specific error handling -- added `ConnectionError`, `ollama.ResponseError`, and `ValueError` handlers with distinct user-facing messages, kept generic `Exception` as safety net.

## Testing

- [x] **Ensure test coverage** -- Improve and expand the test suite.
  - [x] Add tests for `config.py`, `ollama_helpers.py`, `rag_manager.py` (retrieve, generate, error handling), `srt_splitter.py` (metadata, chunk size), and `process_in_batches()`.
  - [x] Fix env-dependent test failures in `test_llm_manager.py` (remote host tests now mock `settings.ollama_host_remote`).
  - [x] Fix test isolation in `test_vector_database.py` -- added `clean_database` fixture so each test sets up its own state and can run independently.
  - [x] Add tests for Telegram bot (`test_telegram_bot.py`) -- 5 tests covering /start greeting, RAG query invocation, answer delivery, video link appending when context has documents, and plain answer when context is empty.
  - [x] Add tests for CLI chatbot (`test_chatbot.py`) -- 4 tests covering greeting and answer output, RAG query invocation, video link printing, and skipping video text when no context. Refactored `chatbot.py` to extract `main()` with `if __name__ == "__main__":` guard for testability.
  - [x] Add tests for Discord bot (`test_discord_bot.py`) -- 7 tests covering basic behavior (ignores own messages, ignores non-mentions, responds when mentioned), error handling (channel not found, send failure), and on_ready (greeting, channel not found).
- [x] **Run tests and fix failures** -- Full suite green. Fixed tests that depended on `.env` being present (remote host tests now mock `settings.ollama_host_remote`).
- [x] **Review and simplify tests** -- Simplified mock-heavy tests to reduce cognitive debt. Previous tests created since commit `82ebb0f` that use mocks and patterns not yet fully understood.
  - [x] **test_discord_bot.py** — Extracted `should_respond`, `wait_with_thinking`, and `send_greeting` into testable functions. Tests target those directly.
  - [x] **test_rag_manager.py** — Simplified to 3 tests, zero mocks. Extracted `build_error_state()` to test error handling directly.
  - [x] **test_chatbot.py** — Simplified to 1 test, 2 mocks (RAG_query + input). Just verifies main() doesn't crash.
  - [x] **test_telegram_bot.py** — Simplified to 2 smoke tests. Verifies greeting and RAG answer reach send_message.
  - [x] **tests/conftest.py** — Added `use_ollama_for_testing` fixture (not autouse — applied per-test via parameter) to force self-hosted Ollama for tests that hit the LLM. Avoids intermittent Ollama Cloud 500 errors.
  - [x] **test_srt_splitter.py** — Reviewed manually. Fine as-is.
  - [x] **test_config.py** — Reviewed manually. Fine as-is.
  - [x] **test_llm_manager.py** — Rewritten for `LLM_Client` class. 12 tests covering chat, embeddings, fallback, and 3 error-path tests with `pytest.raises`.
  - [x] **test_video_links.py** — Reviewed manually. Fine as-is.
  - [x] **test_vector_database.py** — 1 autouse fixture for test isolation. Reviewed, clear.
  - [x] **test_langfuse.py** — No mocks, integration tests. Reviewed, clear.
