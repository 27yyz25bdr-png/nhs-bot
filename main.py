import nest_asyncio
nest_asyncio.apply()

import pandas as pd
import asyncio
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==================== CONFIG ====================
TELEGRAM_BOT_TOKEN = "8884302613:AAHdNPfAk2P0l_hqvxRQ1-8F3K5jS9fiRzc"
ADMIN_CHAT_ID = "5546896254"
BINANCE_ID = "1251705066"
KING_PASS = ["5546896254"]

# Data stores
USERS = {}
CACHE = {}
PENDING = {}
AD_REVENUE = {}

# Ad settings
AD_INTERVAL = 3
AD_EARNINGS_PER_VIEW = 0.50

# ==================== UI MENUS ====================
def get_main_screen():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🆓 NORMAL BOT (FREE)", callback_data="enter_normal")],
        [InlineKeyboardButton("👑 PREMIUM BOT ($10/mo)", callback_data="enter_premium")]
    ])

def get_normal_dashboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 SEARCH JOBS BY ROLE", callback_data="normal_search_roles")],
        [InlineKeyboardButton("👑 UPGRADE TO PREMIUM", callback_data="unlock_premium")]
    ])

def get_premium_dashboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 SEARCH JOBS BY ROLE", callback_data="premium_search_roles")],
        [InlineKeyboardButton("📅 TODAY'S JOBS", callback_data="premium_todays_vault")]
    ])

def get_role_menu(mode):
    prefix = "N_" if mode == "normal" else "P_"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎓 JCF", callback_data=f"{prefix}JCF"),
         InlineKeyboardButton("🎓 SCF", callback_data=f"{prefix}SCF")],
        [InlineKeyboardButton("🏫 Teaching", callback_data=f"{prefix}Teaching"),
         InlineKeyboardButton("🏥 Trust Grade", callback_data=f"{prefix}TrustGrade")],
        [InlineKeyboardButton("🚨 LAS", callback_data=f"{prefix}LAS"),
         InlineKeyboardButton("💼 Locum", callback_data=f"{prefix}Locum")],
        [InlineKeyboardButton("🩻 FY1", callback_data=f"{prefix}FY1"),
         InlineKeyboardButton("🩻 FY2", callback_data=f"{prefix}FY2")],
        [InlineKeyboardButton("🧬 CT", callback_data=f"{prefix}CT"),
         InlineKeyboardButton("🧬 ST1-ST2", callback_data=f"{prefix}ST_Junior")],
        [InlineKeyboardButton("🧬 ST3-ST8", callback_data=f"{prefix}ST_Senior"),
         InlineKeyboardButton("👑 SAS", callback_data=f"{prefix}SAS")],
        [InlineKeyboardButton("👑 Specialist", callback_data=f"{prefix}Specialist"),
         InlineKeyboardButton("🩺 GP", callback_data=f"{prefix}GP")],
        [InlineKeyboardButton("🦷 Dental", callback_data=f"{prefix}Dental")],
        [InlineKeyboardButton("🔙 BACK", callback_data=f"back_{mode}")]
    ])

def get_ad_screen():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 AD BREAK", callback_data="noop")],
        [InlineKeyboardButton("🚀 UK Visa Services", url="https://google.com")],
        [InlineKeyboardButton("✅ CONTINUE", callback_data="ad_dismiss")]
    ])

def get_payment_screen():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧾 PAY $10 VIA BINANCE", callback_data="pay_submit")],
        [InlineKeyboardButton("↩️ CANCEL", callback_data="back_main")]
    ])

# ==================== START ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = str(update.message.chat_id)
    
    if cid not in USERS:
        is_king = cid in KING_PASS
        USERS[cid] = {
            "status": "active" if is_king else "free",
            "mode": "free",
            "role": None,
            "queries": 0,
            "jobs_viewed": 0,
            "ad_views": 0
        }
    
    if cid in KING_PASS:
        USERS[cid]["status"] = "active"
    
    await update.message.reply_text(
        "🏥 *NHS UK MEDICAL & DENTAL JOBS BOT* 🇬🇧\n\n"
        "Choose your access level:\n\n"
        "🆓 *NORMAL BOT — FREE*\n"
        "• Browse jobs posted 12+ hours ago\n"
        "• Full Person Specifications\n"
        "• 2 searches per session\n\n"
        "👑 *PREMIUM BOT — $10/month*\n"
        "• ALL jobs including today's fresh postings\n"
        "• Real-time alerts\n"
        "• AI Comparison\n"
        "• NO ADS\n\n"
        "👇 *Select below:*",
        parse_mode="Markdown",
        reply_markup=get_main_screen()
    )

# ==================== BUTTON HANDLER ====================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cid = str(query.message.chat_id)
    data = query.data
    
    if cid not in USERS:
        USERS[cid] = {"status": "free", "mode": "free", "role": None, "queries": 0, "jobs_viewed": 0, "ad_views": 0}
    
    try:
        df = pd.read_csv("traced_nhs_jobs.csv")
    except:
        await query.message.reply_text("⚠️ Database error. Please check setup.")
        return
    
    # MAIN NAVIGATION
    if data == "enter_normal":
        USERS[cid]["mode"] = "normal"
        await query.message.reply_text(
            "🆓 *NORMAL BOT ACTIVATED*\n\n"
            "Browse jobs posted 12+ hours ago.\n"
            "Fresh jobs are locked for Premium.",
            parse_mode="Markdown",
            reply_markup=get_normal_dashboard()
        )
        return
    
    if data == "enter_premium":
        if USERS[cid]["status"] == "active":
            USERS[cid]["mode"] = "premium"
            await query.message.reply_text(
                "👑 *PREMIUM BOT ACTIVATED*\n\n"
                "All jobs unlocked! No ads!",
                parse_mode="Markdown",
                reply_markup=get_premium_dashboard()
            )
        else:
            await query.message.reply_text(
                "🔒 *UPGRADE TO PREMIUM*\n\n"
                "$10/month via Binance ID: `1251705066`",
                parse_mode="Markdown",
                reply_markup=get_payment_screen()
            )
        return
    
    if data == "back_main":
        await query.message.reply_text("🏥 *MAIN MENU*", parse_mode="Markdown", reply_markup=get_main_screen())
        return
    
    if data == "back_normal":
        USERS[cid]["mode"] = "normal"
        await query.message.reply_text("🆓 *NORMAL BOT*", parse_mode="Markdown", reply_markup=get_normal_dashboard())
        return
    
    if data == "back_premium":
        USERS[cid]["mode"] = "premium"
        await query.message.reply_text("👑 *PREMIUM BOT*", parse_mode="Markdown", reply_markup=get_premium_dashboard())
        return
    
    # SEARCH ROLES
    if data == "normal_search_roles":
        await query.message.reply_text("🆓 *SELECT A ROLE:*", parse_mode="Markdown", reply_markup=get_role_menu("normal"))
        return
    
    if data == "premium_search_roles":
        if USERS[cid]["status"] != "active":
            await query.message.reply_text("🔒 *PREMIUM ONLY*", parse_mode="Markdown", reply_markup=get_payment_screen())
            return
        await query.message.reply_text("👑 *SELECT A ROLE:*", parse_mode="Markdown", reply_markup=get_role_menu("premium"))
        return
    
    # ROLE SELECTION
    if data.startswith("N_"):
        role = data.replace("N_", "")
        USERS[cid]["role"] = role
        USERS[cid]["queries"] += 1
        
        if USERS[cid]["queries"] > 2 and cid not in KING_PASS:
            await query.message.reply_text(
                "⏳ *LIMIT REACHED*\n\nWatch ad to continue.",
                parse_mode="Markdown",
                reply_markup=get_ad_screen()
            )
            return
        
        jobs = [row.to_dict() for _, row in df.iterrows() if row['Role'] == role]
        CACHE[cid] = {role: jobs}
        
        await show_job_list(query, jobs, role, "normal", cid)
        return
    
    if data.startswith("P_"):
        role = data.replace("P_", "")
        USERS[cid]["role"] = role
        
        if USERS[cid]["status"] != "active":
            await query.message.reply_text("🔒 *PREMIUM ONLY*", parse_mode="Markdown", reply_markup=get_payment_screen())
            return
        
        jobs = [row.to_dict() for _, row in df.iterrows() if row['Role'] == role]
        CACHE[cid] = {role: jobs}
        
        await show_job_list(query, jobs, role, "premium", cid)
        return
    
    # VIEW JOB
    if data.startswith("VIEW_"):
        parts = data.split("_")
        mode = parts[1]
        role = parts[2]
        idx = int(parts[3])
        
        jobs = CACHE.get(cid, {}).get(role, [])
        if not jobs or idx >= len(jobs):
            return
        
        # AD CHECK
        if mode == "normal" and cid not in KING_PASS:
            USERS[cid]["jobs_viewed"] += 1
            if USERS[cid]["jobs_viewed"] % AD_INTERVAL == 0:
                CACHE.setdefault(cid, {})["pending_job"] = {"mode": mode, "role": role, "idx": idx}
                await query.message.reply_text("📺 *AD BREAK*", parse_mode="Markdown", reply_markup=get_ad_screen())
                return
        
        await show_job_detail(query, jobs, idx, role, mode, cid)
        return
    
    # AD DISMISS
    if data == "ad_dismiss":
        USERS[cid]["queries"] = 0
        today = date.today().strftime('%Y-%m-%d')
        AD_REVENUE.setdefault(today, {"views": 0, "earnings": 0.0})
        AD_REVENUE[today]["views"] += 1
        AD_REVENUE[today]["earnings"] += AD_EARNINGS_PER_VIEW
        
        pending = CACHE.get(cid, {}).get("pending_job")
        if pending:
            CACHE[cid]["pending_job"] = None
            jobs = CACHE.get(cid, {}).get(pending["role"], [])
            if jobs and pending["idx"] < len(jobs):
                await show_job_detail(query, jobs, pending["idx"], pending["role"], pending["mode"], cid)
                return
        
        await query.message.reply_text("✅ *CONTINUE*", parse_mode="Markdown", reply_markup=get_normal_dashboard())
        return
    
    # COPY SEARCH TERM
    if data.startswith("COPY_"):
        parts = data.split("_")
        mode = parts[1]
        role = parts[2]
        idx = int(parts[3])
        
        jobs = CACHE.get(cid, {}).get(role, [])
        if not jobs or idx >= len(jobs):
            return
        
        job = jobs[idx]
        await query.message.reply_text(
            f"📋 *COPY THIS SEARCH TERM:*\n\n"
            f"`{job['Link']}`\n\n"
            f"✅ Go to www.jobs.nhs.uk and paste this in the search box!",
            parse_mode="Markdown"
        )
        return
    
    # TODAY'S JOBS
    if data == "premium_todays_vault":
        if USERS[cid]["status"] != "active":
            await query.message.reply_text("🔒 *PREMIUM ONLY*", parse_mode="Markdown", reply_markup=get_payment_screen())
            return
        
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        todays = []
        for _, row in df.iterrows():
            job_time = datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S')
            if job_time >= today_start:
                todays.append(row.to_dict())
        
        if not todays:
            await query.message.reply_text("📅 *NO JOBS TODAY*", parse_mode="Markdown", reply_markup=get_premium_dashboard())
            return
        
        CACHE[cid] = {"todays": todays}
        
        text = f"📅 *TODAY'S JOBS: {len(todays)}*\n\n"
        for i, job in enumerate(todays[:5]):
            mins = int((now - datetime.strptime(job['Timestamp'], '%Y-%m-%d %H:%M:%S')).total_seconds() / 60)
            text += f"{i+1}. {job['Role']} at {job['Employer']}\n"
            text += f"   Search: `{job['Link']}`\n"
            text += f"   Posted: {mins} minutes ago\n\n"
        
        if len(todays) > 5:
            text += f"... and {len(todays) - 5} more!\n"
        
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=get_premium_dashboard())
        return
    
    # PAYMENT
    if data == "unlock_premium":
        if cid in PENDING and PENDING[cid]["status"] == "pending":
            await query.message.reply_text("⏳ *PENDING*", parse_mode="Markdown")
            return
        await query.message.reply_text("💰 *PAY $10*", parse_mode="Markdown", reply_markup=get_payment_screen())
        return
    
    if data == "pay_submit":
        PENDING[cid] = {"time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "status": "pending"}
        
        try:
            await context.bot.send_message(
                chat_id=int(ADMIN_CHAT_ID),
                text=f"🚨 NEW PAYMENT from {cid}\nApprove?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{cid}")],
                    [InlineKeyboardButton("❌ REJECT", callback_data=f"reject_{cid}")]
                ])
            )
        except:
            pass
        
        await query.message.reply_text("⏳ *SUBMITTED. WAIT FOR APPROVAL.*", parse_mode="Markdown")
        return
    
    # ADMIN
    if data.startswith("approve_"):
        target = data.replace("approve_", "")
        USERS[target]["status"] = "active"
        
        try:
            await context.bot.send_message(chat_id=int(target), text="🎉 APPROVED! PREMIUM ACTIVE.", reply_markup=get_main_screen())
        except:
            pass
        
        await query.message.reply_text(f"✅ APPROVED {target}")
        return
    
    if data.startswith("reject_"):
        target = data.replace("reject_", "")
        
        try:
            await context.bot.send_message(chat_id=int(target), text="❌ REJECTED.")
        except:
            pass
        
        await query.message.reply_text(f"❌ REJECTED {target}")
        return


# ==================== SHOW JOB LIST ====================
async def show_job_list(query, jobs, role, mode, cid):
    now = datetime.now()
    text = f"{'🆓' if mode == 'normal' else '👑'} *{role} — {len(jobs)} JOBS*\n\n"
    
    for i, job in enumerate(jobs[:5]):
        job_time = datetime.strptime(job['Timestamp'], '%Y-%m-%d %H:%M:%S')
        age_hours = (now - job_time).total_seconds() / 3600
        
        if mode == "normal" and age_hours < 12:
            mins = int(age_hours * 60)
            text += f"{i+1}. 🔒 *LOCKED (PREMIUM ONLY)*\n"
            text += f"   Employer: {job['Employer']}\n"
            text += f"   Posted: {mins} minutes ago 🔥\n\n"
        else:
            text += f"{i+1}. ✅ {job['Job Title']}\n"
            text += f"   Employer: {job['Employer']}\n"
            text += f"   Salary: {job['Salary']}\n"
            text += f"   Region: {job['Region']}\n\n"
    
    if len(jobs) > 5:
        text += f"... and {len(jobs) - 5} more jobs\n"
    
    text += "\n👇 *Click any number to view details:*"
    
    buttons = []
    for i in range(min(5, len(jobs))):
        buttons.append([InlineKeyboardButton(str(i+1), callback_data=f"VIEW_{mode}_{role}_{i}")])
    
    buttons.append([InlineKeyboardButton("🔙 BACK", callback_data=f"back_{mode}")])
    
    await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))


# ==================== SHOW JOB DETAIL ====================
async def show_job_detail(query, jobs, idx, role, mode, cid):
    job = jobs[idx]
    now = datetime.now()
    job_time = datetime.strptime(job['Timestamp'], '%Y-%m-%d %H:%M:%S')
    age_hours = (now - job_time).total_seconds() / 3600
    is_premium = USERS[cid]["status"] == "active"
    
    if age_hours < 1:
        age_text = f"{int(age_hours * 60)} minutes ago 🔥"
    elif age_hours < 24:
        age_text = f"{int(age_hours)} hours ago"
    else:
        age_text = f"{int(age_hours / 24)} days ago"
    
    badge = "👑 " if is_premium else ""
    
    text = f"{badge}📌 *Job {idx+1} of {len(jobs)}*\n\n"
    text += f"*{job['Job Title']}*\n"
    text += f"🏥 {job['Employer']}\n"
    text += f"💰 {job['Salary']}\n"
    text += f"🛂 {job['Visa']}\n"
    text += f"📍 {job['Region']}\n"
    text += f"⏰ {age_text}\n\n"
    
    text += f"📋 *PERSON SPECIFICATION*\n\n"
    text += f"🔴 *ESSENTIAL (Must Have):*\n"
    for i, c in enumerate(job['Essential_Criteria'].split(", "), 1):
        text += f"   {i}. {c.strip()}\n"
    text += f"\n"
    text += f"🔵 *DESIRABLE (Nice to Have):*\n"
    for i, c in enumerate(job['Desirable_Criteria'].split(", "), 1):
        text += f"   {i}. {c.strip()}\n"
    text += f"\n"
    
    text += f"✅ *HOW TO APPLY FOR REAL NHS JOBS:*\n"
    text += f"1️⃣ Go to: www.jobs.nhs.uk\n"
    text += f"2️⃣ Search: `{job['Link']}`\n"
    text += f"3️⃣ Filter by: {job['Region']}\n"
    text += f"4️⃣ Upload CV + GMC certificate\n"
    text += f"5️⃣ Apply before deadline!\n\n"
    
    text += f"📋 *COPY THIS SEARCH TERM:*\n`{job['Link']}`"
    
    if is_premium:
        text += f"\n\n✨ *PREMIUM ACTIVE*"
    
    buttons = []
    if idx > 0:
        buttons.append(InlineKeyboardButton("⬅️", callback_data=f"VIEW_{mode}_{role}_{idx-1}"))
    buttons.append(InlineKeyboardButton(f"{idx+1}/{len(jobs)}", callback_data="noop"))
    if idx < len(jobs) - 1:
        buttons.append(InlineKeyboardButton("➡️", callback_data=f"VIEW_{mode}_{role}_{idx+1}"))
    
    nav_row = buttons
    action_row = [InlineKeyboardButton("📋 COPY SEARCH TERM", callback_data=f"COPY_{mode}_{role}_{idx}")]
    back_row = [InlineKeyboardButton("🔙 BACK", callback_data=f"back_{mode}")]
    
    await query.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([nav_row, action_row, back_row])
    )


# ==================== MAIN ====================
async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    
    await app.run_polling()

# Use nest_asyncio to fix event loop
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
