# Testing Phase Plan

Rollout plan for the Gary's Economics chatbot, from prototype to public release.

## Decisions made

1. **License: GPLv3** — Done. Repo is public under GPLv3.
2. **Volunteer bug triage: approved** — Volunteers will review feedback from Discord/Telegram
   and create GitHub issues.
3. **Load balancing to external APIs: approved** — Will balance requests between self-hosted
   Ollama and external LLM services via APIs. Implementation details to be decided later.

### Open decisions (to revisit during Phase 1)

1. **Which external LLM services to test** — Budget and provider selection.
2. **Concurrency limits** — Sysadmin estimated ~10 concurrent users on current infra.
   Phase 1 (100 users) will validate this. What's the plan if we hit the limit?
3. **Load balancing implementation details** — Strategy (round-robin, percentage-based,
   fallback, etc.) and routing layer design.

### Actionable tasks Phase 1

| Task | Owner | Notes |
|------|-------|-------|
| Fix bot impersonation (#25) | dev | Now issue #33 |
| Verify Langfuse traces (#17) | sysadmin | Needed for metrics |
| Set up Langfuse dashboards | sysadmin | To visualize key metrics |
| Implement routing layer for LLM backends | dev | Ollama + external APIs |
| Recruit feedback-to-GitHub volunteers | Team | Review bug reports, create issues |
| Write tester guide | Team | What to test, how to report |
| Build eval dataset from known issues | dev | Problematic questions + expected behavior |
| Build eval pipeline (prompt × model × LLM judge) | dev | Systematic prompt comparison |
| Set up auto-update for Docker containers | sysadmin | Watchtower or webhook |
| ~~Switch license from CC0 to GPLv3~~ | Team | Done |

---

## Phases overview

| Phase | Users | Focus | Infrastructure |
|-------|-------|-------|----------------|
| **Phase 0** (previous) | ~5 devs/testers | Prototype, core functionality | Small server + remote Ollama |
| **Phase 1** (current) | ~100 signed-up testers | Answer quality + resource measurement | Same server + start using external LLM APIs |
| **Phase 2** | ~3,000 Patreons | Stability, cost validation | Bigger server + external LLM service |
| **Phase 3** | 1M+ YouTube subscribers | Scale | Production infrastructure |

---

## Phase 0 — Prototype (previous)

Bot worked on Discord and Telegram. Small group of testers
had already found several issues (impersonation, tone, RAG leaks).

## Phase 1 — 100 Testers

### Goal A: Answer quality

Find all "the bot said something wrong/weird" issues before the bot reaches a wider
audience.

#### Feedback collection

- **Discord channel** dedicated to bot feedback.
- **Telegram group** for testers.
- **Volunteers** with access to the GitHub repo review bug reports from Discord/Telegram
  and create GitHub issues.

**Tasks:**

- [x] Write a short guide for testers: what to test, how to report.
- [x] Form to report the feedback

#### Prompt evaluation system

We expect to iterate on the prompt based on feedback. Different LLM backends will also
behave differently with the same prompt. We need a systematic way to evaluate combinations
of (prompt version × model).

**The evaluation dataset:**

A growing collection of "problematic questions" — questions that have exposed issues.
Each entry contains:

- The question
- Description of the problem (e.g., "bot impersonated Gary", "bot gave a neutral answer
  on a topic where the channel has a clear position")
- Expected correct behavior (e.g., "should clarify it's a chatbot, not Gary",
  "should reflect the channel's critical view on crypto")

This dataset starts with known issues from Phase 0 and grows with Phase 1 feedback.

**Tasks:**

- [x] Iterate on the prompt based on tester feedback
- [x] Add new problematic questions to the evaluation dataset as they are discovered

### Goal B: Resource estimation

Measure actual usage to project costs for Phase 2 and Phase 3.

#### Monitoring and metrics

We can already extract data from Langfuse. Need to explore how to visualize it usefully.

**Key metrics to track:**

- Queries per user per day (usage intensity)
- Response time per query (user experience)
- Token usage per query — prompt + context + response (cost projection)
- Concurrent users and how performance degrades under load
- Error rate (failed queries, timeouts)

**Tasks:**

- [ ] Explore Langfuse dashboards and find/build useful visualizations for the key metrics
- [ ] Validate the sysadmin's "up to 10 concurrent users" estimate with the 100 testers

#### Load balancing with external LLM APIs

Start sending some requests to external LLM services via APIs while keeping self-hosted
Ollama. This lets us:

- Test how external models perform with our prompts (feeds into the eval system above)
- Measure API costs with real traffic
- Test load balancing between multiple backends

**Tasks:**

- [x] Implement a routing layer to distribute requests between Ollama and external APIs
- [ ] Decide load balancing strategy with sysadmin (round-robin, percentage-based,
  fallback, etc.)
- [ ] Track cost per query for each backend in Langfuse/logs
- [ ] Compare response quality across backends (using the eval system)

#### Cost projection

After Phase 1, use the collected metrics to estimate:

- [ ] Server requirements for Phase 2 (3K users) and Phase 3 (1M+ subscribers, estimate
  active %)
- [ ] Monthly LLM API cost at Phase 2 and Phase 3 scale
- [ ] Whether self-hosted Ollama remains viable at any scale, or if full API is needed

---

## Phase 2 — Patreon (3,000 users)

_To be detailed after Phase 1 learnings. High-level goals:_

- Announce bot on Gary's Economics Patreon
- Run on validated infrastructure (bigger server + chosen LLM backend)
- Prompt and model combination settled based on Phase 1 eval results
- Monitor costs and stability at 30× the Phase 1 scale

---

## Phase 3 — YouTube (1M+ subscribers)

_To be detailed after Phase 2 learnings. High-level goals:_

- Announce bot on the YouTube channel
- Production-grade infrastructure scaled for estimated active user percentage
- Cost model validated at Phase 2 scale, projected for Phase 3
