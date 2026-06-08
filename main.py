from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8884302613:AAHdNPfAk2P0l_hqvxRQ1-8F3K5jS9fiRzc"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Bot is working.")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))

import asyncio
async def main():
    await app.run_polling()

await main()
