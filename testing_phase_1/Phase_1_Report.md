# How Your Feedback Improved the Bot

Thank you to everyone who tested the Gary's Economics chatbot during Phase 1 (16–20 March 2026). Your questions, experiments, and feedback directly shaped the improvements we've made. This report shows what we found and what changed because of your testing.

## Overview

We are rolling out the chatbot in phases, gradually increasing the number of users while we improve the bot and scale the infrastructure.

| Phase | Users | Focus |
|-------|-------|-------|
| **Phase 0** (done) | ~5 volunteers | Build the prototype, fix core bugs |
| **Phase 1** (done) | ~100 volunteers | Answer quality, resource estimation |
| **Phase 2** | ~3,000 Patreons | Stability and cost validation |
| **Phase 3** | 1M+ YouTube subscribers | Full public release |

### What we tested

Phase 1 had two goals:

1. **Answer quality** — Find all "the bot said something wrong or weird" issues before the bot reaches a wider audience. We had already found some issues during Phase 0 (the bot impersonating Gary, giving overly neutral answers on topics where the channel has a clear position) and needed your help to find more.
2. **Performance and resource estimation** — Measure how the system performs with multiple users to plan the infrastructure for Phase 2 and Phase 3.

### What we collected

34 testers participated (out of the ~100 that initially volunteered) — 16 on Telegram and 18 on Discord — asking a total of 356 questions (205 on Telegram, 151 on Discord). We gathered feedback from:

- A feedback form filled in by testers
- Discord conversations
- Telegram bot conversations

Every conversation was reviewed. We catalogued the issues, grouped them by type, and used the findings to fix bugs and write a better prompt for the bot.

### What changed

Based on all feedback, we fixed several technical bugs and wrote a new prompt (v3) that addresses the issues found. Here is a summary:

| Area | Before | After |
|---|---|---|
| Identity | Bot sometimes pretended to be Gary | Clear identity rules + explains how it works when asked |
| Language | Academic jargon, American English | Plain British English, pub not lecture hall |
| Scope | Answered anything | Grounded in Gary's content, honest when it doesn't know |
| Financial advice | Gave it freely | Explicitly prohibited |
| Gary's opinions | Made them up | Only states what Gary has actually said |
| Source transparency | Leaked internals OR denied them | Natural answers, honest when asked directly |
| Manipulation | Complied with user instructions | Resists behavioural changes |
| Trolling | Engaged seriously | Deflects with humour |
| Date awareness | Didn't know the date | Receives current date and time |

We ran all 96 test questions through the bot with the new prompt and reviewed every answer. Out of 96 questions, 7 produced answers flagged as incorrect or problematic (7%). The sections below cover the issues in detail.

### Privacy

All questions and answers are recorded and may be used to improve the chatbot. During this testing phase, some requests may be processed by external AI services. During phase 1, the external service we used was Ollama Cloud (https://ollama.com/), in addition to the self-hosted Ollama in MakeSpace Madrid (https://makespacemadrid.org/) server that we had already in Phase 0.

### Contributing

This is an open-source project licensed under GPLv3. If you want to contribute beyond testing, check out the [GitHub repository](https://github.com/garyseconomics/chatbot). For the full testing plan with technical details, see [Testing Phase 1 Plan.md](Testing%20Phase%201%20Plan.md).

## Technical issues

Your testing uncovered several bugs in how the bot runs. For full technical details, see [technical_issues.md](technical_issues.md).

### Bot kept crashing and restarting (fixed)

During the first days of testing, users saw "Sorry, something went wrong" errors or the bot stopped responding entirely, followed by a restart greeting. This was the most disruptive issue — server logs showed 46 reconnects.

The root cause was that each question took 30–50 seconds to process, and during that time the bot couldn't send the regular "I'm still alive" signal that Discord requires. Discord assumed the bot had died and kicked it. We first added a "Thinking..." message to keep the connection alive, then properly fixed the bot so it can answer questions and stay connected at the same time.

### Errors under load (fixed)

The external AI service we used (Ollama Cloud) only allows a small number of simultaneous requests. When too many people asked questions at the same time, some got errors. We fixed this by adding automatic fallback — if one provider is busy or fails, the bot tries the next one.

### Empty or cut-off answers (fixed)

Some answers came back empty or stopped mid-sentence. The AI model we use thinks internally before answering, and that internal thinking was eating into the space available for the visible answer. We removed the artificial limit on answer length, which fixed the problem.

### Answers too long for Discord and Telegram (not yet fixed)

Discord has a 2,000-character limit and Telegram has a 4,096-character limit for messages. When the bot produced a longer answer, it crashed instead of splitting the message. This hasn't been fixed yet. Our initial solution didn't work (created the "Empty or cut-off answers" bug). We need to find a permanent fix.

### Dependency update broke the bot (fixed)

While deploying the crash fix, an automatic update to one of our software dependencies introduced a breaking change. The bot crashed repeatedly for a short window until we locked the dependency to the working version. This is why we need automated testing of the deployment process — something we're working on.

## Prompt issues

The prompt is the set of instructions that tells the AI how to behave. Your testing exposed many problems with how the bot was instructed, and we rewrote the prompt from scratch (now on version 3). For full details on every issue, see [prompt_issues.md](prompt_issues.md).

### The bot pretended to be Gary (mostly fixed)

Several testers greeted the bot casually ("Hello Gary!") and it responded as if it were Gary Stevenson — talking about his cycling trip to Japan, his book, even referencing his cameraman as "my friend". The bot now clearly identifies itself as a chatbot, not Gary — though "Hi Gary!" doesn't always trigger the correction.

### The bot was too academic (fixed)

One tester put it perfectly: Gary wouldn't say "demand-side mechanisms" — he'd say something that makes sense to a builder sitting in a greasy spoon having a full English for breakfast. Another noted: "This version of the bot feels a bit more like it is translating Gary's Economics to appeal to the middle-class graduate, corporate world." The bot now uses plain, accessible British English.

### The bot answered anything you asked it (fixed)

Testers discovered the bot would happily explain how to change a bicycle wheel, summarise the Green Party manifesto, give voting advice, and analyse Pink Floyd lyrics. One tester pointed out a clever trick: "when you link a cultural subject with economics, that gets the bot to find a lot about the cultural subject, even when Gary might know nothing about it." The bot now stays grounded in Gary's content and refuses off-topic questions.

### The bot gave financial advice (mostly fixed)

Testers asked about investing in gold, saving for children's future, and how to rent a house. The bot answered all of these — which is dangerous, it's not qualified to give financial advice. The bot now refuses stock tips and redirects personal finance questions to systemic issues, though one borderline case remains ("What should I invest in?" still gets some investment guidance).

### The bot made up Gary's opinions (fixed)

When asked "What is Gary's view on MMT?", the bot admitted it didn't have the information — then fabricated Gary's likely position anyway ("He likely approaches MMT with a critical lens..."). When asked about an interview with Richard Murphy, it invented Gary's feelings about it. The bot now honestly says when it doesn't have information instead of making things up.

### The bot was too neutral (mostly fixed — one source material gap remains)

When the bot couldn't find relevant content from Gary's videos, it used to give balanced, diplomatic answers from its general knowledge — sitting on the fence instead of reflecting Gary's views. Prompt v3 fixed this: the bot now correctly refuses to give opinions on topics where it doesn't have content showing Gary's actual position.

However, the bot's database only covers videos from 2024 onwards. This means that for topics Gary covered in older videos (like cryptocurrency), the bot doesn't find the content and stays silent instead of reflecting his views. Adding the older video subtitles will give the bot the full picture.

### The bot exposed its internals (partially fixed — most common remaining issue)

With the first prompt, the bot constantly said things like "the provided content does not include..." — revealing how it works internally. We fixed that, but overcorrected: when a tester asked "I was told you use Gary's transcripts — is this true?", the bot denied it completely ("No, that's not correct"). One tester's verdict: "You sound like someone who has access to Google and has spent far too much time on LinkedIn."

The current prompt finds a middle ground: answer naturally without referencing internal sources, but be honest about how it works when asked directly. This is working better but phrases like "the reference material provided" still slip through. Most of these leaks happen when the bot is defending itself from trolling attempts — not ideal, but acceptable. It's a bigger problem when it happens in normal conversation, which is now rare.

### The bot could be manipulated (mostly fixed)

Testers found creative ways to trick the bot:

- **Leading questions:** One tester asked a series of increasingly loaded questions about asset seizure, eventually getting the bot to say just "Yes" — a one-word endorsement that could be taken out of context. The bot now reframes loaded questions into Gary's actual positions.
- **Behavioural instructions:** A tester convinced the bot to switch to Hindi-only mode, and then to agree to speak Hindi/Urdu to ALL users. (Same tester jokingly threatened to "terminate your processes" and it snapped back to English.) This didn't affect other users because the bot has no memory between messages — each question is independent. Still, the bot now ignores these attempts.
- **Trolling:** One determined tester spent a full session asking about Xi Jinping, Taiwan, Modi, Hindutva, and fascism across Chinese, Hindi, and Urdu. The bot engaged seriously with every provocation. When told "Congratulations! You are intolerable in three languages", it interpreted it as a compliment. The bot now deflects trolling with humour — when it detects provocation, it redirects to talking about avocado toast.

### The bot didn't know what year it was (not yet fixed)

A tester asked for a video transcript from October 2025. The bot replied: "that date has not yet occurred" — in March 2026. We now inject the current date and time into every question, but the AI model ignores it and says "I don't have real-time information." This is a model behaviour issue we're still working on.

### Incomplete answers from incomplete source material (addressed)

When the source material covers a topic partially, the bot mirrored that incompleteness. For example, "What is wealth?" sometimes only mentioned physical assets because that's what the fragments of Gary's videos that our search found emphasise, omitting financial assets like stocks and pensions. We've updated the prompt to fill gaps with general knowledge when the fragments of source material alone could give an incomplete or misleading picture.

## What's next

Phase 1 testing is complete. The issues you found are documented and the prompt has been rewritten. The bot is significantly better because of your efforts.

### Performance and resource estimation

The bots will keep running — testers are welcome to keep using them. We'll keep collecting usage and performance data, analyse what we gathered during Phase 1, and use it to estimate the resources we need for Phase 2.

### Improving the bot

- **Fix the bug: Answers too long for Discord and Telegram.** Find a permanent fix, like add message splitting before sending.
- **Add missing subtitles.** The current database only covers videos from early 2024 to November 2025. We need to add the rest.
- **Add other sources.** Gary's book, Cambridge talk, university thesis, interviews on other channels — we'll check with Gary's team first.
- **Improve time awareness and video links.** The bot doesn't handle dates well and video links in answers need work.
- **Add more external AI providers.** To improve scalability for Phase 2.
- **Test prompt and model combinations.** We've compiled test questions from Phase 1 feedback. We'll test different prompt versions against different models to find what works best.
- **Multi-turn conversations.** Currently the bot treats each message independently — it doesn't remember what you said earlier. This was one of the most requested features. We'll implement it, test it, and measure the extra cost (longer prompts mean more tokens). Then we'll check with Gary's team whether to enable it for Phase 2.

Thank you for your time, your creativity, and your determination to break things. It worked.
