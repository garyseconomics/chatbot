# TODO

Pending tasks and things to investigate.

## Pending tasks

- [x] **Use pyproject.toml** — Migrate from `requirements.txt` to `pyproject.toml` for project configuration and dependency management.
- [x] **Reorganize package structure** — Review and improve the directory/module layout.
- [ ] **Rethink configuration management** — Currently settings are split between `.env` (secrets, host URLs) and `config.py` (plain module-level variables). The boundary between them is unclear — e.g., `use_remote_llm` and model names are environment-dependent but hardcoded in `config.py`. Consider consolidating into a single approach with a clear rule: secrets and environment-specific values in `.env`, everything else derived from those or with sensible defaults in `config.py`. Evaluate whether `config.py` should use a structured approach (e.g., dataclass or pydantic settings) for validation and grouping.
- [ ] **Improve Ollama configuration for chatbot and embedding models** — Currently embeddings use the remote Ollama host (changed from local because local Ollama crashed the machine). The chatbot LLM supports remote/local with fallback, but embeddings have no fallback. Unify the configuration so both chatbot and embedding models can use remote or local Ollama, with consistent fallback behavior. Also add fallback for tests so they can run when the remote server is temporarily down.
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