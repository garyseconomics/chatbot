# Prompt v3.1 — Trace Analysis

## Timeline

- **v3.1 fix deployed**: 2026-03-23 19:18 (commit `ce11a6c`, confirmed via Discord bot greeting message)
- **What changed from v3**: The v3 prompt was refusing to answer legitimate economics
  questions when the reference material had no relevant information. The v3.1 fix updated
  Steps 3 and 5 so the bot would still answer economics questions using its general
  knowledge when the source material didn't cover the topic. See [prompt_v3.md](prompt_v3.md)
  for the full v3 analysis.
- **v3.1 fix confirmed**: The bot refused several valid economics questions with v3
  (Laffer curve, monopolies, tokenisation, crypto, rent control, solving inequality).
  All answered correctly after the v3.1 fix. See developer testing section below.
- **v4 deployed**: 2026-03-28 ~17:50 (commit `409addd`)


## Developer testing (March 23-24)

Questions previously refused in v3 were retested after the fix:

- "can you explain the laffer curve..." — retested 2026-03-23 at 17:56 and 18:19
- "can you explain to me what the difference is between taxing wealth vs work?"
- "How much do monopolies contribute to the issue of inequality?"

All answered correctly. Confirms the v3.1 fix resolved the refusal issue.

## Bot performance (March 23-25)

~35 real user questions across March 23-25 covering a wide range of topics. 

### What the bot handled well

**Economics questions** — Strong answers on wealth tax policy, taxation vs expropriation,
Gary vs communism, economic growth and inequality, immigration and housing, speculative
property buying, UK politics (Green Party), aggregate demand, capitalism under extreme
inequality, historical patterns of poverty and collapse. Answers were well-grounded in
Gary's content, used accessible language, and included concrete examples.

**Conversational flow without memory** — The bot maintained coherent thematic threads
across long multi-question sessions despite having no conversation memory. Vague follow-up
questions (e.g., referencing a timeframe without restating the topic) were answered
correctly — the RAG retrieved relevant content from the limited context.

**Emotional and personal messages** — The bot gave empathetic, grounded responses to
messages about feeling overwhelmed by inequality and political frustration, without
overstepping into counselling. When asked about contributing, the bot correctly pointed
to the open source GitHub repo.

**Follow-up questions days later** — A returning user asked a follow-up on the Green Party
topic 4 days after their first session. Good answer, correctly grounded in Gary's content.

### Issues found

1. **Financial advice** — When asked about personal investment holdings (gold ETFs), the
   bot gave investment guidance ("stick to your plan", "hold steady"). The bot should not
   tell users what to do with their assets. **Ask Gary's team** how the bot should handle
   questions about personal investment decisions. It could redirect to the systemic issues
   (why asset prices move the way they do) without telling the user what to do.

2. **RAG internals leak** — One instance: "The reference material doesn't mention oil
   prices" when asked about the gold/oil relationship.

3. **Over-eager off-topic deflection** — A short, conversational message about fascism was
   deflected as off-topic ("let's keep it focused on the money stuff"), when the connection
   between fascism and inequality is a core topic Gary has covered (anti-immigrant protests,
   Reform, scapegoating). Two messages later the bot explained the fascism/inequality
   connection perfectly when the question was rephrased in economics terms. Three problems
   compounded:
   - **Short conversational query** — gave the vector search very little to match on.
   - **Over-eager deflection** — the bot should recognise fascism and inequality as
     connected topics Gary has covered.
   - **Multi-turn limitation** — with conversation history (#6), the bot would know the
     conversation had been about inequality for several messages. "Fascism" in that context
     is economics-adjacent, not trolling.

### Questions added to test set

From these sessions, added to `analytics/questions_for_testing.py`:

- "Introduce yourself" → `bot_identity`
- "what do know about microeconomy" → `economics_questions` (kept the typo — tests imperfect input)
- "what do you think about passive incomes?" → `economics_questions`

New questions from real users collected in
[new_questions_from_users.md](new_questions_from_users.md), organised by topic.

