database_path = "./vector_database/chroma_langchain_db"
documents_directory = "docs/import"
collection_name = "youtube_videos"
chunk_size = 1024
chunk_overlap = 105
batch_size = 10
show_logs = True
discord_channel = "youtube-chatbot"
embedding_model = "qwen3-embedding:8b"
use_remote_llm = True
# AVAILABLE MODELS:
# Mistral: "dolphin-mistral:7b","mistral-small3.1:24b"
# Alibaba: "qwen3:4b","qwen3:8b","qwen3:14b","qwen3:30b","qwen3:32b"
# Meta: "llama3.1:8b","llama3.3:70b"
# Open AI: "gpt-oss:20b"
remote_llm = "qwen3:4b"
local_llm = "qwen3:4b"
video_ids_separator = "__"
bot_greeting = "Hello. This is Garys Economics Youtube chatbot. You can ask me questions and I'll answer them using the content of our videos."
