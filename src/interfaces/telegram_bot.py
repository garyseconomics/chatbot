import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from config import settings
from interfaces.chunker import telegram_bot_chunker
from mcp_client.mcp_manager import MCP_query

logger = logging.getLogger(__name__)


# Start handler. Called when a user sends the /start command.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=settings.bot_greeting)


# Question funtion. This funtion will answer when a user sends a text message to the bot.
async def question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        question = update.message.text
        rag_answer = await MCP_query(question, client_type="telegram")
        answer = rag_answer["answer"]
        logger.debug("RAG answer: %s", rag_answer)
        for chunk in telegram_bot_chunker.chunk(answer):
            await context.bot.send_message(chat_id=update.effective_chat.id, text=chunk.text)

    except Exception:
        logger.exception("Failed to handle message")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=settings.error_messages["DefaultError"],
        )


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
