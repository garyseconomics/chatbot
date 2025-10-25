import logging, os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from dotenv import load_dotenv

welcome_message = "This is the chatbot for Gary's Economics YouTube channel. You can ask me questions, and I will answer them using the content from our videos."

# Setting up the logging module
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Load the telegram bot token from the environment variable
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message)

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    
    application.run_polling()