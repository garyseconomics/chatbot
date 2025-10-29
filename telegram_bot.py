import logging, os
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from rag.RAG_manager import RAG_query
from config import show_logs
from video_links import get_video_link

welcome_message = "This is the chatbot for Gary's Economics YouTube channel. You can ask me questions, and I will answer them using the content from our videos."

# Setting up the logging module
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Load the telegram bot token from the environment variable
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Start funtion. This function will be called every time the Bot receives a Telegram message that contains the /start command.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message)

# Question funtion. This funtion will answer when a user sends a text message to the bot.
async def question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    rag_answer = RAG_query(question)
    answer = rag_answer["answer"]
    video_link = get_video_link(rag_answer["context"])
    if video_link:
        answer = f"{answer}\nMore information on this video: {video_link}"
    if show_logs:
        print(rag_answer)
        print(f"Video link: {video_link}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)

if __name__ == '__main__':
    # Start the application, using the telegram token to connect to the bot
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Calls the start handler that listen for telegram users starting a new conversation with the bot
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    # Calls the update handler that listen for telegram users sending a text message on an already open chat
    question_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), question)
    application.add_handler(question_handler)

    # Keeps the bot alive and listening
    application.run_polling()
