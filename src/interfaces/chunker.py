from chonkie import SentenceChunker
from config import settings

telegram_bot_chunker = SentenceChunker(
    chunk_size=settings.telegram_message_limit,
    chunk_overlap=0,
)

