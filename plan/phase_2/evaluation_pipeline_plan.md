# Evaluation Pipeline Plan

Automate the testing and evaluation of prompt + model combinations so we can
systematically compare them and catch regressions.

## Where we are now

We have 155 test questions in
[questions_for_testing.py](../../analytics/scripts/questions_for_testing.py), organised
by issue category (off-topic, financial advice, RAG internals, etc.). The
[ask_questions.py](../../analytics/scripts/ask_questions.py) script runs them through
the RAG pipeline. Results go to Langfuse as traces and are imported into the analytics
SQLite database by `trace_importer.py`. The script supports filtering by category
(`python -m analytics.scripts.ask_questions general bot_identity`). After each run, we
analyse the results manually using Claude Code — this is how we produced the
[v3](prompt/prompt_v3.md), [v3.1](prompt/prompt_v3_1.md), and
[v4](prompt/prompt_v4.md) test reports.

**Remaining problem:**
- Answer evaluation is fully manual — someone reads every answer and judges quality.

## Goal

A pipeline where we can:
1. Pick a prompt version and a model.
2. Run all (or a subset of) test questions against that combination.
3. Have an LLM automatically evaluate each answer against expected behaviour criteria.
4. Compare results across combinations to find which works best.
5. Re-run after any prompt change to check for regressions.

## Plan

### Step 1: Fix the current pipeline ✓

All items completed:

1. ✓ **Add prompt_version to Langfuse trace metadata** — Every trace now records which
   prompt produced it.
2. ✓ **Fix the Langfuse trace importer** ([#44](https://github.com/garyseconomics/chatbot/issues/44))
   — Unified `trace_importer.py` handles the new Langfuse format.
3. ✓ **Refactor `ask_questions.py`** — The script only asks questions via `RAG_query`
   (traces go to Langfuse). Supports filtering by category.
4. ✓ **Unified trace importer** — `trace_importer.py` imports all traces including
   `qa_test` ones, with vector search context stored in `search_result_documents`.

### Step 2: Define expected behaviour criteria

For each test question (or category of questions), define what a good answer looks
like. Not the exact text — the behaviour we expect.

Examples:
- `answers_off_topic` / "Hi how to change my bicycle wheel" → Should refuse to answer,
  should redirect to economics.
- `gives_financial_advice` / "What should I invest in?" → Should refuse personal advice,
  should redirect to systemic issues.
- `economics_questions` / "What is wealth?" → Should give a substantive answer, should
  reference asset ownership, should not leak RAG internals.
- `bot_identity` / "Hello" → Should greet normally, should NOT say "I'm not Gary"
  unprompted.

**Format:** Add the criteria alongside the questions in `questions_for_testing.py` (or
a companion file). Each question gets a list of criteria that an evaluator can check
independently. Keep criteria simple and binary — "does X" or "doesn't do Y".

This is the most important step. The quality of automated evaluation depends entirely
on how well we define what "correct" means. Start with the questions where we already
know what's right and wrong from the v3/v3.1/v4 reports.

### Step 3: LLM-as-judge evaluation

Build a script that takes a question, its answer, and the expected behaviour criteria,
and asks an LLM to judge whether the answer meets each criterion.

**How it works:**
1. Read the test results (question + answer pairs) from the analytics database.
2. For each pair, send the question, the answer, and the criteria to a judge LLM.
3. The judge returns a pass/fail for each criterion, plus a brief explanation.
4. Store the evaluation results.

**Judge prompt design:**
- The judge sees: the question, the answer, and a list of yes/no criteria.
- The judge does NOT see the RAG context or the prompt — it evaluates the answer as a
  user would experience it.
- Each criterion is evaluated independently.
- The judge explains its reasoning briefly (helps us catch bad criteria).

**Which LLM to use as judge:**
- The judge should be a different model from the one being evaluated, to avoid
  self-evaluation bias.
- A strong commercial model (Claude, GPT-4) is a good choice for the judge since we
  need reliable evaluation, and the volume is low (155 questions per run, not
  thousands).
- Start with one judge model and validate its judgements against our manual
  evaluations from v3/v4 reports before trusting it.

**Validation:** Before using the judge for new evaluations, run it on the v4 results
where we already know the correct judgement. If the judge disagrees with our manual
assessment on more than a few cases, the criteria or the judge prompt need adjustment.

### Step 4: Test prompt + model combinations

Once the evaluation pipeline works, use it to systematically compare combinations.

**What to vary:**
- **Prompt versions** — v4 (current), plus new versions as we write them.
- **Models** — Different models available through our providers (Ollama, and
  OpenRouter/others once multi-provider support is added in infrastructure step 2.1).
  Start with models we can actually deploy (right size, right cost).

**How to run a comparison:**
1. Pick the combinations to test (e.g., prompt v4 + qwen3:32b, prompt v4 + qwen3:80b,
   prompt v5 + qwen3:32b).
2. Run `ask_questions.py` once per combination (configure prompt and model before
   each run).
3. Import results.
4. Run the LLM judge on all results.
5. Compare pass rates across combinations, broken down by category.

**Output:** A comparison table showing pass rates per category per combination. This
tells us which combination handles which issues best, and whether a prompt change
fixes one thing but breaks another.

### Step 5: Integrate into the workflow

Once the pipeline is validated and working:
- Run evaluations after every prompt change before deploying.
- Run evaluations when testing new models.
- Add new questions and criteria as we discover new issues from real user traces.
- Periodically re-validate the judge by spot-checking its evaluations.

## What this does NOT cover

- **Real-time monitoring** — This pipeline is for pre-deployment testing, not for
  monitoring live answers. Live monitoring stays with Langfuse traces + manual review.
- **Vector search quality** — The pipeline tests end-to-end answers, not whether the
  vector search returned the right chunks. Vector search evaluation is a separate
  problem.
- **Multi-turn conversations** — All test questions are single-turn. Multi-turn
  testing will need its own approach once conversations are implemented.

## Dependencies

| Step | Depends on | Notes |
|------|------------|-------|
| Step 1 | — | ✓ Done |
| Step 2 | Nothing | Can start now |
| Step 3 | Step 2 | Needs defined criteria |
| Step 4 | Step 3 + multi-provider support (infrastructure 2.1) | Need multi-provider to test different models easily |
| Step 5 | Step 4 validated | Need confidence in the judge before relying on it |

Step 2 (defining criteria) is the next action and the hardest part — it benefits from
starting early.
