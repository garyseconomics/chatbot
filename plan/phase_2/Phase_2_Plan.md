# Phase 2 Plan — Preparing for ~3,000 Patreon Users

This plan covers what must be done before Phase 2, what can wait, and the order to
tackle things in. Based on Phase 1 results (34 testers, 356 questions), the latency
reports, and open issues.

| Phase | Users | Focus |
|-------|-------|-------|
| Phase 0 (done) | ~5 volunteers | Build the prototype, fix core bugs |
| Phase 1 (done) | ~34 volunteers (*) | Answer quality, resource estimation |
| **Phase 2** | **~3,000 Patreons** | **Stability, content, and cost validation** |
| Phase 3 | 1M+ YouTube subscribers | Full public release |

(*) Note: ~34 volunteers were active testers out of the ~100 that initially signed up to participate.

## Implementation order

1. [Bug fixes](#1-bug-fixes) — Fix user-facing issues before more users arrive
2. [Infrastructure](#2-infrastructure) — Move to owned accounts and servers
3. [Answer quality](#3-answer-quality) — Fix remaining prompt issues
4. [More content](#4-more-content) — Expand the knowledge base
5. [New functionality](#5-new-functionality) — Date awareness, conversations
6. [Nice to have](#6-nice-to-have) — Operational improvements

---

## 1. Bug fixes

Issues from Phase 1 that will be worse at 3,000 users. Fix first.

### 1.1 Bot crashes on long answers ([#33](https://github.com/garyseconomics/chatbot/issues/33))

Discord and Telegram both have limits on how long a single message can be. When the AI
produces an answer that exceeds those limits, the bot crashes instead of handling it
gracefully.

**Fix:** Before sending, check the message length and split long answers into multiple
messages if needed.

### 1.2 Better error messages on Discord and Telegram

When something goes wrong (e.g., a network error while sending a reply), the bots don't
always show a helpful error message to the user. Discord shows a hardcoded string, and
Telegram shows nothing at all.

**Fix:** Make both bots show the same friendly error messages we've already defined for
other error cases.

### 1.3 Separate welcome messages for Telegram and Discord

Both bots currently send the same greeting: "I'm back online! Feel free to keep asking
questions." This makes sense on Discord (where the bot reconnects after a restart and
users have been chatting before), but confuses new Telegram users who are opening the
bot for the first time and haven't asked anything yet.

**Fix:** Give each platform its own welcome message.

---

## 2. Infrastructure

Move everything to accounts and servers owned by Gary's Economics.

The technical details and research results referenced here are in  [Phase 2 tech decisions](Phase_2_tech_decisions.md)

### 2.1 Support multiple AI providers ([#41](https://github.com/garyseconomics/chatbot/issues/41))

Currently the bot can only use one AI service (Ollama). We need to add support for other
providers (like OpenRouter, SiliconFlow, etc.) so we have more flexibility, redundancy,
and access to a wider range of AI models.

**Why this matters:** This is the prerequisite for the next step (cloud-based search), that will allow us to be independent from MakeSpace servers.
It also lets us test different AI models to find the best one for our bot.

### 2.2 Move search to a cloud provider

The bot uses a search step to find relevant video content before answering each question.
This currently runs on the MakeSpace server, which doesn't scale:

- **MakeSpace server** is fast normally, but slows down dramatically under load because
  it shares resources with other tasks.
- **Backup server** is too slow (3–14 seconds per query, with cold starts of up to 60
  seconds).

Cloud providers offer the same search capability at negligible cost (under $0.01/month
at 10x our Phase 1 volume). Once we add multi-provider support (2.1), switching to a
cloud provider is straightforward and removes our dependency on the MakeSpace server
entirely.

Several providers are available — see the [Phase 2 tech decisions](Phase_2_tech_decisions.md) for the full comparison.

### 2.3 Create Gary's Economics Ollama Cloud account

Ollama Cloud is the service that runs the AI model which generates the bot's answers.
We need to create an account under Gary's Economics and get a Pro subscription
($20/month).

**Why Pro:** The free tier rejected ~10% of queries on the busiest Phase 1 day (10 out of
97 questions failed). Pro gives 50x more capacity.

After upgrading, we'll test whether the paid tier also increases how many questions the
bot can handle simultaneously.

See [latency_report_chat_model.md](../phase_1/latency_report_chat_model.md) for Phase 1 data.

### 2.4 Migrate to Gary's own server

Move the bot from the MakeSpace Madrid server to a server owned by Gary's Economics.

**Current setup:** The bot runs on MakeSpace's AI server — a powerful machine with GPUs,
a fast processor, and 96 GB of memory. But with cloud providers handling the AI work
(2.2 and 2.3), we no longer need that power. The server only needs to run the bot
software and store the video content database.

**What Phase 2 needs:** A reliable server that stays online 24/7. With 3,000 potential
users, downtime and crashes are not acceptable. The content database will grow as we add
more videos (currently ~45, target ~350). A free server is too risky — they can run out
of memory or be shut down without notice. A small paid server ($3–5/month) gives us
reliability and room to grow.

**Recommended option:** [Hetzner](https://www.hetzner.com/cloud/) CX22 at ~$3.60/month —
best value, with EU and US data centres.

Free options exist ([Oracle Cloud](https://www.oracle.com/cloud/free/), [Google Cloud](https://cloud.google.com/free), AWS free tier) but are only suitable for development and testing — not for a service 3,000 people depend on.

Other options documented in [Phase 2 tech decisions](Phase_2_tech_decisions.md).

The code changes from 2.1 and 2.2 should be done first so we deploy multi-provider
support at the same time as the migration.

---

## 3. Answer quality ([#37](https://github.com/garyseconomics/chatbot/issues/37))

Prompt v4 (deployed 2026-03-28) fixed most Phase 1 issues, but introduced some new ones
and several remain open. Tested with 97 questions on 2026-03-29.

**Open issues:**
*Questions about the bot itself:*
- **Refuses to talk about itself** (new in v4) — when asked about its code or how it
  works, deflects with "I'm here to talk about economics" instead of giving the GitHub
  link as instructed.
- **Wrong answers about data collection** (new in v4) — claims it doesn't collect data,
  which is false. Needs a proper data/privacy document (see 4.3).
- **Reveals its internals** — still occasionally says things like "the reference material
  provided" instead of speaking naturally. Improved but not eliminated.

*Content gaps and inconsistencies:*
- **Too diplomatic on some topics** — Gary is strongly critical of crypto, but the bot gives
  balanced answers because the crypto video (2022) isn't imported yet. Will improve as
  older videos are added (see 4.2).
- **Inconsistent on borderline topics** — some sensitive questions get answered or refused
  depending on what the search happens to return, not a consistent policy. Needs guidance
  from the team (see open questions 5 and 6).
- **Refuses to share video content** — when asked for quotes or details from Gary's
  videos, sometimes refuses even though that's exactly what it's built for.
- **Makes up details** (new in v4) — When asked for a specific date for a Gary anecdote, the bot made up the date. This has only happened once, but is important to prevent this happening again.

*Gary's identity and credibility:*
- **Over-corrects on identity** (new in v4) — says "I'm not Gary" even on plain greetings
  like "hi" or "hello gary bot" where the user isn't confused.
- **Credibility questions** — needs team guidance on how to handle challenges to Gary's
  track record (see [prompt_issues.md](prompt/prompt_issues.md) for examples).

**Already fixed in v4:**
- Bot used to impersonate Gary (now corrects — overcorrects, see above)
- Bot used to give financial advice (now consistently refuses and redirects)
- Bot used to fabricate Gary's opinions (now honestly says it doesn't know)
- Bot used to answer off-topic questions (now correctly refuses)
- Language was too academic (now plain and friendly throughout)
- Bot used to speculate about Gary's personal life (now refuses)
- Trolls could manipulate the bot with leading questions (now reframes them)
- Users could override the bot's instructions (now ignores override attempts)

**Repeatable answer testing:** We have a set of 130 test questions across 20 categories and a script that
asks them all to the bot and saves the answers. After each run, we review the answers
with the help of an AI assistant (Claude Code) — this is how we produced the v3, v3.1, and v4 test reports. The next steps
are to fix some issues with the testing script, then use AI to evaluate the answers
automatically. Once that works, we can test
different prompt versions combined with different AI models to find the best
combination.

Full plan in [evaluation_pipeline_plan.md](evaluation_pipeline_plan.md).
Full issue details in [prompt_issues.md](prompt/prompt_issues.md).

---

## 4. More content

See [data_sources.md](data_sources.md) for the full inventory of current and planned
content sources, the transcript review pipeline, and import status.

### 4.1 More subtitles/transcriptions

The current database only includes video subtitles from early 2024 to November 2025.
Several important sources are missing.

**Add videos after November 2025** — Newer videos need to be added. Someone on the team
(or a volunteer) gets the new subtitles and runs the import. This should become a regular
task whenever new videos come out.

**Import older video transcripts** ([#39](https://github.com/garyseconomics/chatbot/issues/39))
— The channel has ~350 videos in total. Only ~45 are currently in the bot's knowledge
base. The remaining ~300 have transcripts available but need to be reviewed before import. Reviewing ~300 transcripts requires significant effort from someone who can watch the videos and compare. We are already preparing AI-cleaned transcripts and uploading them for [volunteer review](https://github.com/Adavideo/transcripts/tree/AI_and_volunteer_review/revisions/2_To_be_reviewed_by_volunteers)
(see [review instructions](https://github.com/Adavideo/transcripts/blob/AI_and_volunteer_review/revisions/2_To_be_reviewed_by_volunteers/INSTRUCTIONS.md)).

### 4.2 Documents written by us

Documents we write to summarize and explain things, so the bot can answer questions about
itself and the channel from RAG context instead of needing all of it in the prompt.
Currently, all this information has to be crammed into the bot's instructions, which
limits how much detail it can give. With background documents, the bot can give thorough
answers when someone asks "How does this bot work?" or "Who is Gary Stevenson?"

**Topics to cover:**
- **The channel** — what it covers, its mission, its perspective on economics. A full
  list of topics covered by the channel has been compiled
  ([channel_topics.md](../../content_database/docs/channel_topics.md)).
- **Gary Stevenson** — who he is, background (former trader, Patriotic Millionaires,
  independently wealthy, not monetising the platform). A draft bio already exists
  ([gary_bio.md](../../content_database/docs/gary_bio.md)), written from two channel
  videos. Needs approval from Gary's team before it can be used.
- **How the bot works** — what AI it uses, that it's built on video transcripts, that
  it's open source on GitHub.
- **Data collection and privacy** — **this is critical to get right.** The bot currently
  claims it doesn't collect data, which is false. The document must explain:
  1. All questions and answers are stored and used to improve the bot.
  2. Users should not share personal information.
  3. Questions are sent to external AI services to generate answers.
  4. Some of those services may use the data to train their models — we don't control that.
  5. The project is open source so anyone can verify all of this.
  **This must be updated whenever we add or change AI providers.**

### 4.3 More documents

Documents from other sources that could enrich the bot's knowledge.

- Gary's book and master thesis.
- Documents from other economists: [Gabriel Zucman](https://gabriel-zucman.eu/), [Thomas Piketty](http://piketty.pse.ens.fr/en/), [Ha-Joon Chang](https://www.youtube.com/watch?v=MGt7swnEb3g).

The import tools already support PDFs and other formats, so adapting to include this doesn't require adding new tools. But it raises questions:
- Which specific documents to include?
- How to handle academic texts (they're structured differently from video subtitles).

**Scope and timing need discussion.** This could be Phase 2 or Phase 3 depending on
how much it adds to the bot's quality versus the effort required.

---

## 5. New functionality

### 5.1 Date awareness ([#26](https://github.com/garyseconomics/chatbot/issues/26))

The bot currently treats all video content as equally recent — it doesn't know when a
video was published. Phase 1 testers noticed this: for example, the bot referenced a
general election when asked about a recent by-election, because it didn't know the
general election video was older.

**Fix:** Attach the publish date to each piece of video content so the bot knows what's
recent and what's old. The bot already knows today's date, so once it has video dates it
can reason about what's current.

This also includes adding video links to answers
([#36](https://github.com/garyseconomics/chatbot/issues/36)) — when the bot references
a video, it will be able to link to it directly.

### 5.2 Multi-turn conversations ([#6](https://github.com/garyseconomics/chatbot/issues/6))

The most requested feature from Phase 1 testers. Currently the bot treats each message
as a brand-new conversation — it doesn't remember what you said two messages ago. This
means you can't ask follow-up questions or have a back-and-forth discussion.

**What's needed:**
- **Conversation memory** — The bot remembers what was said earlier in the conversation.
- **Session management** — Track who is talking and keep conversations separate.
- **Usage limits** — Prevent any single user from overloading the system during Phase 2.
- **Patreon authentication** — Possibly restrict access to Patreon subscribers to prevent
  unauthorized use. Needs discussion with the team.

**Cost consideration:** Conversations mean the bot sends more text to the AI on each
message (the full conversation history), which costs more per question. We need to
measure this before enabling it for 3,000 users.

### 5.3 Source document access

Users have been asking the bot to provide its sources. We can store the original source material (video links, documents, quotes)
so the bot can point users to exactly where its answer came from.

This ties into the content expansion (section 4): when we add new reference material,
we should store the original sources alongside it.

---

## 6. Nice to have

Improvements that are valuable but not blocking Phase 2 launch.

### 6.1 Uptime monitoring ([#21](https://github.com/garyseconomics/chatbot/issues/21))

Set up automatic monitoring so we get alerted if the bot goes down, instead of waiting
for users to report it.

### 6.2 Automatic updates ([#42](https://github.com/garyseconomics/chatbot/issues/42))

When we release a new version of the bot, the server should update automatically instead
of requiring someone to log in and update it manually.

### 6.3 Automated testing before release ([#34](https://github.com/garyseconomics/chatbot/issues/34))

Run the full test suite automatically before each release. During Phase 1, a bug from a
software update was only caught after it reached users because testing only happened
manually.

---

## Estimated monthly costs

| Service | Cost | Notes |
|---------|------|-------|
| Server hosting | ~$3.50–5/month | Only runs the bot software, no special hardware needed. Hetzner at ~$3.60/mo is the best value option |
| AI answer generation | $20/month | Ollama Cloud Pro — 50x more capacity than the free tier |
| AI search | TBD | Cloud embedding provider cost — needs investigation once we choose a provider (see 2.2) |

**Total: ~$24–25/month + AI search cost (TBD)**

---

## Open questions for Gary's team

1. **Patreon authentication** — Should we restrict Phase 2 access to Patreon subscribers
   only? This would prevent unauthorized use but adds implementation complexity.
2. **Multi-turn conversations** — Enable for Phase 2 or wait for Phase 3? Depends on
   the cost assessment.
3. **Economist documents** — Which sources to include? Phase 2 or Phase 3?
4. **Subtitle maintenance** — Who will add subtitles for new videos on an ongoing basis?
5. **Speculative/hypothetical questions** — When a user asks a hypothetical question that
   relates to topics Gary has covered (e.g., "How would bond markets react to a chancellor
   announcing aggressive wealth taxation?"), should the bot speculate based on the
   information it has, or deflect? The current instructions allow the bot to answer from
   general knowledge on economics topics, and these answers can sound authoritative even
   though they're speculative. Need guidance on where the line is.
6. **Sensitive topics with an economics angle** — Some questions are politically/socially
   sensitive but have a legitimate economics side (drug legalisation, defunding police,
   party manifestos, military intervention). Should the bot engage with the economics
   angle, or deflect entirely when Gary hasn't covered the topic? Currently the bot is
   inconsistent — sometimes deflecting, sometimes giving detailed answers. Until we have
   guidance, the bot should deflect on sensitive topics when there's no channel context.
7. **Financial advice on personal investments** — When users ask about their own holdings
   (e.g., gold ETFs), the bot gave investment guidance ("stick to your plan", "hold
   steady"). The bot should not tell users what to do with their assets. Should it redirect
   to systemic issues (why asset prices move the way they do), or refuse entirely?

---

## References

- [Phase 1 Report](../phase_1/Phase_1_Report.md) — Full results from Phase 1 testing
- [Chat Model Latency Report](../phase_1/latency_report_chat_model.md) — Performance and capacity analysis
- [Embedding Latency Report](../phase_1/latency_report_embeddings.md) — Search performance and cloud provider options
- [Data Sources](data_sources.md) — Current and planned content sources, transcript review pipeline, import status
- [Prompt Issues](prompt/prompt_issues.md) — Answer quality issues and fixes (Phase 1 through v4)
- [Prompt v4 Test Summary](prompt/prompt_v4.md) — Full v4 test results (97 questions, 2026-03-29)
- [TODO.md](../../TODO.md) — Full task list with implementation details
