# TODO

Pending tasks and things to investigate.

## Pending tasks

- [x] **Use pyproject.toml** — Migrate from `requirements.txt` to `pyproject.toml` for project configuration and dependency management.
- [x] **Reorganize package structure** — Review and improve the directory/module layout.
- [x] **Rethink configuration management** — Migrated to `pydantic-settings`. All settings consolidated in a single `Settings` class in `config.py` with typed fields, defaults, and automatic `.env` loading. All modules now use `from config import settings`.
- [x] **Improve Ollama configuration for chatbot and embedding models** — Unified with `ollama_helpers.get_available_ollama_host()`: pings remote first, falls back to local. Used by both LLM and embeddings. Removed `use_remote_llm` setting. Tests mock the connectivity check for reliable fallback testing.
- [ ] **Ensure test coverage** — Review existing tests and add missing coverage for all modules.
- [ ] **Run tests and fix failures** — Run the full test suite and fix any broken tests.
- [ ] **Clean up the code** — Apply clean code practices following CLAUDE.md conventions (PEP 8, type hints, ruff, small functions, etc.).
- [ ] **Improve Langfuse integration** — Enhance observability setup and add embedding tracking to Langfuse.

## To investigate

- [ ] **Async support** — Evaluate whether to use `asyncio` and `pytest-asyncio` for the
  Telegram and Discord bots. Currently the bots use their framework's async but the core
  RAG pipeline is synchronous. Consider if async would improve performance or simplify the bot code.
- [ ] **DSPy** — Framework for programming (not prompting) language models. Explore for
  prompt optimization and evaluation. See `prompt_experiments.py` for initial experiments.
- [ ] **MLflow** — Platform for tracking ML experiments, models, and metrics. Explore for
  tracking prompt experiments and RAG pipeline performance.