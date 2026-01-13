import os
from dotenv import load_dotenv
from rag.RAG_manager import RAG_query
from config import show_logs, bot_greeting
from video_links import get_video_link, videos_text_for_chat

load_dotenv()
LANGFUSE_APP_NAME = os.getenv("LANGFUSE_APP_NAME", "GarysEconomics_bot")

print(bot_greeting)
question = input("Your question: ")
response = RAG_query(question, user_id="console-user", app_name=LANGFUSE_APP_NAME)
if show_logs:
    print(response)
print(response["answer"])
video_links = get_video_link(response["context"])
video_text = videos_text_for_chat(video_links)
print(video_text)
