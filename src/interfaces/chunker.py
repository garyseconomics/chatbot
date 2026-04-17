from chonkie import SentenceChunker

TELEGRAM_CHUNK_LIMIT = 4096

telegram_bot_chunker = SentenceChunker(
    chunk_size=TELEGRAM_CHUNK_LIMIT,
    chunk_overlap=0,
)

