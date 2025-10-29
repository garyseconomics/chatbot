from rag.RAG_manager import RAG_query
from config import show_logs
from video_links import get_video_link

print("This is the chatbot for Gary's Economics YouTube channel. You can ask me questions, and I will answer them using the content from our videos.")
question = input("Your question: ")
response = RAG_query(question)
if show_logs:
    print(response)
print(response["answer"])
video_link = get_video_link(response["context"])
if video_link:
    print(f"More information on this video: {video_link}")