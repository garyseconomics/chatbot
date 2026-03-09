# TODO

Pending tasks and things to investigate.

## Pending tasks

- [ ] **Use pyproject.toml** — Migrate from `requirements.txt` to `pyproject.toml` for project configuration and dependency management.
- [ ] **Reorganize package structure** — Review and improve the directory/module layout.
- [ ] **Clean up the code** — Apply clean code practices following CLAUDE.md conventions (PEP 8, type hints, ruff, small functions, etc.).
- [ ] **Ensure test coverage** — Review existing tests and add missing coverage for all modules.
- [ ] **Run tests and fix failures** — Run the full test suite and fix any broken tests.
- [ ] **Improve Langfuse integration** — Enhance observability setup and add embedding tracking to Langfuse.

## To investigate

- [ ] **Async support** — Evaluate whether to use `asyncio` and `pytest-asyncio` for the
  Telegram and Discord bots. Currently the bots use their framework's async but the core
  RAG pipeline is synchronous. Consider if async would improve performance or simplify the bot code.
- [ ] **DSPy** — Framework for programming (not prompting) language models. Explore for
  prompt optimization and evaluation. See `prompt_experiments.py` for initial experiments.
- [ ] **MLflow** — Platform for tracking ML experiments, models, and metrics. Explore for
  tracking prompt experiments and RAG pipeline performance.