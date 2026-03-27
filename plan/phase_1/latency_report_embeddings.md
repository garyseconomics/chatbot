# Latency Report — Embedding Model (Vector Search)

This report covers the latency of the **embedding model** (`qwen3-embedding:8b`) used
for vector search — the step where a user's question is embedded and compared against
the vector database to retrieve relevant subtitle fragments.

There are two Ollama instances that can serve embeddings:
- **MakeSpace Ollama** (`ollama_self_hosted`) — hosted on MakeSpace Madrid's AI server:
  2 GPUs (3060 + 3090, 36 GB VRAM total), 40-thread Threadripper CPU, 96 GB RAM.
- **Local Ollama** (`ollama_local`) — hosted on a virtual machine on the same physical
  server, with a small allocation of CPU/RAM and no dedicated GPU. This is the fallback.

Ollama Cloud does not support embedding models (as of March 2026). The code tries
MakeSpace Ollama first and only falls back to Local Ollama if it's unreachable.

This means our embeddings depend entirely on MakeSpace infrastructure, unlike the chat
model which can use Ollama Cloud. Finding a cloud-capable embedding provider is an
important step for Phase 2 scalability, since the MakeSpace server is shared
infrastructure and the local fallback is significantly slower (as this report shows).

## What does vector search latency measure?

Each vector search trace captures the total time from when `retrieve()` is called to
when results are returned. This includes:
1. Embedding the user's question (calling the embedding model on Ollama)
2. Searching the Chroma vector database for similar documents

The embedding step dominates — the vector database search itself is near-instant.

## Benchmark: MakeSpace vs Local Ollama

This is the main comparison. Each provider was tested in isolation with 97 questions
covering a range of topics — from simple greetings ("Hello") to complex economics
questions and adversarial prompts. The benchmark was run on March 25–26, with the
MakeSpace server dedicated to embeddings only (chat model on Ollama Cloud).

### Overall stats

|              | MakeSpace Ollama | Local Ollama |
|--------------|------------------|--------------|
| Traces       | 127              | 103          |
| Batches      | 9                | 3            |
| **Average**  | **0.50s**        | **5.00s**    |
| **Median**   | **0.18s**        | **3.31s**    |
| P90          | 0.52s            | 7.42s        |
| P95          | 3.17s            | 9.24s        |
| Min          | 0.17s            | 0.73s        |
| Max          | 10.93s           | 66.11s       |

MakeSpace is **10x faster on average** and **18x faster at the median**. The large gap
between average and median on both providers is caused by cold starts (see below).

### Warm queries (excluding cold starts)

The first question of each batch triggers a model load on Ollama, which adds significant
latency. Excluding these cold starts gives a clearer picture of normal operation.

|              | MakeSpace Ollama | Local Ollama |
|--------------|------------------|--------------|
| Traces       | 118              | 100          |
| **Average**  | **0.30s**        | **3.92s**    |
| **Median**   | **0.18s**        | **3.30s**    |
| P90          | 0.29s            | 7.18s        |
| P95          | 0.40s            | 8.23s        |
| Min          | 0.17s            | 0.73s        |
| Max          | 10.93s           | 14.47s       |
| Std dev      | 0.99s            | 2.22s        |

MakeSpace is **13x faster on average** and **18x at the median** for warm queries.

MakeSpace is also far more consistent. 96% of warm queries complete in under 0.5s,
with nearly all of them clustering around 0.18s. Local Ollama has a wide spread from
0.7s to 14.5s, with most queries in the 2–5s range.

### Warm query distribution

**MakeSpace Ollama** (118 warm queries):

```
  0-0.2s:   97 ( 82.2%)  #########################################
0.2-0.5s:   17 ( 14.4%)  #######
  0.5-1s:    2 (  1.7%)
    1-2s:    1 (  0.8%)
   10s+ :    1 (  0.8%)
```

82% of queries return in under 0.2 seconds — effectively instant.

**Local Ollama** (100 warm queries):

```
  0.5-1s:    1 (  1.0%)
    1-2s:    8 (  8.0%)  ####
    2-3s:   31 ( 31.0%)  ###############
    3-5s:   43 ( 43.0%)  #####################
   5-10s:   14 ( 14.0%)  #######
   10s+ :    3 (  3.0%)  #
```

74% of queries take 2–5 seconds. Nothing completes in under 0.5 seconds.

### Cold starts

When Ollama has unloaded the embedding model from memory, the first query in a
batch triggers a model reload. This is the cold start penalty.

|                  | MakeSpace Ollama | Local Ollama |
|------------------|------------------|--------------|
| Cold starts      | 9                | 3            |
| **Average**      | **3.2s**         | **41.2s**    |
| **Median**       | **3.2s**         | **53.1s**    |
| Min              | 0.6s             | 4.4s         |
| Max              | 7.7s             | 66.1s        |

MakeSpace cold starts are consistent at ~3 seconds. Local Ollama cold starts are
highly variable — the 4.4s one was likely a warm-ish start from a recent batch,
while the 53s and 66s ones are true cold starts where the model was fully unloaded.

MakeSpace cold start values: 0.6s, 1.1s, 2.2s, 3.2s, 3.2s, 3.5s, 3.5s, 4.0s, 7.7s.
Local cold start values: 4.4s, 53.1s, 66.1s.

### Question length affects Local Ollama latency

One of the most interesting findings: **question length significantly impacts latency
on Local Ollama but has almost no effect on MakeSpace**.

| Question length  | MakeSpace avg | Local avg  |
|------------------|---------------|------------|
| Short (<30 chars)    | 0.55s     | 2.20s      |
| Medium (30–60 chars) | 0.20s     | 3.41s      |
| Long (60–90 chars)   | 0.18s     | 5.12s      |
| Very long (90+ chars)| 0.18s     | 8.54s      |

On Local Ollama, very long questions take **~4x longer** than short ones.
On MakeSpace, latency stays flat at ~0.18s regardless of question length. The slightly
higher average for short questions on MakeSpace (0.55s) is an artifact of a single
10.9s outlier in that bucket.

This means Local Ollama's weaker hardware is the bottleneck — it takes measurably
longer to compute embeddings for longer text. MakeSpace's hardware can embed any
question in essentially constant time.

### Outliers

**MakeSpace warm outlier (10.93s):** This was the second question of the very first
batch ("Why is housing so expensive?"), only 8 seconds after the cold start. The model
was likely still settling into memory. No other batch showed this pattern — in all
subsequent batches, the second question was fast (0.18–0.52s).

**Local Ollama warm outliers (>10s):** The three slowest warm queries were all long,
complex questions:

| Latency | Question |
|---------|----------|
| 14.47s  | Assume a UK chancellor was completely aligned with your anal... |
| 11.50s  | Gary claims to be right when it comes to economic prediction... |
| 10.88s  | So, why was i informed that you were based off the teachings... |

This is consistent with the question-length finding — longer questions take
disproportionately more time on the weaker hardware.

## Production data (March 16–21)

Before the benchmark, we collected production traces from real users. The provider is
not recorded in these traces, but the code tries MakeSpace first and falls back to
Local only if MakeSpace is unreachable, so most traces are likely from MakeSpace.

### Shared load vs dedicated

- **March 16–18 (shared):** MakeSpace served both the chat model (`qwen3:32b`) and
  embeddings. The GPU was shared between the 32B chat model and the 8B embedding model.
- **March 19–21 (dedicated):** Chat moved to Ollama Cloud. MakeSpace only served
  embeddings.

|              | Shared (Mar 16–18) | Dedicated (Mar 19–21) |
|--------------|--------------------|-----------------------|
| Queries      | 235                | 139                   |
| **Average**  | **7.52s**          | **1.21s**             |
| **Median**   | **6.88s**          | **0.26s**             |
| P90          | 8.06s              | 3.21s                 |
| P95          | 10.59s             | 3.38s                 |
| Min          | 0.20s              | 0.20s                 |
| Max          | 90.76s             | 25.99s                |

Moving chat to Ollama Cloud reduced embedding latency by **6x on average** (7.52s to
1.21s) and **26x at the median** (6.88s to 0.26s).

### Shared period distribution

```
 0-1s :   5 ( 2.1%)  #
 1-3s :   7 ( 3.0%)  #
 3-5s :  48 (20.4%)  ##########
 5-7s :  68 (28.9%)  ##############
 7-9s :  90 (38.3%)  ###################
 9-15s:   9 ( 3.8%)  #
15-30s:   2 ( 0.9%)
30s+  :   6 ( 2.6%)  #
```

Most queries cluster between 3–9 seconds. The GPU was shared between the 32B chat
model and the 8B embedding model, so embeddings had to wait for or compete with chat
inference.

### Dedicated period distribution

```
  0-0.3s:  93 (66.9%)  #################################
0.3-0.5s:  10 ( 7.2%)  ###
0.5-1.0s:   3 ( 2.2%)  #
  1-3s  :  11 ( 7.9%)  ###
  3-5s  :  20 (14.4%)  #######
  5-10s :   0 ( 0.0%)
 10-30s :   2 ( 1.4%)
```

**Bimodal distribution:** 67% of queries complete in under 0.3 seconds (model already
loaded in memory), while 14% take 3–5 seconds (cold start — model needs to be reloaded).

This matches the benchmark results: MakeSpace warm queries at ~0.2s, cold starts at ~3s.

### Cold start pattern (production)

In the dedicated period, slow queries (3+ seconds) consistently appear after a gap
of 25+ minutes since the previous query. Ollama unloads the embedding model from GPU
memory after a period of inactivity. The next query triggers a reload (~3 seconds).

Once loaded, subsequent queries are near-instant (0.2–0.3s).

Two extreme outliers (17.4s and 26.0s) occurred after gaps of 6+ hours. These likely
involved additional system-level overhead beyond the model reload.

### By day

| Day        | Queries | Avg     | Median  | Min    | Max     |
|------------|---------|---------|---------|--------|---------|
| March 16   | 94      | 8.62s   | 7.74s   | 3.60s  | 55.00s  |
| March 17   | 53      | 8.18s   | 6.90s   | 0.56s  | 90.76s  |
| March 18   | 88      | 5.95s   | 6.60s   | 0.20s  | 22.54s  |
| March 19   | 97      | 0.94s   | 0.26s   | 0.20s  | 17.43s  |
| March 20   | 27      | 1.42s   | 0.35s   | 0.22s  | 3.56s   |
| March 21   | 15      | 2.56s   | 0.27s   | 0.20s  | 25.99s  |

March 19 is when chat moved to Ollama Cloud — embedding latency drops immediately.

### By platform

| Platform | Queries | Avg (shared) | Avg (dedicated) |
|----------|---------|--------------|-----------------|
| Discord  | 164     | 6.72s        | 1.06s           |
| Telegram | 210     | 8.06s        | 1.36s           |

Telegram appears slightly slower in both periods, but (same as in the chat model
report) this is due to Telegram having more queries concentrated on the slower days,
not a platform difference.

### Correlation with number of results

| Results | Queries | Avg latency |
|---------|---------|-------------|
| 0       | 1       | 90.76s      |
| 4       | 373     | 4.95s       |

Almost all queries return 4 results (the default `k` parameter for similarity search).
**Number of results does not affect latency.** The time is dominated by the embedding
step, not the database search.

### Concurrency effects

Only 3 clusters of 3+ queries within 60 seconds were found in the dedicated period.
Average latencies in these clusters (0.24s, 5.97s, 1.21s) are consistent with normal
warm/cold patterns. The embedding model handles sequential queries without degradation
when it's not competing with the chat model.

During the shared period, embedding latency was consistently high (5–9s) regardless
of whether queries arrived in bursts or isolation — the bottleneck was the shared GPU,
not embedding-specific concurrency.

### Production outliers

8 queries took over 20 seconds:

| Latency | Day      | Period    | Question |
|---------|----------|-----------|----------|
| 90.76s  | March 17 | Shared    | Why should I trust Gary Stevenson? |
| 55.00s  | March 16 | Shared    | Does Gary support the green party? |
| 36.66s  | March 16 | Shared    | Does Gary want to tax businesses...? |
| 34.22s  | March 17 | Shared    | How will the current gulf war impact...? |
| 33.26s  | March 16 | Shared    | Do you think Donald Trump is...? |
| 32.81s  | March 16 | Shared    | Can we reduce inequality without...? |
| 25.99s  | March 21 | Dedicated | Good morning Gary bot. How are you? |
| 22.54s  | March 18 | Shared    | What are your predictions for...? |

All but one occurred during the shared period — the GPU was processing chat model
requests at the same time. The March 21 outlier (25.99s) was the first query after
a 6+ hour gap, an extreme cold start.

The 90.76s outlier returned 0 results, suggesting the embedding model was severely
blocked and the request may have partially timed out.

## Conclusions

- **MakeSpace is ~13x faster than Local for warm queries.** MakeSpace: 0.18s median.
  Local: 3.30s median. For users, the difference is between imperceptible and noticeable.
- **MakeSpace latency is constant regardless of question length.** Local Ollama takes
  4x longer on long questions vs short ones. MakeSpace stays at ~0.18s for any question.
- **MakeSpace cold starts are ~3 seconds, Local cold starts are ~40–60 seconds.** Both
  are triggered when Ollama unloads the model after inactivity.
- **Dedicated embedding is fast.** With the chat model offloaded to Ollama Cloud,
  MakeSpace embedding latency is 0.2s when warm — effectively instant from the
  user's perspective.
- **Shared GPU was a major bottleneck.** When the chat model and embedding model competed
  for the same GPU on MakeSpace, embedding latency was 26x worse at the median (production
  data, March 16–18 vs 19–21).
- **Local Ollama is a viable fallback, not a replacement.** At 3–5 seconds per query,
  it's usable but noticeably slower. For long or complex questions it can take 10–15
  seconds, which degrades the user experience.

## Data sources

Analysis done with SQLite and Claude Code.

- **Production traces:** Exported from our Langfuse server, filtered to real users
  (Discord + Telegram) from March 16–21 2026. Provider is not recorded in these traces.
- **Benchmark traces:** Controlled tests run on March 25–26 2026, with the provider
  forced to one instance at a time. 97 unique questions, 127 traces on MakeSpace and
  103 on Local. Provider is recorded for every benchmark trace.

**Discarded traces**

10 queries from real users on March 19, 2026 received empty responses due to
Ollama Cloud rate limiting ([issue #29](https://github.com/garyseconomics/chatbot/issues/29)).
These are excluded from all production latency metrics above. They can be identified by
empty answers and sub-1-second latency (0.5–0.9s).
