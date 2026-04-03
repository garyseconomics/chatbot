# Analytics Guide

How to use the analytics scripts, databases, and test tools.

## Quick reference

| Task | Command |
|------|---------|
| Export traces from Langfuse | `python -m analytics.db.export` |
| Import traces into SQLite | `python -m analytics.db.trace_importer` |
| View traces in current DB | `python -m analytics.scripts.trace_viewer` |
| View traces in old DB | `python -m analytics.scripts.trace_viewer_old` |
| Run all test questions | `python -m analytics.scripts.ask_all_questions` |
| Set up database from scratch | `python analytics/db/setup_database.py` |

All commands should be run from the project root with the venv activated.

## Pipeline: Langfuse → SQLite

Traces flow through three steps:

1. **Langfuse cloud** — the chatbot logs every question and answer as a trace.
2. **Export to JSON** — `analytics/db/export.py` downloads traces from Langfuse and
   saves them to `analytics/raw_data/traces_YYYY-MM-DD_HHMMSS.json`.
3. **Import to SQLite** — `analytics/db/trace_importer.py` reads the newest JSON file
   and inserts new traces into `analytics/analytics.db`.

The export script requires `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` in `.env`.
It only fetches traces from 2026-03-28 onwards (when the Langfuse format changed).

The importer deduplicates by trace_id — safe to run multiple times on the same data.

## Databases

### analytics.db (current)

Contains all data from 2026-03-28 onwards (prompt v4). One unified schema.

**`traces` table** — one row per question asked to the bot:

| Column | Description |
|--------|-------------|
| trace_id | Unique Langfuse trace ID (primary key) |
| timestamp | ISO 8601 timestamp |
| user_id | `discord:*`, `telegram:*`, `qa_test`, `cli`, or `benchmark_*` |
| question | The user's question |
| answer | The bot's response |
| prompt_version | Prompt version (currently "4") |
| chat_model | LLM used (e.g., "qwen3-next:80b") |
| chat_provider | LLM provider (e.g., "ollama_cloud") |
| embedding_model | Embedding model used |
| embedding_provider | Embedding provider |
| latency | Total response time in seconds |
| num_results | Number of documents returned by vector search |
| embedding_latency | NULL (not yet populated) |
| chat_latency | NULL (not yet populated) |

**`search_result_documents` table** — links traces to the Chroma document IDs that the
vector search returned as context. Use this to find out what context the bot had when
answering a question:

```sql
SELECT t.question, t.answer, srd.document_id
FROM traces t
JOIN search_result_documents srd ON t.trace_id = srd.trace_id
WHERE t.user_id LIKE 'telegram:%'
ORDER BY t.timestamp;
```

**`document_content` table** — intended for backing up Chroma document text. Currently
empty.

### analytics_old.db (pre-2026-03-28)

Contains all data from before the Langfuse format change. Different schema with
separate tables for different trace types:

- **`user_traces`** (1,073 rows) — real user Q&A from Discord and Telegram. Prompt
  versions v2, v3, and v3.1.
- **`vector_search_traces`** (1,719 rows) — vector search performance data.
- **`test_questions`** (441 rows) — QA test traces imported from Langfuse.
- **`qa_test_results`** (320 rows) — test results written directly by
  `ask_all_questions.py`.
- **`search_result_documents`** (5,388 rows) — same as current DB, links traces to
  Chroma document IDs.

Use `trace_viewer_old.py` to browse this database, or query it directly:

```sql
sqlite3 analytics/analytics_old.db "SELECT user_id, question, answer FROM user_traces WHERE user_id LIKE 'telegram:%' ORDER BY timestamp;"
```

## Useful queries

### Find a specific user's questions and the context they received

```sql
SELECT t.question, t.answer, srd.document_id
FROM traces t
JOIN search_result_documents srd ON t.trace_id = srd.trace_id
WHERE t.user_id = 'telegram:<user_id>'
ORDER BY t.timestamp;
```

### Count questions by user type

```sql
SELECT
  CASE
    WHEN user_id LIKE 'discord:%' THEN 'discord'
    WHEN user_id LIKE 'telegram:%' THEN 'telegram'
    ELSE user_id
  END AS user_type,
  COUNT(*) AS count
FROM traces
GROUP BY user_type
ORDER BY count DESC;
```

### Find all real user questions (exclude test data)

```sql
SELECT timestamp, user_id, question, answer
FROM traces
WHERE user_id LIKE 'discord:%' OR user_id LIKE 'telegram:%'
ORDER BY timestamp;
```

### Find questions where vector search returned no results

```sql
SELECT question, answer, timestamp
FROM traces
WHERE num_results = 0 OR num_results IS NULL
ORDER BY timestamp;
```

### See what context documents were returned for a specific question

To get the full context text, you need the raw JSON exports in `raw_data/` — the
`search_result_documents` table only stores document IDs (Chroma UUIDs), not the text
content. The `document_content` table is not yet populated.

To find the full context for a trace, look it up in the JSON:

```bash
python -c "
import json
with open('analytics/raw_data/traces_2026-04-01_141933.json') as f:
    traces = json.load(f)
for t in traces:
    if t.get('input', {}).get('args', [''])[0] == 'YOUR QUESTION HERE':
        for doc in t.get('output', {}).get('context', []):
            print(doc.get('source', 'unknown'))
            print(doc.get('content', '')[:200])
            print('---')
        break
"
```

Or query Langfuse directly if you have the trace ID.

## Test questions

### questions_for_testing.py

155 questions across 20 categories (e.g., `economics_questions`, `bot_identity`,
`gives_financial_advice`, `answers_off_topic`, `troll_detection`). Used by
`ask_all_questions.py` for batch testing across prompt versions.

### sensitive_questions_for_testing.py (private/)

21 additional questions covering Qwen censorship edge cases and troll detection.
Not tracked in git.

### Running a test

`ask_all_questions.py` sends every question through the full RAG pipeline and logs
results to Langfuse with `user_id="qa_test"`. After running, export and import to
get the results into SQLite:

```bash
python -m analytics.scripts.ask_all_questions
python -m analytics.db.export
python -m analytics.db.trace_importer
```

## Prompt version deployment dates

| Version | Deployed | Commit |
|---------|----------|--------|
| v2 | Before 2026-03-21 04:13 | — |
| v3 | 2026-03-21 04:13 | — |
| v3.1 | 2026-03-23 19:18 | `ce11a6c` |
| v4 | 2026-03-28 ~17:50 | `409addd` |

## raw_data/

JSON exports from Langfuse and reference files. Not tracked in git.

- `traces_*.json` — full Langfuse exports (multiple files, up to 104 MB each)
- `all_user_questions.txt` — extracted list of all real user questions
- `top_user_questions.txt` — most frequently asked questions
- `benchmark_trace_ids.csv` — trace IDs for benchmarking runs

## Other scripts

- **`test_cloud_limits.py`** — tests Ollama Cloud rate limits and concurrency. Sends
  10 concurrent requests and logs rate limit headers.
