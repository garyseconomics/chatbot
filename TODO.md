# TODO

Pending tasks and things to investigate.

## Make RAG_query async - Priority 0

- [x] **Make RAG_query async (Phase 1)** -- `RAG_query` is now `async def` and uses `graph.ainvoke()`. The internal functions (`retrieve`, `generate`, `llm_chat`) are still sync — LangGraph runs them in threads automatically. Error handling simplified to a single `except` block with configurable messages in `settings.error_messages`.
- [x] **Improve error messages** -- Error messages moved to `settings.error_messages` dict in `config.py`, keyed by exception class name. `RAG_query` looks up `type(e).__name__` and returns a user-facing message. Default message under `"DefaultError"` key.
- [ ] **Make RAG_query async (Phase 2)** -- Convert `retrieve`, `generate`, and `llm_chat` to async with `.ainvoke()` / `.asimilarity_search()` to make the pipeline fully async end-to-end.
- [ ] **Update callers and tests for async RAG_query** -- Reviewed: (1) `rag_manager.py`: async + `build_error_state()` extracted, (2) `test_rag_manager.py`: simplified to 3 tests with zero mocks, (3) Discord bot: `create_task()` replaces `run_in_executor`, (4) Telegram bot: `await` added, (5) CLI chatbot: `asyncio.run()` wrapper, (6) `test_ask_questions.py`: async. Still pending: (7) Rethink and simplify `test_telegram_bot.py` (see "Review and simplify tests" section), (8) Rethink and simplify `test_chatbot.py` (see "Review and simplify tests" section). Run ruff after review.

## Bug fixes - Priority 1 (most urgent)

- [ ] **Bot crashes when a user replies to a bot message in Discord** ([#23](https://github.com/garyseconomics/chatbot/issues/23)) -- When a user replies to one of the bot's messages mentioning the bot, the bot crashes with the generic error message. Need to check server logs to identify the root cause. Before fixing, clean up `test_discord_bot.py` (see "Review and simplify tests" section) so the tests are understood and simplified.
- [ ] **Intermittent Ollama Cloud 500 errors** -- Ollama Cloud sometimes returns `ResponseError: Internal Server Error (status code: 500)`. Happens intermittently during tests and likely in production too. Need to investigate: is it a rate limit, model overload, or provider instability? Consider adding retry logic or falling back to the next provider in `chat_provider_priority`.
- [ ] **Bots crash on long LLM answers** ([#33](https://github.com/garyseconomics/chatbot/issues/33)) -- Telegram bot crashes when the LLM returns an answer exceeding Telegram's 4096 character limit. No error handler registered, so the user never receives a response. Fix: split long messages into chunks ≤4096 chars or truncate with an indication. Before fixing, clean up `test_telegram_bot.py` (see "Review and simplify tests" section) so the tests are understood and simplified.

## Priority 2 (urgent)

- [ ] **Visualize user traces** ([#32](https://github.com/garyseconomics/chatbot/issues/32)) -- Configure Langfuse dashboard to show: (1) Q&A view — questions, answers, user name, timestamp; (2) Performance view — latency metrics, most active users. CLI viewer available as `python -m analytics.trace_viewer`. Fallback: build a Streamlit dashboard if Langfuse doesn't fit our needs.
- [ ] **Evaluate latency and stability with the new provider** ([#30](https://github.com/garyseconomics/chatbot/issues/30)) -- Measure latency and check if the bot crashes less after switching providers.
- [ ] **Finish Dockerize the application** ([#5](https://github.com/garyseconomics/chatbot/issues/5)) -- Remaining tasks: add MySQL service to docker-compose and auto-update containers. See Deployment & Operations section for details.


## Deployment & Operations

- [ ] **Dockerize the application** ([#5](https://github.com/garyseconomics/chatbot/issues/5)) -- Create a Docker container with the application and all its dependencies to facilitate deployment on any server.
  - [x] Dockerfile and docker-compose.yml for Telegram bot.
  - [x] CI/CD workflow to build and push image to GHCR on every push.
  - [x] Restart policy (`unless-stopped`) so container recovers after server reset.
  - [x] Enable Discord bot in docker-compose (service exists but is commented out).
  - [ ] Add MySQL service to docker-compose ([#31](https://github.com/garyseconomics/chatbot/issues/31)) -- Add a `mysql` service with a persistent volume for data, and run `setup_database.py` automatically so the database is ready when the stack starts.
  - [ ] Auto-update running containers when a new image is pushed. Options: (1) Watchtower -- a container that monitors and auto-pulls new images, simplest for single-server; (2) Webhook-based deploy -- CI triggers a webhook on the server to run `docker compose pull && docker compose up -d`; (3) Cron job on the server that periodically pulls the latest image.
- [ ] **Service watcher** ([#21](https://github.com/garyseconomics/chatbot/issues/21)) -- Monitor the bot service availability. Options: (1) HTTP `/health` endpoint polled by Uptime Kuma, or (2) a second bot that pings the main bot through the chat. Observer must run on a different host.
- [ ] **Run tests inside Docker image in CI** ([#34](https://github.com/garyseconomics/chatbot/issues/34)) -- Add a CI step that runs `pytest` inside the built Docker image before pushing to GHCR. During Phase 1 day 2, a Langfuse v3→v4 breaking change was only caught in production because tests only ran locally.
- [ ] **Remove RequestsDependencyWarning filters** -- `requests 2.32.5` doesn't recognize `chardet 7.0.1` as compatible, causing a harmless `RequestsDependencyWarning`. We added filters in `discord_bot.py` and `pyproject.toml` to suppress it. Once `requests` releases a new version with updated version bounds, remove the filters from both files.

## New functionality

- [ ] **Add other OpenAI-compatible providers** ([#29](https://github.com/garyseconomics/chatbot/issues/29)) -- Generalize the provider abstraction to support providers like [OpenRouter](https://openrouter.ai/models/?q=free). Combine with the prompt+LLM evaluation task (see Prompt improvements section) to test different model/prompt combinations.
- [ ] **Multi-turn conversations** ([#6](https://github.com/garyseconomics/chatbot/issues/6)) -- Enable conversations with multiple interactions by implementing chat memory and a conversation loop, so the LLM receives the history of the conversation on each call. Note: the CLI chatbot will become a loop, so the current `asyncio.run()` wrapper (one-shot call) will need to change — likely to an async `main()` with `asyncio.run(main())` at the entry point.

## RAG improvements

- [ ] **Bot lacks temporal awareness** ([#26](https://github.com/garyseconomics/chatbot/issues/26)) -- The bot treats all video content as equally recent because chunks have no date metadata. This causes confusion on time-sensitive topics (e.g., referencing the general election when asked about a recent by-election). Need to add video publish dates to chunk metadata and make the retrieval/generation pipeline date-aware.

## Prompt improvements

- [ ] **Evaluate prompt + LLM combinations** -- Test different prompt versions against different LLMs to find the best combination that meets all our requirements. Use Langfuse to run each combination against a set of test questions and compare results. The test questions from `tests/test_ask_questions.py` can be used as a starting dataset. Known prompt issues to address: bot exposes RAG internals ([#22](https://github.com/garyseconomics/chatbot/issues/22)), bot is too diplomatic ([#24](https://github.com/garyseconomics/chatbot/issues/24)), bot still impersonates Gary ([#25](https://github.com/garyseconomics/chatbot/issues/25)).
  - [ ] Store prompt versions in a MySQL table -- Move prompt text from `llm/prompt_template.py` to a `prompt_versions` table so different versions can be managed and referenced from traces.
  - [ ] Detect prompt version automatically in the importer -- Currently hardcoded to "2". The importer (`user_trace_importer.py`) should identify which prompt version was used for each trace.

## To investigate

- [ ] **DSPy** -- Framework for programming (not prompting) language models. Explore for
  prompt optimization and evaluation. See `prompt_experiments.py` for initial experiments.
- [ ] **MLflow** -- Platform for tracking ML experiments, models, and metrics. Explore for
  tracking prompt experiments and RAG pipeline performance.

## Review and simplify tests

Tests created since commit `82ebb0f` that use mocks and patterns not yet fully understood.
Go through each one, simplify where possible, and make sure every test is understood.
Files are ordered from most complex (most mocks) to simplest.

- [ ] **test_discord_bot.py** — 11 tests, ~23 mocks. Most complex file: event handler interception, AsyncMock, patch.object on asyncio, timing-based tests.
- [ ] **test_fetch_langfuse_traces.py** — 7 tests, ~23 mocks. SimpleNamespace factories, @patch decorators. Tests Langfuse trace extraction and classification.
- [ ] **test_rag_manager.py** — 8 tests, ~22 mocks. Stacked @patch decorators, side_effect for error simulation. Tests RAG query happy path and error handling.
- [ ] **test_user_trace_importer.py** — 9 tests, ~19 mocks. @patch, tmp_path, os.utime. Tests file finding, JSON parsing, MySQL import.
- [ ] **test_chatbot.py** — 4 tests, ~12 mocks. @patch on input/print/RAG_query. Tests CLI chatbot behavior.
- [ ] **test_telegram_bot.py** — 6 tests, ~7 mocks. AsyncMock, @patch. Tests Telegram bot message handling.
- [ ] **test_setup_database.py** — 2 tests, ~7 mocks. @patch on MySQL connector. Tests database table creation.
- [ ] **test_trace_viewer.py** — 5 tests, ~7 mocks. @patch on MySQL connector. Tests CLI trace viewer.

Files with no or minimal mocks (likely fine as-is):

- [ ] **test_vector_database.py** — 1 autouse fixture for test isolation. Review if fixture is clear.
- [ ] **test_srt_splitter.py** — 1 fixture. Straightforward, likely fine.
- [ ] **test_config.py** — No mocks. Direct assertions. Likely fine.
- [ ] **test_langfuse.py** — No mocks, integration tests. Likely fine.
- [ ] **test_llm_manager.py** — No mocks, integration tests. Likely fine.
- [ ] **test_video_links.py** — No mocks. Likely fine.
- [ ] **test_llm_providers_helpers.py** — No mocks. Likely fine.

## Done Tasks

### Analytics

- [x] **Export traces from Langfuse** -- Fetch all traces from Langfuse, classify them as user or other, and store them as JSON files in `analytics/raw_data/`. Run with `python -m analytics.export`.
- [x] **Store user traces in MySQL database** -- Import clean user trace JSON files (from `analytics/raw_data/`) into a MySQL database for analysis. Script checks for duplicates before inserting. Run with `python -m analytics.setup_database` then `python -m analytics.user_trace_importer`.
  - [x] Create the `user_traces` table in MySQL (trace_id, user_id, question, answer, timestamp, model, latency, prompt_version).
- [x] **Visualize metrics from Phase 1 day 1 session** ([#27](https://github.com/garyseconomics/chatbot/issues/27)) -- Pull metrics from Phase 1 day 1 testing session (Langfuse traces, latency, error rates, usage patterns).

### Operations

- [x] **Investigate why the bot has been resetting so many times** ([#28](https://github.com/garyseconomics/chatbot/issues/28)) -- Check server logs to identify the root cause of frequent bot restarts during Phase 1 testing.
- [x] **Redirect LLM requests from Ollama to another provider** ([#29](https://github.com/garyseconomics/chatbot/issues/29)) -- Added Ollama Cloud as a provider with config settings `ollama_cloud_url`, `ollama_cloud_api_key`, and chat model `qwen3-next:80b`. Replaced the remote/local fallback with a configurable `chat_provider_priority` list that tries providers in order. Embeddings use a separate `embedding_provider_priority`.

### Deployment & Operations

- [x] **Improve Langfuse integration** ([#17](https://github.com/garyseconomics/chatbot/issues/17)) -- Enhanced observability setup. Dashboard visualization tracked in [#32](https://github.com/garyseconomics/chatbot/issues/32).
  - [x] Reuse Langfuse client in `llm_chat()` instead of creating a new one per call.
  - [x] Fix model name in trace metadata -- was always empty because `model_name` param wasn't passed by callers. Now reads `llm.model` which has the resolved name.
  - [x] Track retrieval step in Langfuse -- added `@observe` to `retrieve()` in `rag_manager.py` so vector search timing and results are visible.
  - [x] Raise error when Langfuse credentials are missing instead of silently failing.
  - [x] Replace `print()` with `logger.info()` in `get_llm_client()`.
  - [x] Propagate `user_id` from bot interfaces through the RAG pipeline to Langfuse traces.
  - [x] Verify on the Langfuse platform that traces show correct user IDs, model names, and retrieval steps.

### New functionality

- [x] **Discord bot DM support** ([#16](https://github.com/garyseconomics/chatbot/issues/16)) -- Added Direct Message support to the Discord bot. Uses `message.channel` instead of looking up the channel by name — works for both DMs and channel messages.

### Bug fixes

- [x] **Fix video link parsing** ([#14](https://github.com/garyseconomics/chatbot/issues/14)) -- `video_links.py` uses `strip()` to remove a path prefix, but `strip()` removes *characters*, not a substring -- this is a bug that causes wrong video links (e.g., truncated YouTube IDs). Rewrite using `Path` operations for correct and robust parsing.

### Project setup & cleanup

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

### Testing

- [x] **Ensure test coverage** -- Improve and expand the test suite.
  - [x] Add tests for `config.py`, `ollama_helpers.py`, `rag_manager.py` (retrieve, generate, error handling), `srt_splitter.py` (metadata, chunk size), and `process_in_batches()`.
  - [x] Fix env-dependent test failures in `test_llm_manager.py` (remote host tests now mock `settings.ollama_host_remote`).
  - [x] Fix test isolation in `test_vector_database.py` -- added `clean_database` fixture so each test sets up its own state and can run independently.
  - [x] Add tests for Telegram bot (`test_telegram_bot.py`) -- 5 tests covering /start greeting, RAG query invocation, answer delivery, video link appending when context has documents, and plain answer when context is empty.
  - [x] Add tests for CLI chatbot (`test_chatbot.py`) -- 4 tests covering greeting and answer output, RAG query invocation, video link printing, and skipping video text when no context. Refactored `chatbot.py` to extract `main()` with `if __name__ == "__main__":` guard for testability.
  - [x] Add tests for Discord bot (`test_discord_bot.py`) -- 7 tests covering basic behavior (ignores own messages, ignores non-mentions, responds when mentioned), error handling (channel not found, send failure), and on_ready (greeting, channel not found).
- [x] **Run tests and fix failures** -- Full suite green. Fixed tests that depended on `.env` being present (remote host tests now mock `settings.ollama_host_remote`).