from rag.rag_manager import RAG_query
from config import settings
from rag.video_links import get_video_link, videos_text_for_chat

print(settings.bot_greeting)
question = input("Your question: ")
response = RAG_query(question)
if settings.show_logs:
    print(response)
print(response["answer"])
video_links = get_video_link(response["context"])
video_text = videos_text_for_chat(video_links)
print(video_text)