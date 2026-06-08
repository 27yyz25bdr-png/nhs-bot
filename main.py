import pandas as pd
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TELEGRAM_BOT_TOKEN = "8884302613:AAF4cVrPihPiaM9yDdUw2uMW88s2S0AQR5k"
ADMIN_CHAT_ID = "5546896254"
KING_PASS = ["5546896254"]

USERS = {}

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("FREE BOT", callback_data="free")],
        [InlineKeyboardButton("PREMIUM BOT", callback_data="premium")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = str(update.message.chat_id)
    if cid not in USERS:
        USERS[cid] = {"status": "active" if cid in KING_PASS else "free"}
    await update.message.reply_text("NHS BOT. Choose:", reply_markup=main_menu())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cid = str(query.message.chat_id)
    data = query.data
    
    if data == "free":
        await query.message.reply_text("FREE MODE. Browse jobs 12+ hours old.")
        return
    
    if data == "premium":
        if USERS.get(cid, {}).get("status") == "active":
            await query.message.reply_text("PREMIUM MODE. All jobs unlocked!")
        else:
            await query.message.reply_text("Upgrade to Premium $10/month. Pay to Binance ID: 1251705066")
        return

async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    await app.run_polling()

await main()
