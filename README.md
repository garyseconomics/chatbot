# Gary's Economics Chatbot 

A prototype chatbot designed to answer questions by referencing videos from Gary's Economics YouTube channel.

## Repository layout

```
chatbot/
├── src/                    # Application source code
│   ├── interfaces/             # Channel integrations
│   │   ├── chatbot.py          #   CLI chatbot interface
│   │   ├── telegram_bot.py     #   Telegram bot
│   │   └── discord_bot.py      #   Discord bot
│   ├── llm/                    # LLM client management
│   │   ├── llm_manager.py      #   Multi-provider Ollama wrapper (priority-based fallback)
│   │   ├── prompt_template.py  #   RAG prompt builder (reads from prompt_versions)
│   │   └── prompt_versions.py  #   Versioned prompt texts (v1–v4+)
│   ├── rag/                    # RAG pipeline
│   │   ├── rag_manager.py      #   LangGraph retrieve → generate graph
│   │   ├── vector_database.py  #   Chroma vector store factory for query-time access
│   │   ├── video_links.py      #   YouTube video link generation
│   │   └── langfuse_helpers.py #   Langfuse tracing utilities
│   └── config.py               # Central configuration (pydantic-settings)
├── data/                   # Vector database copy (Chroma) — see "Include a copy of the database"
├── tests/                  # pytest test suite (main chatbot)
├── analytics/              # Analytics scripts and data
│   ├── config.py               # Analytics configuration
│   ├── db/                     # Database setup + import/export pipeline
│   │   ├── export.py               # Langfuse trace export
│   │   ├── setup_database.py       # SQLite analytics DB setup
│   │   └── trace_importer.py       # Import traces from Langfuse export
│   ├── scripts/                # Manual tools and one-off tasks
│   │   ├── ask_questions.py    # Batch question runner
│   │   ├── questions_for_testing.py   # Test question sets
│   │   ├── test_cloud_limits.py    # Cloud provider limit testing
│   │   ├── trace_viewer.py        # Trace inspection utility
│   │   └── trace_viewer_old.py    # Viewer for pre-2026-03-28 data (analytics_old.db)
│   └── raw_data/              # Exported trace data (JSON/CSV)
├── plan/                   # Project plans and reports
│   ├── phase_1/               # Testing Phase 1 reports
│   └── phase_2/               # Testing Phase 2 plans and evaluation
├── pyproject.toml          # Project metadata and dependencies
├── docker-compose.yml      # Docker Compose (Telegram + Discord bot services)
├── Dockerfile              # Docker image (Python 3.11-slim)
└── .github/workflows/      # CI/CD (Docker build + push to GHCR)
```

> **Note:** Content import, transcripts, and database generation now live in the separate
> [chatbot-database](https://github.com/garyseconomics/chatbot-database) repo. This repo only
> **consumes** a pre-built vector database at runtime.

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
 (Chroma)   (Ollama: priority-based provider fallback)
```

1. **Channels** — CLI, Telegram bot, Discord bot. Each receives a question and calls the RAG pipeline.
2. **RAG pipeline** — LangGraph graph: retrieves relevant documents from the vector DB, builds a versioned prompt with context, calls the LLM.
3. **Vector database** — Chroma with Ollama embeddings. Stores chunked SRT subtitles with video metadata. Content import and database generation live in the separate [chatbot-database](https://github.com/garyseconomics/chatbot-database) repo; this repo only **consumes** the database at runtime via `src/rag/vector_database.py`.
4. **LLM manager** — Wraps multiple chat and embeddings providers (Ollama and OpenAI-compatible, e.g. OpenRouter) and uses the first available one by priority. Chat falls back from cloud to self-hosted (`qwen3:32b`) to local (`qwen3:4b`), then to OpenAI-compatible providers. The provider order and the model used for each are configured in `src/config.py` (the specific cloud models change over time as providers update their offerings).
5. **Analytics** — SQLite database for traces (questions, answers, latency, models, vector search results). Imported from Langfuse. Scripts in `analytics/`. See [analytics/ANALYTICS_GUIDE.md](analytics/ANALYTICS_GUIDE.md) for details.

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

## Prerequisites

### Install Ollama and download the models

We use Large Language Models (LLMs) for two things: embedding documents into the vector database, and answering user questions. All models run through [Ollama](https://ollama.com/).

Install Ollama:
```bash
sudo apt install curl
curl -fsSL https://ollama.com/install.sh | sh
```

**Embedding model** — used to process subtitles before importing them to the vector database. The process is called [embedding](https://en.wikipedia.org/wiki/Embedding_(machine_learning)): it converts text into numerical vectors that represent concepts, which are later used to find related content when searching.

```bash
ollama pull qwen3-embedding:8b
```

You can use a different embedding model — check the [Ollama library](https://ollama.com/library?sort=newest&q=embedding) for options and change `embeddings_model` in `src/config.py`.

**Chat model** — used to answer user questions. The chatbot tries providers in priority order configured in `src/config.py` (cloud and self-hosted Ollama, then a local fallback, then OpenAI-compatible providers such as OpenRouter). To use the local fallback:

```bash
ollama pull qwen3:4b
```

### Configure the environment variables

**IMPORTANT**: The `.env` file contains secret keys and is not in the repository. Create your own by copying `.env.sample`:

```bash
cp .env.sample .env
```

Then fill in the values. The available variables are:

**Ollama servers**
- `OLLAMA_LOCAL_HOST_URL` — URL of the local Ollama server. Defaults to `http://localhost:11434`.
- `OLLAMA_SELF_HOSTED_URL` — URL of the self-hosted Ollama server.
- `OLLAMA_CLOUD_URL` — URL of the cloud Ollama provider.
- `OLLAMA_CLOUD_API_KEY` — API key for the cloud Ollama provider.

**Backup LLM Providers**
- `OPENROUTER_API_KEY` - API key for [OpenRouter](https://openrouter.ai) they have a decent free tier to be used as a backup.

**Bot tokens**
- `TELEGRAM_TOKEN` — Token for the Telegram bot. You get this when you [create a bot with BotFather](#create-a-telegram-bot).
- `DISCORD_TOKEN` — Token for the Discord bot. You need a bot installed on a server with permission to read and send messages.

**Observability**
- `LANGFUSE_PUBLIC_KEY` — Public key for the [Langfuse](https://langfuse.com/) observability platform.
- `LANGFUSE_SECRET_KEY` — Secret key for Langfuse.
- `LANGFUSE_HOST` — Langfuse server URL. Defaults to `https://cloud.langfuse.com`.

**Vector database**
- `DATABASE_PATH` — Path to the Chroma database directory where you place the downloaded database. E.g. `./data`.

### Include a copy of the database

To run the application you need the vector database with the processed subtitles. You can use a pre-built copy (recommended) or generate your own.

Using a pre-built copy:
- Download [`chroma.sqlite3`](https://github.com/garyseconomics/chatbot-database/blob/main/data/chroma.sqlite3) from the [chatbot-database](https://github.com/garyseconomics/chatbot-database) repository.
- Place it at `./data/chroma.sqlite3` (matching `DATABASE_PATH`).

Alternatively, you can generate your own database (import transcripts, build the embeddings) using the [chatbot-database](https://github.com/garyseconomics/chatbot-database) repo.

### Configuration

All configuration is managed through [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) classes. Environment variables from `.env` are loaded automatically — each field maps to an env var of the same name. Fields not set in `.env` use the defaults defined in the class.

There are two config files:
- `src/config.py` — Main application settings (LLM providers, provider priority, bot tokens, Langfuse, vector database). Includes the query-time settings `embeddings_model`, `collection_name`, and `video_ids_separator`.
- `analytics/config.py` — Analytics settings (database path, Langfuse keys).

Some variables in `.env` are shared across config files — the database path, Ollama URLs, API keys, and Langfuse keys are read by more than one config. (The import-side settings used to build the database now live in the separate [chatbot-database](https://github.com/garyseconomics/chatbot-database) repo.)

## Setup with Docker

```bash
docker compose build
docker compose up
```

Or, to run in the background with automatic restart:
```bash
docker compose up -d
```

## Setup without Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .
```

This reads `pyproject.toml` and installs all dependencies. To also install development tools (ruff, pytest):
```bash
pip install ".[dev]"
```

## Usage

Activate the virtual environment first (not needed with Docker):
```bash
source .venv/bin/activate
```

### Build or update the database

The chatbot uses video subtitles (SRT format) as its knowledge base. Building or updating the vector database (importing transcripts, generating embeddings) is handled in the [chatbot-database](https://github.com/garyseconomics/chatbot-database) repo. This repo consumes a pre-built database — see [Include a copy of the database](#include-a-copy-of-the-database).

### CLI chatbot

```bash
python -m interfaces.chatbot
```

The chatbot will greet you and ask for a question. It searches the vector database for relevant context and uses it to generate an answer. Answers are better when the uploaded subtitles cover the topic asked about.

<img width="1863" height="615" alt="Image" src="https://github.com/user-attachments/assets/7acdd1cb-0aa7-4137-8ad8-3d719fb13b3c" />

### Telegram chatbot

#### Create a Telegram bot

- Open the Telegram app (or [web version](https://web.telegram.org/)).
- Start a conversation with **@BotFather** (look for the blue checkmark).

<img width="446" height="424" alt="Image" src="https://github.com/user-attachments/assets/dc86f1e5-a957-43d6-ba65-94ab377a26d5" />

- Send `/newbot` and follow the prompts to choose a name and username.
- BotFather will give you a URL to access your bot and a token.

<img width="776" height="457" alt="Image" src="https://github.com/user-attachments/assets/1865122a-8d1d-462b-ad57-71aa12f5ae90" />

- Copy the token to `TELEGRAM_TOKEN` in your `.env` file.

More information: [Telegram Bot Tutorial](https://core.telegram.org/bots/tutorial#obtain-your-bot-token).

#### Launch the Telegram bot

```bash
python -m interfaces.telegram_bot
```

### Discord chatbot

- Add the Discord token to your `.env` file as `DISCORD_TOKEN`.
- Set the channel name as `DISCORD_CHANNEL` in `.env` (or change the default in `src/config.py`).
- Launch the bot:

```bash
python -m interfaces.discord_bot
```

The bot supports two modes of interaction:
- **In channels**: mention the bot with @botname followed by your question.
- **In DMs**: send a message directly to the bot — no mention needed.

## Testing

```bash
pytest                                    # main chatbot tests
```

## Testing plan

We are rolling out the chatbot in phases. See the [plan/](plan/) folder for details.
