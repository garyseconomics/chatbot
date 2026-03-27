# Latency Report — Chat Model

This report covers the latency of the **chat model** (LLM that generates answers).
Embedding model performance will be analyzed in a separate document.

Data source: user traces exported from our Langfuse server, filtered to real users
(Discord + Telegram) with successful responses only. Analysis done with SQLite
and Claude Code.

## Ollama Cloud latency analysis

Data: 129 successful queries from real users (Discord + Telegram), March 19–21 2026.
Model: `qwen3-next:80b`.

### By platform

| Platform | Queries | Avg    |
|----------|---------|--------|
| Discord  | 65      | 11.2s  |
| Telegram | 64      | 10.3s  |

### Latency distribution

```
 0-5s :   3 ( 2.3%)  #
 5-10s:  62 (48.1%)  ########################
10-15s:  43 (33.3%)  ################
15-20s:  17 (13.2%)  ######
20-30s:   4 ( 3.1%)  #
```

~80% of queries are answered in under 15 seconds.

### Pattern analysis

**Answer length does not affect latency.** Average latency is virtually the same
regardless of answer length (10.4s–11.3s across all size buckets). This is expected
with a thinking model — most time is spent reasoning, not generating output.

| Answer length   | Queries | Avg latency |
|-----------------|---------|-------------|
| < 400 chars     | 34      | 11.0s       |
| 400–800 chars   | 35      | 10.4s       |
| 800–1200 chars  | 33      | 10.6s       |
| 1200–1600 chars | 15      | 11.3s       |
| 1600+ chars     | 12      | 11.0s       |

**No concurrency overload.** 6 clusters of 3+ queries within 60 seconds showed
average latencies (8.5s–11.9s) similar to the overall average. Bursts of queries
do not slow the service down.

**Time of day shows mild variation.** Night/early morning queries average ~10s,
mid-morning ~12–13s. The difference is small and likely noise given the sample size.

**The 4 slowest queries (20–26s)** were all open-ended or complex questions
("tell me about yourself", a detailed follow-up on capital flight). The thinking
model takes longer on questions that require more reasoning to stay in character
or synthesize multiple topics. This is natural variance, not a system problem.

**The 3 fastest queries (3.5–4.5s)** were simple greetings ("Hello", "hello gary bot")
and one off-topic question easily dismissed (asking about a musician's contribution
to macroeconomics). These require minimal thinking — the model quickly recognizes
there's nothing to reason about and responds with a short answer.

### Conclusion

Ollama Cloud latency is consistent at ~10s median with no signs of overload,
time-of-day degradation, or answer-length correlation. The occasional spikes
(20–26s) are explained by question complexity, not infrastructure issues.

## Latency comparison: self-hosted vs cloud

|              | Self-hosted Ollama (`qwen3:32b`) | Ollama Cloud (`qwen3-next:80b`) |
|--------------|----------------------------------|---------------------------------|
| Period       | March 10–18                      | March 19–21                     |
| Queries      | 276                              | 129                             |
| **Average**  | **58.9s**                        | **10.8s**                       |
| **Median**   | **50.3s**                        | **10.0s**                       |
| P90          | 93.4s                            | 16.5s                           |
| P95          | 111.4s                           | 18.6s                           |
| Min          | 15.4s                            | 3.5s                            |
| Max          | 299.1s                           | 26.4s                           |

The switch to Ollama Cloud reduced average latency by ~6x (59s to 10.8s).
The cloud's worst case (26s) is better than the self-hosted's best day average (31s).

### Self-hosted details

Data: 276 successful queries from real users, March 10–18 2026.
Hardware: MakeSpace Madrid AI server — 2 GPUs (3060 + 3090, 36 GB VRAM total),
40-thread Threadripper CPU, 96 GB RAM. The server also hosts a virtual machine
running the bot application and other MakeSpace services, so GPU/CPU resources
are shared.

**Latency distribution:**

```
  0-15s :   0 ( 0.0%)
 15-30s :  47 (17.0%)  ########
 30-45s :  74 (26.8%)  #############
 45-60s :  44 (15.9%)  #######
 60-90s :  77 (27.9%)  #############
 90-120s:  23 ( 8.3%)  ####
120-180s:   6 ( 2.2%)  #
180-300s:   5 ( 1.8%)
```

40% of queries took over a minute. 12% took over 90 seconds.

**Answer length affects latency on self-hosted.** Unlike the cloud, longer answers
cost more time because the server generates tokens slower.

| Answer length   | Queries | Avg latency |
|-----------------|---------|-------------|
| < 400 chars     | 24      | 33.4s       |
| 400–800 chars   | 52      | 38.4s       |
| 800–1200 chars  | 52      | 56.6s       |
| 1200–1600 chars | 52      | 64.9s       |
| 1600+ chars     | 96      | 74.2s       |

**Latency varied significantly by day**, but not due to query concurrency.

| Day        | Queries | Users | Avg latency |
|------------|---------|-------|-------------|
| March 10   | 20      | 6     | 31.2s       |
| March 11   | 21      | 6     | 86.8s       |
| March 12   | 2       | 1     | 38.5s       |
| March 15   | 1       | 1     | 67.2s       |
| March 16   | 94      | 16    | 75.5s       |
| March 17   | 50      | 8     | 67.0s       |
| March 18   | 88      | 10    | 36.4s       |

**No actual concurrency overload.** Despite having up to 16 users and 94 queries
in a single day (March 16), queries never actually overlapped on the server. With
50–90s latency per query and users waiting for answers before asking the next one,
the server was processing one query at a time. Peak hour was 17:00–18:00 on March 16
with 4 users active, but even then queries arrived sequentially.

March 18 had nearly as many queries (88) as March 16 (94) but was twice as fast
(36.4s vs 75.5s). Since concurrency wasn't the issue, the day-to-day variation
was likely caused by other processes on the self-hosted server competing for
resources (GPU/CPU) on the slow days. The bottleneck was raw model speed on
that hardware, not capacity.

**Telegram appeared slower than Discord** (67.7s vs 47.6s) but this is not a
platform difference. Telegram had more queries concentrated on the slowest days
(March 11, 16, 17). On days where both platforms had significant traffic, their
latencies were similar (e.g., March 18: Telegram 36.4s vs Discord 36.5s).

| Day        | Telegram queries | Telegram avg | Discord queries | Discord avg |
|------------|------------------|--------------|-----------------|-------------|
| March 10   | 5                | 26.3s        | 15              | 32.8s       |
| March 11   | 10               | 112.6s       | 11              | 63.3s       |
| March 16   | 74               | 74.7s        | 20              | 78.6s       |
| March 17   | 32               | 76.8s        | 18              | 49.5s       |
| March 18   | 32               | 36.4s        | 56              | 36.5s       |

## Ollama Cloud API limits (free tier)

Ollama Cloud offers three tiers: Free ($0), Pro ($20/month), and Max ($100/month).
We are currently on the **Free tier**. This section documents the known limits
to inform the decision on whether to upgrade for Phase 2.

### Published limits (from ollama.com/pricing)

| | Free | Pro ($20/mo) | Max ($100/mo) |
|---|---|---|---|
| Concurrent cloud models | 1 | 3 | 10 |
| Usage level | "Light usage" | 50x more than Free | 5x more than Pro |
| Session limit reset | Every 5 hours | Every 5 hours | Every 5 hours |
| Weekly limit reset | Every 7 days | Every 7 days | Every 7 days |

- Usage is measured by **GPU time**, not tokens — there are no fixed token caps.
- Session and weekly limits exist but **Ollama does not publish the actual quotas**.
- "Queued requests are held up to a fixed limit" beyond the concurrency slots.
- Prompts and responses are never logged or trained on.
- Embedding models are **not supported** on Ollama Cloud (as of March 2026).

### Observed limits (from our debugging in issue #29)

The rate limit headers returned by Ollama Cloud reveal concrete concurrency
constraints not documented on the pricing page:

- `x-ratelimit-max-concurrent: 2` — max 2 requests actively running at once
- `x-ratelimit-queue-limit: 5` — up to 5 additional requests queued behind active ones
- Requests beyond 7 total (2 active + 5 queued) are rejected with 429 or 500 errors

These limits were discovered by running 10 concurrent requests — 3 out of 10
were rejected. The test can be reproduced with `python -m analytics.test_cloud_limits`.

### Impact on real users

On March 19, 2026, **10 out of 97 queries (~10%) returned empty responses**
due to Ollama Cloud rejecting requests under load. 4 users were affected
(2 Discord, 2 Telegram) over a ~20.5-hour window. See issue #29 for the
full trace analysis.

This was mitigated by the `LLM_Client` refactor (commit 5bf7f09) which
falls back to the next provider when a request fails, but on the free tier
the concurrency limits remain a risk during traffic spikes.

### What's not documented

- The exact session and weekly quotas (how many requests or how much GPU time
  per reset period).
- Whether the concurrency limits (max-concurrent, queue-limit) change between
  tiers — Pro and Max advertise more concurrent *models*, but it's unclear if
  per-model concurrency also increases.
- How "50x more usage" and "5x more usage" translate to actual numbers.

### Considerations for Phase 2

- The free tier handled ~97 queries/day with a ~10% failure rate on the busiest
  day. With the provider fallback in place, failures are less visible to users
  but still add latency when retrying on a slower provider.
- Pro ($20/month) advertises 50x more usage, which should eliminate the session
  and weekly quota pressure. Whether it also raises the concurrency limits
  (currently 2 active + 5 queued) is unknown.
- If Phase 2 expects higher traffic or concurrent users, upgrading to Pro
  would be the first thing to try. The 50x multiplier likely covers our
  current usage patterns with significant headroom.
- **If we upgrade, re-run `python -m analytics.test_cloud_limits`** to check
  whether the `x-ratelimit-max-concurrent` and `x-ratelimit-queue-limit`
  headers change on a paid tier. This would answer the biggest open question
  about whether Pro/Max also raises the per-model concurrency limits.

## Discarded traces

10 queries from real users on March 19, 2026 received empty responses due to
Ollama Cloud rate limiting ([issue #29](https://github.com/garyseconomics/chatbot/issues/29)).
These are excluded from all latency metrics above. They can be identified by
empty answers and sub-1-second latency (0.5–0.9s).
