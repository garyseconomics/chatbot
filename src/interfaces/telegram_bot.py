import logging

from langchain_core.messages import HumanMessage
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from config import settings
from interfaces.chunker import telegram_bot_chunker
from mcp_client.mcp_manager import answer_question

logger = logging.getLogger(__name__)


# Start handler. Called when a user sends the /start command.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=settings.bot_greeting)


# Question funtion. This funtion will answer when a user sends a text message to the bot.
async def question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        question = update.message.text
        # chat_data is a dict that python-telegram-bot keeps for each chat (in memory only).
        conversation = context.chat_data.setdefault("conversation", [])
        knowledge = context.chat_data.setdefault("knowledge", {})
        conversation.append(HumanMessage(content=question))
        answer = await answer_question(conversation, knowledge, client_type="telegram")
        logger.debug("Answer: %s", answer)
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
