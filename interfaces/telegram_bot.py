import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from config import settings
from rag.rag_manager import RAG_query
from rag.video_links import get_video_link, videos_text_for_chat

logger = logging.getLogger(__name__)


# Start handler. Called when a user sends the /start command.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=settings.bot_greeting)


# Question funtion. This funtion will answer when a user sends a text message to the bot.
async def question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question = update.message.text
    user_id = f"telegram:{update.effective_user.id}"
    rag_answer = RAG_query(question, user_id=user_id)
    answer = rag_answer["answer"]
    video_links = get_video_link(rag_answer["context"])
    if video_links:
        video_text = videos_text_for_chat(video_links)
        answer = f"{answer}\n\n{video_text}"
    logger.debug("RAG answer: %s", rag_answer)
    logger.debug("Video links: %s", video_links)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)


if __name__ == "__main__":
    # Start the application, using the telegram token to connect to the bot
    application = ApplicationBuilder().token(settings.telegram_token).build()

    # Handler for new conversations (user sends /start)
    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)

    # Handler for text messages in an open chat
    question_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), question)
    application.add_handler(question_handler)

    # Keeps the bot alive and listening
    application.run_polling()
