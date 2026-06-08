import pandas as pd
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==================== CONFIG ====================
TELEGRAM_BOT_TOKEN = "8884302613:AAF4cVrPihPiaM9yDdUw2uMW88s2S0AQR5k"  # REPLACE!
ADMIN_CHAT_ID = "5546896254"
BINANCE_ID = "1251705066"
KING_PASS = ["5546896254"]

# Data stores
USERS = {}
CACHE = {}
PENDING = {}

# ==================== SIMPLE MENUS ====================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("FREE BOT", callback_data="free")],
        [InlineKeyboardButton("PREMIUM BOT", callback_data="premium")]
    ])

def free_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Search Jobs", callback_data="search")],
        [InlineKeyboardButton("Upgrade Premium", callback_data="pay")]
    ])

def premium_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Search Jobs", callback_data="search")],
        [InlineKeyboardButton("Todays Jobs", callback_data="today")]
    ])

def role_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("JCF", callback_data="role_JCF"),
         InlineKeyboardButton("SCF", callback_data="role_SCF")],
        [InlineKeyboardButton("Teaching", callback_data="role_Teaching"),
         InlineKeyboardButton("TrustGrade", callback_data="role_TrustGrade")],
        [InlineKeyboardButton("LAS", callback_data="role_LAS"),
         InlineKeyboardButton("Locum", callback_data="role_Locum")],
        [InlineKeyboardButton("FY1", callback_data="role_FY1"),
         InlineKeyboardButton("FY2", callback_data="role_FY2")],
        [InlineKeyboardButton("CT", callback_data="role_CT"),
         InlineKeyboardButton("ST1-ST2", callback_data="role_ST_Junior")],
        [InlineKeyboardButton("ST3-ST8", callback_data="role_ST_Senior"),
         InlineKeyboardButton("SAS", callback_data="role_SAS")],
        [InlineKeyboardButton("Specialist", callback_data="role_Specialist"),
         InlineKeyboardButton("GP", callback_data="role_GP")],
        [InlineKeyboardButton("Dental", callback_data="role_Dental")],
        [InlineKeyboardButton("BACK", callback_data="back")]
    ])

def pay_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("I have paid 10 USDT", callback_data="paid")],
        [InlineKeyboardButton("BACK", callback_data="back")]
    ])

# ==================== START ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = str(update.message.chat_id)
    
    if cid not in USERS:
        is_king = cid in KING_PASS
        USERS[cid] = {
            "status": "active" if is_king else "free",
            "mode": "free",
            "role": None
        }
    
    if cid in KING_PASS:
        USERS[cid]["status"] = "active"
    
    await update.message.reply_text("NHS JOBS BOT. Choose:", reply_markup=main_menu())

# ==================== BUTTON HANDLER ====================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cid = str(query.message.chat_id)
    data = query.data
    
    # Init user
    if cid not in USERS:
        USERS[cid] = {"status": "free", "mode": "free", "role": None}
    
    # Load database
    try:
        df = pd.read_csv("traced_nhs_jobs.csv")
    except:
        await query.message.reply_text("Database error. Please check setup.")
        return
    
    # MAIN NAVIGATION
    if data == "free":
        USERS[cid]["mode"] = "free"
        await query.message.reply_text("FREE MODE. Search jobs posted 12+ hours ago.", reply_markup=free_menu())
        return
    
    if data == "premium":
        if USERS[cid]["status"] == "active":
            USERS[cid]["mode"] = "premium"
            await query.message.reply_text("PREMIUM MODE. All jobs unlocked!", reply_markup=premium_menu())
        else:
            await query.message.reply_text("Upgrade to Premium for $10/month.", reply_markup=pay_menu())
        return
    
    if data == "back":
        await query.message.reply_text("Main Menu:", reply_markup=main_menu())
        return
    
    # SEARCH
    if data == "search":
        await query.message.reply_text("Select Role:", reply_markup=role_menu())
        return
    
    if data == "today":
        if USERS[cid]["status"] != "active":
            await query.message.reply_text("Premium only!", reply_markup=pay_menu())
            return
        
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        todays = []
        for _, row in df.iterrows():
            job_time = datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S')
            if job_time >= today_start:
                todays.append(row.to_dict())
        
        if not todays:
            await query.message.reply_text("No jobs posted today.", reply_markup=premium_menu())
            return
        
        text = "TODAYS JOBS: " + str(len(todays)) + "\n\n"
        for job in todays[:5]:
            text += job['Role'] + " at " + job['Employer'] + "\n"
            text += "Search: " + job['Link'] + "\n\n"
        
        await query.message.reply_text(text, reply_markup=premium_menu())
        return
    
    # ROLE SELECTION
    if data.startswith("role_"):
        role = data.replace("role_", "")
        USERS[cid]["role"] = role
        
        jobs = []
        for _, row in df.iterrows():
            if row['Role'] == role:
                jobs.append(row.to_dict())
        
        if not jobs:
            await query.message.reply_text("No jobs found for this role.", reply_markup=role_menu())
            return
        
        CACHE[cid] = {role: jobs}
        
        # Show first 5 jobs
        text = role + " JOBS: " + str(len(jobs)) + "\n\n"
        
        for i, job in enumerate(jobs[:5]):
            job_time = datetime.strptime(job['Timestamp'], '%Y-%m-%d %H:%M:%S')
            age_hours = (datetime.now() - job_time).total_seconds() / 3600
            
            if USERS[cid]["mode"] == "free" and age_hours < 12:
                text += str(i+1) + ". LOCKED (Premium Only)\n"
                text += "   Employer: " + job['Employer'] + "\n"
                text += "   Posted: " + str(int(age_hours * 60)) + " minutes ago\n\n"
            else:
                text += str(i+1) + ". " + job['Job Title'] + "\n"
                text += "   Employer: " + job['Employer'] + "\n"
                text += "   Salary: " + job['Salary'] + "\n"
                text += "   Visa: " + job['Visa'] + "\n"
                text += "   Region: " + job['Region'] + "\n\n"
                text += "   ESSENTIAL: " + job['Essential_Criteria'] + "\n"
                text += "   DESIRABLE: " + job['Desirable_Criteria'] + "\n\n"
                text += "   SEARCH ON NHS JOBS: " + job['Link'] + "\n\n"
        
        if len(jobs) > 5:
            text += "... and " + str(len(jobs) - 5) + " more jobs\n"
        
        await query.message.reply_text(text, reply_markup=role_menu())
        return
    
    # PAYMENT
    if data == "pay":
        await query.message.reply_text("Pay 10 USDT to Binance ID: " + BINANCE_ID + "\nThen click 'I have paid'", reply_markup=pay_menu())
        return
    
    if data == "paid":
        PENDING[cid] = {"status": "pending"}
        
        try:
            await context.bot.send_message(
                chat_id=int(ADMIN_CHAT_ID),
                text="NEW PAYMENT from user: " + cid + "\nApprove?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("APPROVE", callback_data="approve_" + cid)],
                    [InlineKeyboardButton("REJECT", callback_data="reject_" + cid)]
                ])
            )
        except:
            pass
        
        await query.message.reply_text("Payment submitted. Waiting for approval.")
        return
    
    # ADMIN APPROVAL
    if data.startswith("approve_"):
        target = data.replace("approve_", "")
        USERS[target]["status"] = "active"
        
        try:
            await context.bot.send_message(chat_id=int(target), text="APPROVED! You are now PREMIUM.", reply_markup=main_menu())
        except:
            pass
        
        await query.message.reply_text("User approved.")
        return
    
    if data.startswith("reject_"):
        target = data.replace("reject_", "")
        
        try:
            await context.bot.send_message(chat_id=int(target), text="Rejected. Please try again.")
        except:
            pass
        
        await query.message.reply_text("User rejected.")
        return


# ==================== MAIN ====================
async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    print("BOT RUNNING!")
    
    while True:
        await asyncio.sleep(3600)

await main()
