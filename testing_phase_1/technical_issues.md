# Technical Issues — Testing Phase 1

Technical bugs found and fixed during Phase 1 testing (March 2026). Each section covers one root cause: what happened, how it was discovered, and how it was fixed.

During Phase 1, multiple bugs were active simultaneously. Some user-facing errors had more than one possible cause, so attribution is approximate where noted.

## 1. Discord heartbeat blocking (#28)

**Impact:** The bot reset repeatedly during Phase 1 day 1 and day 2, causing the majority of user-facing errors.

**Symptoms:** Users saw "Sorry, something went wrong. Please try again later." or the bot stopped responding entirely, followed by a restart greeting ("Hello. This is Garys Economics Youtube chatbot"). Server logs showed 46 reconnects.

**Root cause:** `RAG_query()` was called synchronously inside the Discord async event loop. Each query involved embedding + LLM call (30–50+ seconds). While `RAG_query` blocked, the Discord gateway heartbeat couldn't be sent — Discord requires one every ~41 seconds. Discord closed the WebSocket and the bot reconnected.

**Evidence from logs:**

Every reconnect in the server logs followed this pattern:
```
Message received: <question>
WARNING - Shard ID None heartbeat blocked for more than 10 seconds.
WARNING - Shard ID None heartbeat blocked for more than 20 seconds.
WARNING - Shard ID None heartbeat blocked for more than 30 seconds.
...
ERROR - Attempting a reconnect in X.XXs
```

**Evidence from conversations:**
- Conversations 1 (3/10–3/11): 4 errors. Bot restarted between questions.
- Conversations 2 (3/16–3/17): 4 errors, multiple reboots visible. A user reported the bot was "very slow to respond."
- Conversations 3 (3/18, ~2:56–3:27 PM): 6 errors from a single user in ~30 minutes. Errors followed by greeting messages confirm the bot was restarting.

**Fix:**
1. **Interim fix:** Added a "Thinking..." message sent before starting `RAG_query`, to keep the Discord connection alive. This prevented Discord from kicking the bot but didn't solve the underlying heartbeat blocking.
2. **Proper fix:** Made `RAG_query` async. First with `run_in_executor` to unblock the event loop (commit 8611e13), then with a full async rewrite (#38): `RAG_query` became `async def` with `graph.ainvoke()`, and all internal functions (`retrieve`, `generate`, `LLM_Client.chat`) were converted to use `await`. The Discord bot now uses `create_task`.

**Status:** Fixed.

---

## 2. Langfuse v4 auto-update

**Impact:** Caused a cluster of crashes on 3/18 afternoon, shortly after deploying the heartbeat fix.

**Symptoms:** The bot crashed repeatedly in a brief window. All errors showed the "Thinking..." indicator (confirming the timeout fix was active), so these had a different cause from the heartbeat blocking.

**Root cause:** When rebuilding the Docker container to deploy the heartbeat fix, `pip install` pulled Langfuse v4, which introduced breaking API changes incompatible with our v3 code. The previous container had Langfuse v3 installed.

**Evidence from conversations:**
- Conversations 4 (3/18, ~4:45–5:24 PM): 7 errors from a single user testing in Hindi/Urdu. All showed "Thinking..." before the error. Same afternoon as conversations 3, which had a mix of heartbeat and non-heartbeat errors.

**Fix:** Locked the Langfuse dependency to v3 in `pyproject.toml` (commit ab8f834).

**Status:** Fixed.

**Lesson learned:** This is why we need CI tests running inside the Docker image before pushing (#34) — the Langfuse v4 breaking change was only caught in production.

---

## 3. Ollama Cloud concurrency limits (#29)

**Impact:** Intermittent errors that were hard to reproduce — requests sometimes worked, sometimes failed under load.

**Symptoms:** The bot returned "Sorry, something went wrong" or "the AI service returned an error" on valid questions. Some succeeded on retry.

**Root cause:** Ollama Cloud enforces strict concurrency limits:
- `x-ratelimit-max-concurrent: 2` — only 2 requests can run simultaneously.
- `x-ratelimit-queue-limit: 5` — up to 5 more can queue.
- Requests beyond 7 total get rejected (429/500 errors).

Reproduced with a debug script (10 concurrent requests, 3 rejected).

**Evidence from conversations:**
- Conversations 1 (3/11, ~1:25 AM): User asked 3 questions in rapid succession via DM — third one errored. Consistent with rate limiting.
- Conversations 5 (3/19): 1 isolated error.
- Intermittent errors throughout testing that didn't correlate with bot restarts.

**Fix:** Refactored LLM management into `LLM_Client` class. `chat()` tries providers in priority order (`chat_provider_priority` setting) and falls back to the next provider when `ainvoke()` fails. `_select_provider()` retries with error reset after exhausting all providers.

**Status:** Fixed.

---

## 4. Thinking model token budget

**Impact:** Empty or truncated answers from the bot.

**Symptoms:** The bot returned empty answers or answers cut off mid-sentence. Out of 90 test questions with `max_tokens=2500`, ~12 produced empty responses.

**Root cause:** `qwen3-next:80b` (Ollama Cloud) uses a thinking mode where internal reasoning tokens count against the `num_predict` budget. With `max_tokens=500`, the model spent all tokens on thinking and returned empty answers (`response.content == ""`). Raising to 2500 helped but didn't eliminate the problem — the thinking overhead varies per question. The `max_tokens` limit had been added as a quick fix for #33 (message too long — see section 6).

**Fix:** Removed `num_predict` / `max_tokens` entirely (commit 77642f9). The message length problem (#33) should be solved on the sending side (split/truncate before sending to Discord/Telegram), not by limiting the LLM output.

**Status:** Fixed. Empty responses no longer occur.

---

## 5. Bot crashes on reply (#23)

**Impact:** Reported during early testing, could not reproduce later.

**Symptoms:** When a user replied to one of the bot's messages in Discord, the bot responded with "Sorry, something went wrong. Please try again later."

**Investigation:**
- 4 crash examples identified from conversations (3/10–3/18): replies to bot messages about capital flight, tokenisation, crypto, and book recommendations.
- All four retested on 3/21 — bot handled all without errors.
- All interaction patterns tested: direct @mention, reply with/without @mention, DMs with/without @mention — all worked.

**Root cause (probable):** The original crashes were most likely caused by Discord's 2000-character message limit (#33) — replies ask for elaboration, producing longer responses — or by Ollama Cloud 500 errors (#29). Both issues have since been addressed.

**Status:** Closed — not reproducible after #29 and #33 fixes were applied.

---

## 6. Message too long (#33) — NOT FIXED

**Impact:** Crashed both Telegram and Discord bots when answers exceeded platform limits.

**Symptoms:**
- Telegram: `telegram.error.BadRequest: Message is too long` — user never received a response (no error handler was registered).
- Discord: `discord.HTTPException` — bot sent the generic error message.

**Root cause:** Discord has a 2000-character limit and Telegram has a 4096-character limit for messages. The LLM sometimes produced answers exceeding these limits. The bots passed the full answer to the send function, which raised an exception.

**Evidence:**
- Telegram logs (3/17, 02:47): User asked "Can I get rich by trading on the stock market?" — answer exceeded 4096 characters.
- Several Discord errors likely caused by this, especially on follow-up questions which tend to produce longer answers.

**Workaround applied and removed:** Added a `max_tokens` setting (500 tokens) passed as `num_predict` to ChatOllama to limit LLM response length (commit 5fb494a). This caused empty responses with thinking models (see section 4) and was removed in commit 77642f9.

**Status:** Not fixed. The bots still have no message length handling. A proper fix needs to check the message length before sending and split or truncate if it exceeds the platform limit.
