# TODO

Pending tasks and things to investigate.

## Urgent

- [ ] **Visualize user traces** ([#32](https://github.com/garyseconomics/chatbot/issues/32)) -- Configure Langfuse dashboard to show: (1) Q&A view — questions, answers, user name, timestamp; (2) Performance view — latency metrics, most active users. CLI viewer available as `python -m analytics.trace_viewer`. Fallback: build a Streamlit dashboard if Langfuse doesn't fit our needs.
- [ ] **Visualize metrics from Phase 1 day 1 session** ([#27](https://github.com/garyseconomics/chatbot/issues/27)) -- Pull metrics from Phase 1 day 1 testing session (Langfuse traces, latency, error rates, usage patterns).
- [ ] **Investigate why the bot has been resetting so many times** ([#28](https://github.com/garyseconomics/chatbot/issues/28)) -- Check server logs to identify the root cause of frequent bot restarts during Phase 1 testing.
- [ ] **Redirect LLM requests from Ollama to another provider** ([#29](https://github.com/garyseconomics/chatbot/issues/29)) -- Implement an alternative LLM provider to replace or supplement the self-hosted Ollama setup. Options to explore: [OpenRouter free models](https://openrouter.ai/models/?q=free) (API gateway with free-tier models), [Ollama Cloud](https://ollama.com/cloud) (free tier with session limits resetting every 5h and weekly limits every 7d, API endpoint: `https://ollama.com/api/chat`, OpenAI-compatible, requires API key — minimal code changes since we already use the Ollama API format).
- [ ] **Evaluate latency and stability with the new provider** ([#30](https://github.com/garyseconomics/chatbot/issues/30)) -- Measure latency and check if the bot crashes less after switching providers.
- [ ] **Finish Dockerize the application** ([#5](https://github.com/garyseconomics/chatbot/issues/5)) -- Remaining tasks: add MySQL service to docker-compose and auto-update containers. See Deployment & Operations section for details.


## Analytics

- [x] **Export traces from Langfuse** -- Fetch all traces from Langfuse, classify them as user or other, and store them as JSON files in `analytics/raw_data/`. Run with `python -m analytics.export`.
- [x] **Store user traces in MySQL database** -- Import clean user trace JSON files (from `analytics/raw_data/`) into a MySQL database for analysis. Script checks for duplicates before inserting. Run with `python -m analytics.setup_database` then `python -m analytics.user_trace_importer`.
  - [x] Create the `user_traces` table in MySQL (trace_id, user_id, question, answer, timestamp, model, latency, prompt_version).


## Deployment & Operations

- [ ] **Dockerize the application** ([#5](https://github.com/garyseconomics/chatbot/issues/5)) -- Create a Docker container with the application and all its dependencies to facilitate deployment on any server.
  - [x] Dockerfile and docker-compose.yml for Telegram bot.
  - [x] CI/CD workflow to build and push image to GHCR on every push.
  - [x] Restart policy (`unless-stopped`) so container recovers after server reset.
  - [x] Enable Discord bot in docker-compose (service exists but is commented out).
  - [ ] Add MySQL service to docker-compose ([#31](https://github.com/garyseconomics/chatbot/issues/31)) -- Add a `mysql` service with a persistent volume for data, and run `setup_database.py` automatically so the database is ready when the stack starts.
  - [ ] Auto-update running containers when a new image is pushed. Options: (1) Watchtower -- a container that monitors and auto-pulls new images, simplest for single-server; (2) Webhook-based deploy -- CI triggers a webhook on the server to run `docker compose pull && docker compose up -d`; (3) Cron job on the server that periodically pulls the latest image.
  - [ ] Run tests inside Docker image in CI ([#34](https://github.com/garyseconomics/chatbot/issues/34)) -- During Phase 1 day 2, the Docker image installed Langfuse v4 (breaking API change) while local tests ran against v3 and passed. Tests never caught the incompatibility because they only run locally, not against the Docker image. Add a CI step that runs `pytest` inside the built image before pushing.
- [ ] **Service watcher** ([#21](https://github.com/garyseconomics/chatbot/issues/21)) -- Monitor the bot service availability. Options: (1) HTTP `/health` endpoint polled by Uptime Kuma, or (2) a second bot that pings the main bot through the chat. Observer must run on a different host.
- [ ] **Remove RequestsDependencyWarning filters** -- `requests 2.32.5` doesn't recognize `chardet 7.0.1` as compatible, causing a harmless `RequestsDependencyWarning`. We added filters in `discord_bot.py` and `pyproject.toml` to suppress it. Once `requests` releases a new version with updated version bounds, remove the filters from both files.

## Bug fixes

- [ ] **Bot crashes when a user replies to a bot message in Discord** ([#23](https://github.com/garyseconomics/chatbot/issues/23)) -- When a user replies to one of the bot's messages mentioning the bot, the bot crashes with the generic error message. Need to check server logs to identify the root cause.
- [ ] **Telegram bot crashes on long LLM answers** ([#33](https://github.com/garyseconomics/chatbot/issues/33)) -- When the LLM returns an answer exceeding Telegram's 4096 character limit, `send_message` raises `telegram.error.BadRequest: Message is too long` and the user gets no response. Fix: split long messages into chunks or truncate.

## New functionality

- [ ] **Multi-turn conversations** ([#6](https://github.com/garyseconomics/chatbot/issues/6)) -- Enable conversations with multiple interactions by implementing chat memory and a conversation loop, so the LLM receives the history of the conversation on each call.

## RAG improvements

- [ ] **Bot lacks temporal awareness** ([#26](https://github.com/garyseconomics/chatbot/issues/26)) -- The bot treats all video content as equally recent because chunks have no date metadata. This causes confusion on time-sensitive topics (e.g., referencing the general election when asked about a recent by-election). Need to add video publish dates to chunk metadata and make the retrieval/generation pipeline date-aware.

## Prompt improvements

- [ ] **Evaluate prompt + LLM combinations** -- Test different prompt versions against different LLMs to find the best combination that meets all our requirements. Use Langfuse to run each combination against a set of test questions and compare results. The test questions from `tests/test_ask_questions.py` can be used as a starting dataset.
  - [ ] Store prompt versions in a MySQL table -- Move prompt text from `llm/prompt_template.py` to a `prompt_versions` table so different versions can be managed and referenced from traces.
  - [ ] Detect prompt version automatically in the importer -- Currently hardcoded to "2". The importer (`user_trace_importer.py`) should identify which prompt version was used for each trace.
  - [ ] **Hide RAG internals from the user** ([#22](https://github.com/garyseconomics/chatbot/issues/22)) -- The bot sometimes says things like "the provided content does not include..." or "based on the provided material...". The prompt must instruct the LLM to never reference "the provided content/material/context" and instead answer naturally. This is a requirement that the winning prompt+LLM combination must satisfy.
  - [ ] **Bot still impersonates Gary** ([#25](https://github.com/garyseconomics/chatbot/issues/25)) -- The bot still sometimes speaks as if it is Gary Stevenson. The winning combination must clearly distinguish the bot's identity from Gary's.
  - [ ] **Bot is too diplomatic — doesn't reflect the channel's tone and views** ([#24](https://github.com/garyseconomics/chatbot/issues/24)) -- The bot gives overly neutral answers on topics where the channel takes a clear position (e.g., crypto). The winning combination must reflect the channel's perspective.
  - [ ] **Bot lacks temporal awareness** ([#26](https://github.com/garyseconomics/chatbot/issues/26)) -- The prompt must handle date-aware context correctly. This is the second part of the RAG temporal awareness task: first the vector database needs to be updated with video publish dates (see RAG improvements section), then the prompt must be tested to ensure the winning combination uses temporal metadata properly.

## To investigate

- [ ] **Async support** -- Evaluate whether to use `asyncio` for the core RAG pipeline.
  Currently the bots use their framework's async but the RAG pipeline is synchronous.
  Consider if async would improve performance or simplify the bot code. Note:
  `pytest-asyncio` is already installed and used for Discord and Telegram bot handler tests.
- [ ] **DSPy** -- Framework for programming (not prompting) language models. Explore for
  prompt optimization and evaluation. See `prompt_experiments.py` for initial experiments.
- [ ] **MLflow** -- Platform for tracking ML experiments, models, and metrics. Explore for
  tracking prompt experiments and RAG pipeline performance.

## Done Tasks

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