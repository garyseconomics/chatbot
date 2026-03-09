# TODO

Pending tasks and things to investigate.

## Pending tasks

- [x] **Use pyproject.toml** — Migrate from `requirements.txt` to `pyproject.toml` for project configuration and dependency management.
- [x] **Reorganize package structure** — Review and improve the directory/module layout.
- [x] **Rethink configuration management** — Migrated to `pydantic-settings`. All settings consolidated in a single `Settings` class in `config.py` with typed fields, defaults, and automatic `.env` loading. All modules now use `from config import settings`.
- [x] **Improve Ollama configuration for chatbot and embedding models** — Unified with `ollama_helpers.get_available_ollama_host()`: pings remote first, falls back to local. Used by both LLM and embeddings. Removed `use_remote_llm` setting. Tests mock the connectivity check for reliable fallback testing.
- [x] **Ensure test coverage** — Added tests for `config.py`, `ollama_helpers.py`, `rag_manager.py` (retrieve, generate, error handling), `srt_splitter.py` (metadata, chunk size), and `process_in_batches()`. Fixed env-dependent test failures in `test_llm_manager.py`. 51 tests, all passing.
- [x] **Run tests and fix failures** — Full suite green. Fixed tests that depended on `.env` being present (remote host tests now mock `settings.ollama_host_remote`).
- [ ] **Clean up the code** — Apply clean code practices following CLAUDE.md conventions (PEP 8, type hints, ruff, small functions, etc.).
  - [x] Fix typos in `rag_manager.py` ("querying", "technical").
  - [x] Move `ollama_helpers.py` into `llm/` package where it logically belongs.
  - [x] Run `ruff check --fix` and `ruff format` across the codebase — fixed import sorting, tabs→spaces, trailing newlines, `== None`→`is None`, unused imports, consistent formatting (13 files reformatted).
  - [x] Fix long lines (E501) — shortened comments in `telegram_bot.py` and `import_documents.py`, split long strings in `prompt_template.py` and `test_vector_database.py`.
  - [x] Replace star import in `test_vector_database.py` with explicit imports.
  - [x] Fix duplicate condition bug in `import_documents.py` (`answer == "y" or answer == "y"` → `answer.strip().lower() in ("y", "yes")`).
  - [x] Extract prompt string as `RAG_PROMPT_TEXT` constant in `prompt_template.py`.
  - [x] Fix test isolation in `test_vector_database.py` — added `clean_database` fixture so each test sets up its own state and can run independently.
  - [ ] Add `if __name__ == "__main__":` guards to `import_documents.py` and `collections_viewer.py` (they run code at import time).
  - [ ] Add error handling to Discord bot `on_message` handler (currently crashes silently if `RAG_query()` fails).
  - [ ] Add type hints to files that are missing them (`video_links.py`, `llm_manager.py`, interfaces).
  - [ ] Replace `print()` with `logging` module throughout the codebase for consistent log handling.
  - [ ] Reuse Langfuse client in `llm_chat()` instead of creating a new one per call.
  - [ ] Improve generic `except Exception` in `RAG_query()` with more specific error handling.
  - [ ] Add tests for interfaces (Telegram bot, Discord bot, CLI chatbot).
- [ ] **Fix video link parsing** — `video_links.py` uses `strip()` to remove a path prefix, but `strip()` removes *characters*, not a substring — this is a bug. Rewrite using `Path` operations for correct and robust parsing.
- [ ] **Improve Langfuse integration** — Enhance observability setup and add embedding tracking to Langfuse.

## To investigate

- [ ] **Async support** — Evaluate whether to use `asyncio` and `pytest-asyncio` for the
  Telegram and Discord bots. Currently the bots use their framework's async but the core
  RAG pipeline is synchronous. Consider if async would improve performance or simplify the bot code.
- [ ] **DSPy** — Framework for programming (not prompting) language models. Explore for
  prompt optimization and evaluation. See `prompt_experiments.py` for initial experiments.
- [ ] **MLflow** — Platform for tracking ML experiments, models, and metrics. Explore for
  tracking prompt experiments and RAG pipeline performance.