# Gary's Economics Chatbot 

A prototype chatbot that answers questions by referencing videos from Gary's Economics YouTube channel. You can talk to it through a CLI, a Telegram bot or a Discord bot.

The chatbot doesn't search the videos itself. It sends each question to the [Gary's Economics MCP server](https://github.com/garyseconomics/MCP_server), which finds the relevant transcripts and writes the answer. The transcripts are imported and turned into a vector database in the [chatbot-database](https://github.com/garyseconomics/chatbot-database) repo.

## Repository layout

```
chatbot/
├── src/                    # Application source code
│   ├── interfaces/             # Channel integrations
│   │   ├── chatbot.py          #   CLI chatbot interface
│   │   ├── telegram_bot.py     #   Telegram bot
│   │   ├── discord_bot.py      #   Discord bot
│   │   └── chunker.py          #   Splits long answers to fit Telegram and Discord message limits
│   ├── mcp_client/             # Connection to the MCP server
│   │   └── mcp_manager.py      #   Sends questions to the MCP server's RAG tool
│   ├── llm/                    # LLM client management (not used yet, kept for choosing MCP tools)
│   │   ├── llm_manager.py      #   Multi-provider Ollama wrapper (priority-based fallback)
│   │   ├── prompt_template.py  #   RAG prompt builder (reads from prompt_versions)
│   │   └── prompt_versions.py  #   Versioned prompt texts (v1–v4+)
│   ├── tracing/                # Observability
│   │   └── langfuse_helpers.py #   Langfuse tracing utilities
│   └── config.py               # Central configuration (pydantic-settings)
├── tests/                  # pytest test suite
├── plan/                   # Project plans and reports
│   ├── phase_1/               # Testing Phase 1 reports
│   └── phase_2/               # Testing Phase 2 plans and evaluation
├── pyproject.toml          # Project metadata and dependencies
├── docker-compose.yml      # Docker Compose (Telegram + Discord bot services)
├── Dockerfile              # Docker image (Python 3.11-slim)
├── .devcontainer/          # Dev container used to run the tests in CI
└── .github/workflows/      # CI/CD (tests, Docker build + push to GHCR)
```

## Architecture overview

```
Channels (CLI / Telegram / Discord)
        │  question
        ▼
┌──────────────────┐
│    MCP client    │  ← src/mcp_client/mcp_manager.py
│   (MCP_query)    │
└────────┬─────────┘
         │  retrieval_augmented_generation tool
         ▼
Gary's Economics MCP server
(searches the transcripts, writes the answer)
```

1. **Channels** — CLI, Telegram bot, Discord bot. Each receives a question, sends it to the MCP client and replies with the answer. Long answers are split into several messages to fit the Telegram and Discord message limits.
2. **MCP client** — Connects to the MCP server at `MCP_SERVER_URL` and calls its `retrieval_augmented_generation` tool, which returns the answer. Links to the videos used in the answer are not available yet: they will come from a new MCP tool ([MCP_server#3](https://github.com/garyseconomics/MCP_server/issues/3)).
3. **MCP server** — Lives in its own [repo](https://github.com/garyseconomics/MCP_server). It holds the RAG pipeline: it searches the vector database for the transcripts related to the question and uses an LLM to write the answer.
4. **LLM manager** — Not used by the bots yet. It's kept for a future step, in which the chatbot will use an LLM to decide which MCP tools to call for each question. It wraps several chat providers (Ollama and OpenAI-compatible, e.g. OpenRouter) and uses the first available one by priority. By default, chat falls back from Ollama Cloud to local Ollama (`qwen3:4b`). Each provider's type, URL, chat model and API key variable are configured in `providers.json`, and the provider order and API keys in `.env`; other providers, such as a private server, can be added without changing the code.
5. **Tracing** — Each question sent to the MCP server creates a trace in [Langfuse](https://langfuse.com/), labelled with the client type (`cli`, `telegram` or `discord`).

## Tech stack

- **Python 3.11+**
- **pytest** for testing
- **ruff** for linting and formatting
- **MCP Python SDK** (`mcp`) to connect to the MCP server
- **LangChain** for LLM integration
- **Ollama** (`langchain-ollama`) and OpenAI-compatible providers (`langchain-openai`) for the LLM
- **pydantic-settings** for typed configuration with automatic `.env` loading
- **Langfuse** for LLM observability and tracing
- **chonkie** to split long answers into several messages
- **python-dotenv** for environment variable loading
- **python-telegram-bot** and **discord.py** for bot integrations
- **Docker** + **GitHub Actions** for CI/CD

## Prerequisites

### MCP server

The chatbot needs a running [Gary's Economics MCP server](https://github.com/garyseconomics/MCP_server) to answer questions. You can use a remote one, or run your own by following the instructions in that repo. Set its address in `MCP_SERVER_URL` (see below).

### Install Ollama and download the models

> **Note:** the bots don't use these models yet. They're used by the LLM manager (see [Architecture overview](#architecture-overview)) and its tests.

All models run through [Ollama](https://ollama.com/).

Install Ollama:
```bash
sudo apt install curl
curl -fsSL https://ollama.com/install.sh | sh
```

**Chat model** — The chatbot tries providers in the priority order set in `.env` (by default Ollama Cloud, then a local fallback). To use the local fallback:

```bash
ollama pull qwen3:4b
```

### Configure the environment variables

**IMPORTANT**: The `.env` file contains secret keys and is not in the repository. Create your own by copying `.env.sample`:

```bash
cp .env.sample .env
```

Then fill in the values. The available variables are:

**LLM providers**
- `CHAT_PROVIDER_PRIORITY` — providers tried for chat, in order, as a JSON list of names from `providers.json`. Defaults to `["ollama_cloud", "ollama_local"]`.
- `TEST_CHAT_PROVIDER` — the only provider used by the tests that call an LLM. Defaults to `ollama_cloud`. If it fails, the tests fail: fix it or choose another provider, then run the tests again.
- API keys — one variable per provider that needs a key, named in the provider's `api_key_env` in `providers.json`. For example, `OLLAMA_CLOUD_API_KEY` for `ollama_cloud`.

**Bot tokens**
- `TELEGRAM_TOKEN` — Token for the Telegram bot. You get this when you [create a bot with BotFather](#create-a-telegram-bot).
- `DISCORD_TOKEN` — Token for the Discord bot. You need a bot installed on a server with permission to read and send messages.

**Observability**
- `LANGFUSE_TRACING_ENABLED` — set to `true` to send traces to the [Langfuse](https://langfuse.com/) observability platform. Recommended: the traces record latency, token usage and which providers and models are used. Off unless set to `true`, because it needs the keys below.
- `LANGFUSE_MESSAGE_TRACING_ENABLED` — set to `true` to also send the questions and answers to Langfuse. Off unless set to `true`.
- `LANGFUSE_PUBLIC_KEY` — Public key for Langfuse.
- `LANGFUSE_SECRET_KEY` — Secret key for Langfuse.
- `LANGFUSE_BASE_URL` — Langfuse server URL. Defaults to `https://cloud.langfuse.com`.
- `LANGFUSE_TRACING_ENVIRONMENT` — labels the traces so you can filter them in Langfuse, for example `production` or `testing`. Defaults to `development` in `.env.sample`.
- `LANGFUSE_TEST_TRACING_ENVIRONMENT` — replaces `LANGFUSE_TRACING_ENVIRONMENT` while running the tests, so their traces are not mixed with real use of the bots. Defaults to `automated_tests`.
- `OTEL_SERVICE_NAME` — names this app in the traces. Defaults to `garys-economics-chatbot` in `.env.sample`.

**MCP server**
- `MCP_SERVER_URL` — Address of the [Gary's Economics MCP server](https://github.com/garyseconomics/MCP_server) the chatbot uses to answer questions, e.g. `http://127.0.0.1:8080/mcp` for a server running on your machine.

  > **Note:** this example works when you run the chatbot without Docker, or when you point `MCP_SERVER_URL` to a remote server. To run the chatbot with Docker, see [Setup with Docker](#setup-with-docker).

### Configure the LLM providers

The providers are configured in `providers.json`, which is not in the repository. Create your own by copying `providers.sample.json` (if there is no `providers.json`, the chatbot uses the sample):

```bash
cp providers.sample.json providers.json
```

It holds the settings for each provider, by name (the order to try them in is set in `.env`):

- `type` — `ollama` (default) or `openai` for OpenAI-compatible APIs such as [OpenRouter](https://openrouter.ai) (see its [authentication](https://openrouter.ai/docs/api/reference/authentication) and [models](https://openrouter.ai/models?fmt=cards&input_modalities=text)).
- `url` — URL of the provider.
- `chat_model` — chat model to use.
- `api_key_env` — name of the variable in `.env` that holds the provider's API key, or `null` if it doesn't need one (e.g. a local Ollama). The provider is skipped when the key is missing.

### Configuration

All configuration is managed through [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) classes. Environment variables from `.env` are loaded automatically — each field maps to an env var of the same name. Fields not set in `.env` use the defaults defined in the class.

The settings live in `src/config.py` (provider priority, MCP server, bot tokens and message limits, Langfuse). The LLM providers themselves are in `providers.json` (see [Configure the LLM providers](#configure-the-llm-providers)).

## Setup with Docker

> **Before starting the containers, update `MCP_SERVER_URL` in your `.env`.** Inside a Docker container, `127.0.0.1` (or `localhost`) points to the container itself, not to your machine, so the chatbot can't reach an MCP server at that address. Use one of these instead:
> - **A remote MCP server:** its public URL or network address.
> - **An MCP server running on the same machine:** your machine's network address (e.g. `http://192.168.1.10:8080/mcp`). The MCP server must accept connections from outside itself — set `MCP_HOST=0.0.0.0` in the MCP server's `.env`.

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

`pip install .` copies the code into `.venv`, so later changes to `src/` (including ones you pull from GitHub) are not used until you run it again. If you are developing, install in editable mode instead, which links `.venv` to `src/` so changes apply straight away:
```bash
pip install -e ".[dev]"
```

## Usage

Activate the virtual environment first (not needed with Docker):
```bash
source .venv/bin/activate
```

### CLI chatbot

```bash
python -m interfaces.chatbot
```

The chatbot will greet you and ask for a question. It sends the question to the MCP server and shows the answer. Answers are better when Gary's videos cover the topic asked about.

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
pytest
```

Some tests call live services: the MCP server, Langfuse and the LLM providers. Most of them are skipped when the service is not configured, and fail when it is configured but not reachable.

## Testing plan

We are rolling out the chatbot in phases. See the [plan/](plan/) folder for details.
