# TODO

Pending tasks and things to investigate.

## Priority 1

- [ ] **Visualize user traces** ([#32](https://github.com/garyseconomics/chatbot/issues/32)) -- Configure Langfuse dashboard to show: (1) Q&A view — questions, answers, user name, timestamp; (2) Performance view — latency metrics, most active users. CLI viewer available as `python -m analytics.trace_viewer`. Fallback: build a Streamlit dashboard if Langfuse doesn't fit our needs.
- [ ] **Evaluate latency and stability with the new provider** ([#30](https://github.com/garyseconomics/chatbot/issues/30)) -- Measure latency and check if the bot crashes less after switching providers.
- [ ] **Improve error handling in Discord and Telegram bots** -- Currently the Discord bot catches all exceptions in `on_message` and sends a hardcoded error string. The Telegram bot has no error handling at all outside of `RAG_query`. Improvements needed: (1) Replace the hardcoded Discord error message with `settings.error_messages` (use `DefaultError` for now since the only realistic exception outside `RAG_query` is `discord.HTTPException` from message-too-long); (2) Add try/except to Telegram's `question()` handler like Discord has; (3) Consider adding specific error types like `HTTPException` to `settings.error_messages` once #33 (message length handling) is addressed. Note: `RAG_query` already catches all exceptions internally and returns error messages from `settings.error_messages`, so the bot-level `except` blocks only trigger for failures outside `RAG_query` (e.g., `message.channel.send` or `context.bot.send_message`).

## Deployment & Operations

- [ ] **Remove RequestsDependencyWarning filters** -- `requests 2.32.5` doesn't recognize `chardet 7.0.1` as compatible, causing a harmless `RequestsDependencyWarning`. We added filters in `discord_bot.py` and `pyproject.toml` to suppress it. Once `requests` releases a new version with updated version bounds, remove the filters from both files.
- [ ] **Run tests inside Docker image in CI** ([#34](https://github.com/garyseconomics/chatbot/issues/34)) -- Add a CI step that runs `pytest` inside the built Docker image before pushing to GHCR. During Phase 1 day 2, a Langfuse v3→v4 breaking change was only caught in production because tests only ran locally.
- [ ] **Auto-update running containers when a new image is pushed** -- Options: (1) Watchtower -- a container that monitors and auto-pulls new images, simplest for single-server; (2) Webhook-based deploy -- CI triggers a webhook on the server to run `docker compose pull && docker compose up -d`; (3) Cron job on the server that periodically pulls the latest image.
- [ ] **Service watcher** ([#21](https://github.com/garyseconomics/chatbot/issues/21)) -- Monitor the bot service availability. Options: (1) HTTP `/health` endpoint polled by Uptime Kuma, or (2) a second bot that pings the main bot through the chat. Observer must run on a different host.

## New functionality
- [ ] **Add other OpenAI-compatible providers** ([#29](https://github.com/garyseconomics/chatbot/issues/29)) -- Generalize the provider abstraction to support providers like [OpenRouter](https://openrouter.ai/models/?q=free). Currently `_create_chat_client()` always returns `ChatOllama` — needs to select the right LangChain class based on provider type. Combine with the prompt+LLM evaluation task (see Prompt improvements section) to test different model/prompt combinations.
- [ ] **Multi-turn conversations** ([#6](https://github.com/garyseconomics/chatbot/issues/6)) -- Enable conversations with multiple interactions by implementing chat memory and a conversation loop, so the LLM receives the history of the conversation on each call. One of the most requested features from Phase 1 testers. Plan: implement, test, measure the extra cost (longer prompts = more tokens), then check with Gary's team whether to enable it for Phase 2. Note: the CLI chatbot will become a loop, so the current `asyncio.run()` wrapper (one-shot call) will need to change — likely to an async `main()` with `asyncio.run(main())` at the entry point.
- [ ] **Chat sessions** -- `LLM_Client` currently creates a new instance per call in `generate()`. For multi-turn conversations, a single instance should persist across the session to track `provider_name` and reuse the working provider.

## RAG improvements

- [ ] **Add more content to the vector database** -- The current database only includes video subtitles from early 2024 to November 2025. Several important sources are missing. See `prompt_issues/prompt_issues.md` (Source Material Gaps) for the full list.
  - [ ] Add subtitles for videos after November 2025.
  - [ ] Clean up and import transcripts from [garyseconomics/transcripts](https://github.com/garyseconomics/transcripts/tree/main/transcripts) ([#39](https://github.com/garyseconomics/chatbot/issues/39)) — these need review before they can be used. Clean subtitles should be added to [garyseconomics/subtitle-data](https://github.com/garyseconomics/subtitle-data).
  - [ ] Add older videos (pre-2024) — YouTube's auto-generated subtitles from that era were poor quality. Can regenerate with current AI speech-to-text for better results.
  - [ ] Cambridge talk, Gary's book, interviews on other channels (need permission), Gary's university thesis.
- [ ] **Bot lacks temporal awareness** ([#26](https://github.com/garyseconomics/chatbot/issues/26)) -- The bot treats all video content as equally recent because chunks have no date metadata. This causes confusion on time-sensitive topics (e.g., referencing the general election when asked about a recent by-election). Solving together with #36 (inline video links) — each subtitle fragment in the prompt will carry its video link and publish date, so the LLM can reason about recency.
  - [ ] **Step 1: Rename SRT files to include publish dates** -- 14 of 39 files already have dates in the filename (`VIDEO_ID__YYYY-MM-DD_Title.srt`). Look up publish dates for the remaining 25 files and rename them to match the same format.
  - [ ] **Step 2: Regenerate the vector database with date metadata** -- Update the import process (`srt_splitter.py`) to extract the publish date from the filename and store it in chunk metadata. Then regenerate the database so all chunks carry their video's publish date.
  - [ ] **Step 3: Write tests for the new prompt format** -- Tests first. Write tests for the new context formatting that includes video links and dates with each subtitle fragment.
  - [ ] **Step 4: Include dates and video links with each fragment in the prompt** -- Change `generate()` in `rag_manager.py` to format each chunk with its publish date and YouTube link. The LLM already knows the current date via `{current_datetime}`, so it can reason about which content is recent.

## Prompt improvements

- [ ] **Evaluate prompt + LLM combinations** ([#37](https://github.com/garyseconomics/chatbot/issues/37)) -- Test different prompt versions against different LLMs to find the best combination that meets all our requirements. Use Langfuse to run each combination against a set of test questions and compare results. The test questions from `tests/test_ask_questions.py` can be used as a starting dataset (selected in commit d11929e). `RAG_query` now returns `chat_model` so results can be tracked per model (commit aa78166). Covers the behaviour issues from Phase 1 testing (previously tracked as #22, #24, #25 — now closed and centralized in #37): bot exposes RAG internals, bot is too diplomatic, bot impersonates Gary, bot answers out-of-scope questions, bot gives financial advice, bot fabricates Gary's opinions, bot can be manipulated. Full list in `testing_phase_1/feedback_report.md`. Related: #26 (temporal awareness, tracked separately). When in doubt about whether Gary has covered a topic, check the subtitle repos: [subtitle-data](https://github.com/garyseconomics/subtitle-data) (imported into vector DB) and [transcripts](https://github.com/garyseconomics/transcripts/tree/main/transcripts) (to be cleaned up for import).
  - [ ] **Include video links inline with subtitle fragments in the prompt** ([#36](https://github.com/garyseconomics/chatbot/issues/36)) -- Currently video links are appended as a separate block at the end of the response. Instead, each subtitle fragment provided as context should carry its own video link, so the LLM can reference the correct source naturally within the answer. This is tied to #33 (message length) since inline links change how much space the response uses, and to the video link handling rework noted there. **Being implemented as part of #26 (temporal awareness) — see RAG improvements section.**
  - [ ] Store prompt versions in the analytics database -- Move prompt text from `llm/prompt_template.py` to a `prompt_versions` table in SQLite so different versions can be managed and referenced from traces.
  - [ ] Detect prompt version automatically in the importer -- Currently hardcoded to "2". The importer (`user_trace_importer.py`) should identify which prompt version was used for each trace.

## To investigate

- [ ] **LLM-as-judge evaluation pipeline** (part of [#37](https://github.com/garyseconomics/chatbot/issues/37)) -- Run each test question against multiple (prompt × model) combinations and use an LLM judge to evaluate whether the answer meets the expected behavior criteria. This gives a systematic way to compare prompt versions and model backends. Tasks: (1) define evaluation dataset format and create initial entries from known issues; (2) build the eval pipeline to run questions against combinations; (3) implement LLM-as-judge scoring against expected behavior criteria; (4) store results in a database/file for comparison across runs; (5) re-run the eval pipeline after each prompt change to check for regressions.
- [ ] **DSPy** -- Framework for programming (not prompting) language models. Explore for
  prompt optimization and evaluation. See `prompt_experiments.py` for initial experiments.
- [ ] **MLflow** -- Platform for tracking ML experiments, models, and metrics. Explore for
  tracking prompt experiments and RAG pipeline performance.

## Done Tasks

### Bug fixes — Testing Phase 1

- [x] **Bot crashes when a user replies to a bot message in Discord** ([#23](https://github.com/garyseconomics/chatbot/issues/23)) -- When a user replies to one of the bot's messages, the bot crashes with the generic error message. Could not reproduce (2026-03-21): retested all four crash examples from the original report — bot handled all of them without errors. The original crashes were most likely caused by Discord's 2000-char message limit (#33) or intermittent Ollama Cloud 500 errors (#29), both of which have since been addressed.
- [x] **Investigate why the bot has been resetting so many times** ([#28](https://github.com/garyseconomics/chatbot/issues/28)) -- Check server logs to identify the root cause of frequent bot restarts during Phase 1 testing.
- [x] **Intermittent Ollama Cloud 500 errors** ([#29](https://github.com/garyseconomics/chatbot/issues/29)) -- Ollama Cloud sometimes returns `ResponseError: Internal Server Error (status code: 500)`. Root cause: Ollama Cloud enforces a strict concurrency limit — max 2 active requests + 5 queued (headers: `x-ratelimit-max-concurrent: 2`, `x-ratelimit-queue-limit: 5`). Requests beyond that get rejected (429/500). Reproduced with `debug_cloud_500.py` (10 concurrent requests, 3 rejected). Addressed by the `LLM_Client` refactor: `chat()` now falls back to the next provider when `invoke()` fails, and `_select_provider()` retries with error reset after exhausting all providers. Tests force self-hosted Ollama via `use_ollama_for_testing` fixture to avoid flaky cloud errors.
- [x] **Bots crash on long LLM answers** ([#33](https://github.com/garyseconomics/chatbot/issues/33)) -- Quick fix: added `max_tokens` setting (500 tokens) passed as `num_predict` to ChatOllama to limit LLM response length. This keeps answers under Discord's 2000-char and Telegram's 4096-char limits. **Future improvements needed:** (1) check final message length before sending to Telegram/Discord and split or truncate if it exceeds the platform limit; (2) rethink how video links are integrated into messages — the current approach of appending links affects total message length and will change when we improve video link handling.
- [x] **Thinking models consume `num_predict` with thinking tokens** -- `qwen3-next:80b` (Ollama Cloud) uses a thinking mode where internal reasoning tokens count against the `num_predict` limit. With `max_tokens=500`, the model spent all tokens thinking and returned empty answers. **Fix:** removed `num_predict` / `max_tokens` entirely (2026-03-21). The message length problem (#33) should be solved on the sending side (split/truncate before sending to Discord/Telegram) instead of limiting the LLM output.

### Bug fixes — Testing Phase 0

- [x] **Fix video link parsing** ([#14](https://github.com/garyseconomics/chatbot/issues/14)) -- `video_links.py` uses `strip()` to remove a path prefix, but `strip()` removes *characters*, not a substring -- this is a bug that causes wrong video links (e.g., truncated YouTube IDs). Rewrite using `Path` operations for correct and robust parsing.

### Async RAG pipeline ([#38](https://github.com/garyseconomics/chatbot/issues/38))

- [x] **Make RAG_query async (Phase 1)** -- `RAG_query` is now `async def` and uses `graph.ainvoke()`. The internal functions (`retrieve`, `generate`, `llm_chat`) are still sync — LangGraph runs them in threads automatically. Error handling simplified to a single `except` block with configurable messages in `settings.error_messages`.
- [x] **Improve error messages** -- Error messages moved to `settings.error_messages` dict in `config.py`, keyed by exception class name. `RAG_query` looks up `type(e).__name__` and returns a user-facing message. Default message under `"DefaultError"` key.
- [x] **Make RAG_query async (Phase 2)** -- Pipeline is now fully async end-to-end. `retrieve()` uses `await vector_store.asimilarity_search()`, `generate()` uses `await client.chat()`, and `LLM_Client.chat()` uses `await llm.ainvoke()`. All LLM manager tests updated to async. No more sync functions running in LangGraph's thread pool.
- [x] **Update callers and tests for async RAG_query** -- All callers updated: Discord bot (`create_task`), Telegram bot (`await`), CLI chatbot (`asyncio.run`). All tests updated and simplified: `test_rag_manager.py` (3 tests, zero mocks), `test_chatbot.py` (1 test, 2 mocks), `test_telegram_bot.py` (2 tests, 2 mocks), `test_ask_questions.py` (async). Ruff clean. Final commit: 2d15125.

### LLM management

- [x] **Refactor LLM management into `LLM_Client` class** -- Consolidated all provider management (`llm_manager.py` + `llm_providers_helpers.py`) into a single `LLM_Client` class. `chat()` tries providers in priority order and falls back on invoke failure. `get_embedding_model()` returns an embedding model from the first available provider. `_select_provider()` handles both chat and embeddings with retry logic (do-while loop, error reset, `max_attempts` safety net). `providers_errors` dict tracks all failures. Callers (`rag_manager.py`, `vector_database_manager.py`) now use `LLM_Client` — no longer need to know about Ollama internals. `llm_providers_helpers.py` and its tests deleted. 12 tests including 3 error-path tests with `pytest.raises`.
- [x] **Embedding provider fallback** -- `get_embedding_model()` currently uses the first available provider with no invoke-level fallback. If a cloud embedding provider is added in the future, it should have the same retry/fallback logic as `chat()`.

### Analytics

- [x] **Export traces from Langfuse** -- Fetch all traces from Langfuse, classify them as user or other, and store them as JSON files in `analytics/raw_data/`. Run with `python -m analytics.export`.
- [x] **Store user traces in database** -- Import clean user trace JSON files (from `analytics/raw_data/`) into a SQLite database for analysis. Script checks for duplicates before inserting. Run with `python -m analytics.setup_database` then `python -m analytics.user_trace_importer`. Originally built with MySQL, switched to SQLite (2026-03-20) — no server needed.
  - [x] Create the `user_traces` table in SQLite (trace_id, user_id, question, answer, timestamp, model, latency, prompt_version).
- [x] **Visualize metrics from Phase 1 day 1 session** ([#27](https://github.com/garyseconomics/chatbot/issues/27)) -- Pull metrics from Phase 1 day 1 testing session (Langfuse traces, latency, error rates, usage patterns).

### Deployment & Operations

- [x] **Redirect LLM requests from Ollama to another provider** ([#29](https://github.com/garyseconomics/chatbot/issues/29)) -- Added Ollama Cloud as a provider with config settings `ollama_cloud_url`, `ollama_cloud_api_key`, and chat model `qwen3-next:80b`. Replaced the remote/local fallback with a configurable `chat_provider_priority` list that tries providers in order. Embeddings use a separate `embedding_provider_priority`.
- [x] **Dockerize the application** ([#5](https://github.com/garyseconomics/chatbot/issues/5)) -- Create a Docker container with the application and all its dependencies to facilitate deployment on any server. Dockerfile and docker-compose.yml for Telegram bot. CI/CD workflow to build and push image to GHCR on every push. Restart policy (`unless-stopped`) so container recovers after server reset. Discord bot enabled in docker-compose. ~~Add MySQL service~~ — switched to SQLite, no service required.
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
