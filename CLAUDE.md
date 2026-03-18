# Gary's Economics Chatbot

A RAG chatbot that answers economics questions by referencing Gary's Economics YouTube videos.
It uses a vector database of video subtitles to provide context-aware answers via LLM.

## Repository layout

```
chatbot/
├── interfaces/             # Channel integrations
│   ├── chatbot.py          #   CLI chatbot interface
│   ├── telegram_bot.py     #   Telegram bot
│   └── discord_bot.py      #   Discord bot
├── llm/                    # LLM client management
│   ├── llm_manager.py      #   Ollama LLM wrapper (remote → local fallback)
│   ├── ollama_helpers.py   #   Host availability detection
│   └── prompt_template.py  #   RAG prompt template
├── rag/                    # RAG pipeline
│   ├── rag_manager.py      #   LangGraph retrieve → generate graph
│   └── video_links.py      #   YouTube video link generation
├── vector_database/        # Chroma vector DB operations
│   ├── vector_database_manager.py  # DB init, search, add documents
│   ├── import_documents.py         # Script to import SRT subtitles
│   ├── srt_splitter.py             # SRT chunking with overlap
│   └── collections_viewer.py       # DB inspection utility
├── docs/                   # SRT subtitle files (imported into vector DB)
│   └── import/             # Staging directory for new SRT files
├── tests/                  # pytest test suite
├── config.py               # Central configuration (pydantic-settings)
├── pyproject.toml          # Project metadata and dependencies
├── prompt_experiments.py   # Prompt experimentation scratch file
├── learning.md             # Developer learning tracker (checked by Claude)
├── TODO.md                 # Pending tasks and investigations
├── docker-compose.yml      # Docker Compose (Telegram bot service)
├── Dockerfile              # Docker image (Python 3.11-slim)
└── .github/workflows/      # CI/CD (Docker build + push to GHCR)
```

## Architecture overview

```
Channels (CLI / Telegram / Discord)
        │
        ▼
┌─────────────────┐
│   RAG Pipeline  │  ← LangGraph (retrieve → generate)
│  (RAG_manager)  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
Vector DB   LLM Manager
 (Chroma)   (Ollama: remote → local fallback)
```

1. **Channels** — CLI, Telegram bot, Discord bot. Each receives a question and calls the RAG pipeline.
2. **RAG pipeline** — LangGraph graph: retrieves relevant documents from the vector DB, builds a prompt with context, calls the LLM.
3. **Vector database** — Chroma with Ollama embeddings. Stores chunked SRT subtitles with video metadata.
4. **LLM manager** — Wraps Ollama clients. Primary: remote server (`qwen3:32b`). Fallback: local (`qwen3:4b`). Embeddings: `qwen3-embedding:8b`. Host selection is automatic via `ollama_helpers.get_available_ollama_host()`.

## Tech stack

- **Python 3.11+**
- **pytest** for testing
- **ruff** for linting and formatting
- **LangChain** + **LangGraph** for RAG pipeline and LLM integration
- **Chroma** (`chromadb`, `langchain-chroma`) as vector database
- **Ollama** (`langchain-ollama`) for LLM and embeddings
- **pydantic-settings** for typed configuration with automatic `.env` loading
- **Langfuse** for LLM observability and tracing
- **pysrt** for SRT subtitle parsing
- **python-dotenv** for environment variable loading
- **python-telegram-bot** and **discord.py** for bot integrations
- **Docker** + **GitHub Actions** for CI/CD

## Configuration

All settings live in `config.py` as a `pydantic-settings` `BaseSettings` class with typed fields, defaults, and automatic `.env` loading. Environment variables (API keys, tokens) in `.env` — see `.env.sample` for the template.

## Project philosophy

- **Learn by building.** Every piece of code should be understood by the developer.
- **Small iterations.** Deliver working value at each step. Each iteration should produce
  something you can run and test.
- **Tests for everything.** Product-oriented tests preferred (test behavior, not implementation).
- **Python first.** Use Python for everything. Other languages only if truly unavoidable.
- **Simple before clever.** Prefer straightforward code over abstractions. Add complexity only
  when the current code forces it.

## Working conventions

### For the developer
- Work interactively with Claude. Ask questions, discuss options.
- Review and understand all code before moving on.
- Run tests after every change.

### For Claude (AI assistant)
- **Check `learning.md`** at the start of each session. It tracks concepts the developer
  is learning. When these topics come up in code, explain them proactively.
  When the developer asks about a concept, add it to `learning.md`.
- **Check `TODO.md`** at the start of each session. It tracks pending tasks and things
  to investigate.
- **Ask, don't assume.** When there are meaningful choices to make, present options
  and discuss — don't decide silently.
- **Small steps.** Propose one thing at a time. Wait for feedback before moving on.
- **Explain the why.** When writing code, briefly explain design decisions.
- **Tests first.** When implementing new features or fixing bugs, write the tests first,
  then implement the code to make them pass.
- **No magic.** Avoid complex abstractions, metaprogramming, or "clever" patterns
  unless explicitly discussed and agreed upon.

### Code style
- Follow PEP 8 and standard Python conventions.
- Use type hints.
- Use `ruff` for linting and formatting.
- Keep functions small and focused.
- Docstrings only where the purpose isn't obvious from the name and signature.
- **Never remove existing comments** without asking first. Comments are there to help
  the developer understand the code — don't silently delete them.

### Testing
- Use `pytest`.
- Prefer product-oriented tests: test the behavior as a user would experience it.
- Mock external services (LLM API, Ollama, etc.) at the boundary.
- Test naming: `test_<what_it_does>` (e.g., `test_search_returns_relevant_documents`).
- **Tests must be deterministic.** Never rely on filesystem timestamps, real dates/times,
  or execution order for correctness. Use explicit values (e.g., `os.utime` for mtime)
  and `tmp_path` with controlled test data. Tests must pass on any machine at any time.

### Privacy and publishing
- This project is **open source** and published on GitHub.
- Never put personal information (names, paths, credentials) in tracked files.
- Anything private or local-only must go in files listed in `.gitignore`.
- **Never read `.env`** — it contains secrets (API keys, tokens). Use `.env.sample` to understand the expected variables.

### Running tests
```bash
source .venv/bin/activate
pytest
```

**Note on Ollama and tests:** Some tests (e.g., `test_vector_database.py`) call the Ollama embedding server. Host selection uses `ollama_helpers.get_available_ollama_host()` which pings remote first and falls back to local. Tests mock the connectivity check for reliable results. If both remote and local Ollama are unavailable, embedding-dependent tests will fail — this is expected.

### Git
- Small, focused commits.
- Commit messages: imperative mood, concise (e.g., "Add SRT chunking with overlap").