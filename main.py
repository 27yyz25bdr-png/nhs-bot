import nest_asyncio
nest_asyncio.apply()

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

TOKEN = "8884302613:AAHdNPfAk2P0l_hqvxRQ1-8F3K5jS9fiRzc"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Bot is working!")

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    await app.run_polling()

# Use nest_asyncio instead of asyncio.run()
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
