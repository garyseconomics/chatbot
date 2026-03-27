# Phase 2 Plan — Preparing for ~3,000 Patreon Users

This plan covers what must be done before Phase 2, what can wait, and the order to
tackle things in. Based on Phase 1 results (34 testers, 356 questions), the latency
reports, and open issues.

| Phase | Users | Focus |
|-------|-------|-------|
| Phase 0 (done) | ~5 volunteers | Build the prototype, fix core bugs |
| Phase 1 (done) | ~100 volunteers | Answer quality, resource estimation |
| **Phase 2** | **~3,000 Patreons** | **Stability, content, and cost validation** |
| Phase 3 | 1M+ YouTube subscribers | Full public release |

## Implementation order

1. [Bug fixes](#1-bug-fixes) — Fix user-facing issues before more users arrive
2. [Infrastructure](#2-infrastructure) — Move to owned accounts and servers
3. [New functionality](#3-new-functionality) — Temporal awareness, multi-turn conversations, source access
4. [More content](#4-more-content) — Expand the knowledge base
5. [Nice to have](#5-nice-to-have) — Operational improvements

---

## 1. Bug fixes

These are user-facing issues from Phase 1 that will be worse at 3,000 users. Fix first.

### 1.1 Fix message length crash ([#33](https://github.com/garyseconomics/chatbot/issues/33))

The bots crash when the LLM returns a long answer. Discord has a 2,000-character limit
and Telegram has a 4,096-character limit. The initial quick fix (`max_tokens`/`num_predict`)
was removed because thinking models consumed the token limit with reasoning tokens.

**Fix:** Check final message length before sending and split or truncate if it exceeds
the platform limit.

### 1.2 Improve error handling in Discord and Telegram bots

- Replace the hardcoded Discord error message with `settings.error_messages`.
- Add try/except to Telegram's `question()` handler (currently has no error handling
  outside of `RAG_query`).
- `RAG_query` already catches all exceptions internally — bot-level error handling only
  needs to catch failures outside `RAG_query` (e.g., `message.channel.send` or
  `context.bot.send_message`).

### 1.3 Separate greeting messages for Telegram and Discord

Both bots use the same `settings.bot_greeting` ("I'm back online! Feel free to keep
asking questions.") which makes sense for Discord (bot reconnecting) but confuses new
Telegram users who haven't asked anything yet. Add a separate greeting for Telegram.

---

## 2. Infrastructure

Move everything to commercial servers and accounts owned by Gary's Economics.

### 2.1 Add support for OpenAI-compatible providers ([#41](https://github.com/garyseconomics/chatbot/issues/41))

**This is the prerequisite for cloud embeddings.** Currently `LLM_Client` only creates
`ChatOllama` clients. We need it to also create clients for OpenAI-compatible providers
(OpenRouter, SiliconFlow, etc.).

The provider priority system and fallback logic already work generically — only the
client creation step in `_create_chat_client()` is Ollama-specific. Scope:
- Add provider type to config (e.g., `"type": "ollama"` vs `"type": "openai"`).
- Update `_create_chat_client()` to select the right LangChain class.
- Add at least one OpenAI-compatible provider config.
- Update tests.

### 2.2 Add a cloud embedding provider

Once #41 is done, add a cloud embedding provider. This eliminates the dependency on
MakeSpace for embeddings and gives us redundancy and scalability. With a cloud embedding
provider, we no longer need a local Ollama instance on the server.

**Current embedding model:** `qwen3-embedding:8b`, scoring 70.58 on the MTEB benchmark —
the best available on Ollama as of March 2026. The only models scoring higher (NVIDIA's
NV-Embed-v2 at 72.31 and Llama-Embed-Nemotron-8B) are not on Ollama yet.

**Current provider situation:** Our two Ollama instances don't scale for Phase 2:
- **MakeSpace Ollama** is fast (0.18s warm) but it's shared infrastructure — under load
  embeddings slowed to 7s+ when sharing the GPU with the chat model.
- **Local Ollama** is slow (3–5s per query) and even slower on long questions (up to 14s).
  Cold starts take 40–60 seconds.

Ollama Cloud does not support embedding models (as of March 2026).

**Cloud providers** — Several offer `qwen3-embedding:8b` via OpenAI-compatible APIs at
negligible cost:

| Provider | Price | API |
|----------|-------|-----|
| [OpenRouter](https://openrouter.ai/qwen/qwen3-embedding-8b) | $0.01 / M tokens | OpenAI-compatible |
| [SiliconFlow](https://www.siliconflow.com/models/qwen-qwen3-embedding-8b) | Pay-as-you-go ($1 free) | OpenAI-compatible |
| [DeepInfra](https://deepinfra.com/Qwen/Qwen3-Embedding-8B/api) | Pay-as-you-go (free credits) | OpenAI-compatible |
| [Alibaba DashScope](https://qwen.ai/apiplatform) | Pay-as-you-go (free quota) | OpenAI-compatible |

At $0.01 per million tokens, the cost is negligible for our use case. All use the
OpenAI-compatible API, which is why #41 must be done first.

Re-check model availability in mid-2026 — watch for NVIDIA models landing on Ollama and
Ollama Cloud adding embedding support. Tracked in
[issue #40](https://github.com/garyseconomics/chatbot/issues/40).

### 2.3 Create Gary's Economics Ollama Cloud account

Create an account at [ollama.com](https://ollama.com/) under Gary's Economics and get
a Pro subscription ($20/month). The free tier had a ~10% failure rate on the busiest
Phase 1 day (10 out of 97 queries rejected). Pro gives 50x more usage and 3 concurrent
models.

After upgrading, re-run `python -m analytics.test_cloud_limits` to check whether the
concurrency limits (currently 2 active + 5 queued on the free tier) also increase on Pro.

See [latency_report_chat_model.md](latency_report_chat_model.md) for Phase 1 data and
the full analysis of Ollama Cloud limits.

### 2.4 Migrate to Gary's server

Move the application (Python scripts, Docker setup, vector database) to a server owned
by Gary's Economics.

**Current setup (MakeSpace Madrid):** The AI server has 2 GPUs (3060 + 3090, 36 GB VRAM
total), a 40-thread Threadripper CPU, and 96 GB RAM. The LLM and embedding models run
on the GPUs with some CPU/RAM usage. The bots run in a virtual machine on the same
server, using a small amount of resources for the Python processes.

**What Phase 2 needs:** With cloud providers handling both chat (Ollama Cloud) and
embeddings (OpenAI-compatible provider from 2.2), the server only needs to run Docker
containers — no GPU required. The MakeSpace sysadmin confirms that when using online AI
providers, the bots run with a free-tier amount of CPU/RAM resources.

The code changes from 2.1 and 2.2 should be done first so we deploy the new provider
support at the same time as the migration.

---

## 3. New functionality

### 3.1 Temporal awareness ([#26](https://github.com/garyseconomics/chatbot/issues/26))

The bot treats all video content as equally recent because chunks have no date information.
Phase 1 testers flagged this — e.g., referencing a general election when asked about a
recent by-election.

Step 1 is done (SRT files renamed with dates in the filename). Two approaches to explore
for the remaining work:

**Option A — Date metadata in the vector database:**
- Update `srt_splitter.py` to extract the publish date from the filename and store it in
  chunk metadata.
- Regenerate the vector database so all chunks carry their video's publish date.
- The LLM receives date information with each retrieved chunk automatically.

**Option B — Add date info in the prompt template:**
- Keep the vector database as-is.
- When building the context for the prompt, look up the video date from the filename or a
  mapping and inject it alongside each subtitle fragment.
- More flexible (no database regeneration needed) but adds complexity to the prompt
  building step.

Both options also include [#36](https://github.com/garyseconomics/chatbot/issues/36)
(inline video links) — each subtitle fragment in the prompt should carry its video link
and publish date so the LLM can reference the correct source naturally. The LLM already
receives the current date via `{current_datetime}`, so it can reason about recency.

**Tasks:** Evaluate both options, write tests for the chosen approach, implement, and
regenerate the vector database if needed.

### 3.2 Multi-turn conversations ([#6](https://github.com/garyseconomics/chatbot/issues/6))

Most requested feature from Phase 1 testers. Currently the bot treats each message
independently — it doesn't remember what you said earlier. Implementation needs:

- **Chat memory** — Store conversation history so the LLM receives the full conversation
  on each call. Investigate [OpenBrain (OB1)](https://github.com/NateBJones-Projects/OB1/blob/main/docs/01-getting-started.md)
  as the framework for this.
- **Sessions** — Manage conversation sessions to control interaction flow.
- **Usage limits** — Prevent intensive use by individual users during Phase 2.
- **Patreon authentication** — Possibly restrict access to Patreon subscribers during
  Phase 2 to prevent unauthorized use. Needs discussion with Gary's team.

**Cost consideration:** Multi-turn conversations mean longer prompts (full conversation
history on each call) = more tokens per query. Measure the extra cost before enabling
for 3,000 users. Discuss with Gary's team whether to enable it for Phase 2.

### 3.3 Source document access

Users have been asking the bot to provide source documents. When we add the memory
system (OpenBrain) for multi-turn conversations, we can also use its database to store
the original documents we import — links to the source material and the documents
themselves, so the bot can provide exact quotes and references.

This ties into the content expansion (section 4): when importing reference material
(economist papers, book chapters), we should store the source links and original text
alongside the vector embeddings.

---

## 4. More content

### 4.1 Add subtitles after November 2025

The vector database only covers videos from early 2024 to November 2025. Subtitles for
newer videos need to be added using the existing import pipeline.

Establish a process for adding new video subtitles when they come out — someone on
Gary's team (or a volunteer) downloads subtitles from YouTube and runs the import script.

### 4.2 Import older video transcripts ([#39](https://github.com/garyseconomics/chatbot/issues/39))

The [transcripts repo](https://github.com/garyseconomics/transcripts/tree/main/transcripts)
has 261 full videos + 49 shorts that are missing from the database (full list in
`docs/missing_subtitles.txt`). These are in VTT format and need review before import:
1. Review transcripts for correctness (compare with what's actually said in videos).
2. Convert from VTT to SRT format.
3. Add clean subtitles to the [subtitle-data](https://github.com/garyseconomics/subtitle-data) repo.

This is the most time-consuming content task — reviewing 310 transcripts requires
significant effort from someone who can compare them against the videos.

### 4.3 Add economist documents — discuss scope, possibly Phase 3

Add documents from economists to give the bot a ground knowledge base beyond Gary's
videos. Example sources:
- [Gabriel Zucman](https://gabriel-zucman.eu/) — research on wealth inequality, tax havens
- [Thomas Piketty](http://piketty.pse.ens.fr/en/) — research on capital and inequality

The same library we use for SRT imports (LangChain document loaders) supports PDFs, HTML,
and other formats, so this doesn't require a new import pipeline. However, it is a new
type of content with different considerations:
- What specific documents to include (papers, book chapters, articles).
- How to chunk academic/economic texts effectively.
- Metadata: author, publication date, source URL.
- Source storage: keep original documents accessible so the bot can provide quotes and
  links (see 3.2).
- All material must be publicly available for divulgation.

**Scope and timing need discussion.** This could be Phase 2 or Phase 3 depending on
how much it adds to the bot's quality versus the effort required.

---

## 5. Nice to have

Operational improvements that are valuable but not blocking Phase 2 launch.

### 5.1 Service watcher ([#21](https://github.com/garyseconomics/chatbot/issues/21))

Monitor bot availability from a different host. Options: HTTP `/health` endpoint polled
by Uptime Kuma, or a second bot that pings the main bot through the chat.

### 5.2 Auto-update containers ([#42](https://github.com/garyseconomics/chatbot/issues/42))

Automatically update running containers when a new Docker image is pushed to GHCR (GitHub Container Registry).
Options: Watchtower (simplest for single-server), webhook-based deploy, or a cron job.

### 5.3 Run tests in Docker CI ([#34](https://github.com/garyseconomics/chatbot/issues/34))

Run `pytest` inside the built Docker image before pushing to GHCR. During Phase 1, a
Langfuse v3-to-v4 breaking change was only caught in production because tests only ran
locally.

### 5.4 Prompt v3 remaining issues ([#37](https://github.com/garyseconomics/chatbot/issues/37))

From Phase 1 testing, 7 out of 118 answers (6%) were flagged. Main remaining issues:
- RAG internals still leak ("the reference material provided" in answers).
- Identity correction inconsistent ("Hi Gary!" not always caught).
- Financial advice boundary inconsistent on edge cases.

These can be addressed iteratively through prompt refinement and testing different
prompt + model combinations. Related to #41 (OpenAI-compatible providers gives access
to more models to test against).

### 5.5 Retrieve and review prompt v3 traces

Export user traces from Langfuse for the period between the v3 prompt deployment
(2026-03-21 04:13) and the v3 fix deployment (2026-03-23 19:18). Review the answers
to identify cases where the bot refused to answer or gave bad answers to legitimate
economics questions. See TODO.md for full details.

---

## Estimated monthly costs

| Service | Cost | Notes |
|---------|------|-------|
| Ollama Cloud Pro | $20/month | Chat LLM (`qwen3-next:80b`). 50x more usage than free tier |
| Cloud embeddings | ~$0.01/M tokens | Negligible at current volume. During Phase 1 we processed ~400 queries — even at 10x that volume the embedding cost would be under $0.01/month |
| Server hosting | ~$0–5/month | No GPU required — only runs Docker containers. A free-tier or minimal VPS is sufficient |

---

## Open questions for Gary's team

1. **Patreon authentication** — Should we restrict Phase 2 access to Patreon subscribers
   only? This would prevent unauthorized use but adds implementation complexity.
2. **Multi-turn conversations** — Enable for Phase 2 or wait for Phase 3? Depends on
   cost assessment.
3. **Economist documents** — Which sources to include? Phase 2 or Phase 3?
4. **Subtitle maintenance** — Who will add subtitles for new videos on an ongoing basis?

---

## References

- [Phase 1 Report](Phase_1_Report.md) — Full results from Phase 1 testing
- [Chat Model Latency Report](latency_report_chat_model.md) — Ollama Cloud vs self-hosted
  performance, API limits analysis
- [Embedding Latency Report](latency_report_embeddings.md) — MakeSpace vs Local Ollama
  benchmarks, cloud provider options
- [Prompt Issues](prompt_issues.md) — Detailed Phase 1 prompt issues and fixes
- [TODO.md](../TODO.md) — Full task list with implementation details
