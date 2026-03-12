# Testing Plan

We are rolling out the Gary's Economics chatbot in phases, gradually increasing the
number of users while we improve the bot and scale the infrastructure.

## Phases

| Phase | Users | Focus |
|-------|-------|-------|
| **Phase 0** (done) | ~5 volunteers | Build the prototype, fix core bugs |
| **Phase 1** (current) | 100 volunteers | Answer quality, resource estimation |
| **Phase 2** | ~3,000 Patreons | Stability and cost validation |
| **Phase 3** | 1M+ YouTube subscribers | Full public release |

## Phase 1 — What we are testing

### Answer quality

We need to make sure the bot behaves correctly, even with tricky questions. Examples of
issues we have already found and are working on:

- The bot impersonating Gary instead of clarifying it is a chatbot
- The bot giving overly neutral answers on topics where the channel has a clear position

If you find the bot giving a bad answer, please report it in the **#github channel** on
Discord or the **testing Telegram group**, including:

- The question you asked
- What was wrong with the response

Volunteers with access to the GitHub repo review these reports and create issues.

### Performance and resource estimation

We are measuring how the system performs with multiple users at the same time. This helps
us plan the infrastructure we will need for Phase 2 and Phase 3.

If the system struggles under load, we may organize group testing sessions at specific
times. We will coordinate this in the Discord and Telegram channels.

## Privacy notice

All questions and answers are recorded and may be used to improve the chatbot. During this
testing phase, some requests may be processed by external AI services that use data for
their own model training. Please do not include any personal or sensitive information in
your questions.

## Contributing

This is an open-source project licensed under GPLv3. If you want to contribute beyond
testing, check out the [GitHub repository](https://github.com/garyseconomics/chatbot).
