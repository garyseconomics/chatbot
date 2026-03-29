# Data Sources

## Vector database content

The vector database currently contains subtitle transcripts from Gary's YouTube videos,
chunked and embedded for RAG retrieval.

### Source: garyseconomics/subtitle-data

Repository: https://github.com/garyseconomics/subtitle-data

Contains transcripts reviewed by a professional transcription agency, coordinated through
Oscar. The agency started this work around early 2024. These form the bulk of the
currently imported content, covering mostly early 2024 to November 2025 (45 transcripts).

### Volunteer-reviewed transcripts

A couple of volunteer-reviewed transcripts have also been imported (e.g., "How COVID-19
Makes the Rich Richer" 2020, "Avocado Toast" 2021), with more expected soon as the
review pipeline produces results.

### Import path

Reviewed transcripts are added to `content_database/docs/video_transcripts/` in this
repo, then imported into the vector database using the import scripts in
`content_database/scripts/`.

## Transcript review pipeline

GitHub issue: [#39](https://github.com/garyseconomics/chatbot/issues/39)

Repository: https://github.com/garyseconomics/transcripts
Review branch: https://github.com/Adavideo/transcripts/tree/AI_and_volunteer_review

Contains ~350 transcripts extracted from Gary's YouTube videos using the tools in the
repo. These go through a multi-stage review pipeline before they can be imported:

1. **Automated script cleanup** (`scripts/review_transcript.py`) — fixes known garbled
   words, applies British English spelling, capitalises proper nouns, removes fillers,
   deduplicates echo-cues.
2. **AI review** (Claude) — fixes context-dependent errors (e.g., garbled names),
   adds punctuation, identifies multiple speakers.
3. **Corrections document** (`scripts/generate_corrections_doc.py`) — generates a
   comparison doc showing all changes for volunteer review.
4. **Volunteer review** — volunteers watch the video while checking the corrections doc.
5. **Final merge** — volunteer corrections are incorporated into the final SRT.

Reviewed transcripts to be imported are placed in
`revisions/2_To_be_reviewed_by_volunteers/` on the review branch.

### Current status

- 45 agency-reviewed (stage 0)
- 2 volunteer-reviewed 
- 11 AI-reviewed, awaiting volunteer review
- ~294 not yet started

See `docs/missing_subtitles.txt` for the full list of 310 missing transcripts (261 full
videos + 49 shorts).

## Local transcripts

### content_database/docs/video_transcripts/already_imported/

Transcripts that have been reviewed and imported into the vector database.

### content_database/docs/video_transcripts/pending_review/

Transcripts that have **not** been reviewed yet but are kept for reference while
working on prompt issues. These help us understand what the bot *should* answer once the
full context is available. They are **not** imported into the vector database.

## Related tasks in TODO.md

- **Add more content to the vector database** — umbrella task for all missing content
- **Compile a list of topics covered by the channel** — using the transcripts repo
- **Bot lacks temporal awareness** ([#26](https://github.com/garyseconomics/chatbot/issues/26)) — adding publish dates and video links to chunks so the LLM can reason about recency
- **Include video links inline** ([#36](https://github.com/garyseconomics/chatbot/issues/36)) — each subtitle fragment in the prompt should carry its video link
- **Add informational documents** — documents about the bot, Gary, the channel, and data collection/privacy for the vector database

## Other potential sources (not yet started)

- **Cambridge talk** — Gary's talk about his life and economics. The original:
  https://www.youtube.com/watch?v=CFamoP5FEQA. Version on Gary's channel:
  https://www.youtube.com/watch?v=0jwCLwi_N70. Added to `pending_review/` as
  `How_to_live_in_a_collapsing_economy.srt`. Needs review before import.
- **Gary's book** (*The Trading Game*) — a dramatisation with changed names but based on
  a true story. Contains useful info about how the system works and about Gary's voice.
  Needs careful indexing — it's a narrative, not a transcript.
- **Interviews on other channels** — need permission before importing.
- **Gary's master thesis** (https://www.wealtheconomics.org/unithesis/) — needs cleanup
  before import: only include the parts written in plain English, not the
  mathematical/jargon sections.
- **Works by economists Gary recommends** — Gary cites and recommends these economists
  in his videos. The actual books/papers are third-party content. See Phase 2 Plan
  section 4.4 for import considerations.
  - [Gabriel Zucman](https://gabriel-zucman.eu/) — research on wealth inequality, tax havens
  - [Thomas Piketty](http://piketty.pse.ens.fr/en/) — research on capital and inequality
  - Ha-Joon Chang — development economics, critique of free trade orthodoxy

## Impact on bot quality

The bot can only use content that's in the vector database. Missing transcripts directly
cause issues:

- **Crypto stance** — Gary is strongly critical of crypto ("a trap, not a way out") but
  this is in pre-2024 videos not yet imported. The bot currently gives generic answers.
  Key video: ["Crypto = Internet Points? Why it Won't Make You Rich"](https://www.youtube.com/watch?v=Llrs7herILg)
  (2022-02-27). Added to `pending_review/` for reference.
- **Tour and book information** — Gary has been on tour (UK, Italy, Australia/NZ planned
  for Feb/March) and the paperback launched end of January 2025. This is in recent videos
  not yet imported (e.g., "Goodbye and Good Luck", added to `pending_review/`). The bot
  currently fabricates dates when asked about the book or tours.
- **Older topics** — Gary covered many topics in pre-2024 videos that aren't available to
  the bot, leading to unnecessary refusals or generic answers on topics the channel has
  actually addressed. A task to compile a list of topics covered by the channel is tracked
  in TODO.md, using the [transcripts repo](https://github.com/garyseconomics/transcripts)
  as source.
