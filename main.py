import pandas as pd
import asyncio
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==================== CONFIG ====================
TELEGRAM_BOT_TOKEN = "8884302613:AAF4cVrPihPiaM9yDdUw2uMW88s2S0AQR5k"  # REPLACE WITH YOUR REAL TOKEN!
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
        [InlineKeyboardButton("🔍 SEARCH BY ROLE", callback_data="normal_search_roles")],
        [InlineKeyboardButton("👑 UPGRADE TO PREMIUM", callback_data="unlock_premium")]
    ])

def get_premium_dashboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 SEARCH BY ROLE", callback_data="premium_search_roles")],
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

def get_job_swarm(jobs, role, mode, page=0, per_page=5):
    buttons = []
    now = datetime.now()
    start = page * per_page
    end = min(start + per_page, len(jobs))
    
    for i in range(start, end):
        job = jobs[i]
        t = datetime.strptime(job['Timestamp'], '%Y-%m-%d %H:%M:%S')
        age_hours = (now - t).total_seconds() / 3600
        
        if mode == "normal" and age_hours < 12:
            label = f"🔒 {job['Employer'][:20]}..."
            cb = f"LOCK_{role}_{i}"
        else:
            label = f"✅ {job['Employer'][:25]}..."
            cb = f"VIEW_{mode}_{role}_{i}"
        
        buttons.append([InlineKeyboardButton(label, callback_data=cb)])
    
    if end < len(jobs):
        buttons.append([InlineKeyboardButton(f"📥 MORE ({len(jobs)-end})", callback_data=f"PAGE_{mode}_{role}_{page+1}")])
    
    buttons.append([InlineKeyboardButton("🔙 BACK", callback_data=f"{mode}_search_roles")])
    return InlineKeyboardMarkup(buttons)

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
        USERS[cid] = {
            "status": "active" if cid in KING_PASS else "free",
            "mode": None, "role": None, "queries": 0,
            "notified": [], "banned": False,
            "jobs_viewed": 0, "ad_views": 0
        }
    
    if USERS[cid].get("banned"):
        await update.message.reply_text("❌ BANNED")
        return
    
    if cid in KING_PASS:
        USERS[cid]["status"] = "active"
    
    await update.message.reply_text(
        "🏥 NHS JOBS BOT\n\nChoose:",
        reply_markup=get_main_screen()
    )

# ==================== BUTTON HANDLER ====================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cid = str(query.message.chat_id)
    data = query.data
    
    if cid not in USERS:
        USERS[cid] = {"status": "free", "mode": None, "role": None, "queries": 0, "notified": [], "banned": False, "jobs_viewed": 0, "ad_views": 0}
    
    try:
        df = pd.read_csv("traced_nhs_jobs.csv")
    except:
        await query.message.reply_text("⚠️ Database error. Run Cell 2 first.")
        return
    
    # MAIN NAVIGATION
    if data == "enter_normal":
        USERS[cid]["mode"] = "normal"
        await query.message.reply_text("🆓 NORMAL MODE", reply_markup=get_normal_dashboard())
        return
    
    if data == "enter_premium":
        if USERS[cid]["status"] == "active":
            USERS[cid]["mode"] = "premium"
            await query.message.reply_text("👑 PREMIUM MODE", reply_markup=get_premium_dashboard())
        else:
            await query.message.reply_text("🔒 UPGRADE NEEDED", reply_markup=get_payment_screen())
        return
    
    if data == "back_main":
        await query.message.reply_text("🏥 MAIN MENU", reply_markup=get_main_screen())
        return
    
    if data == "back_normal":
        USERS[cid]["mode"] = "normal"
        await query.message.reply_text("🆓 NORMAL", reply_markup=get_normal_dashboard())
        return
    
    if data == "back_premium":
        USERS[cid]["mode"] = "premium"
        await query.message.reply_text("👑 PREMIUM", reply_markup=get_premium_dashboard())
        return
    
    # SEARCH ROLES
    if data == "normal_search_roles":
        await query.message.reply_text("🆓 SELECT ROLE:", reply_markup=get_role_menu("normal"))
        return
    
    if data == "premium_search_roles":
        if USERS[cid]["status"] != "active":
            await query.message.reply_text("🔒 PREMIUM ONLY", reply_markup=get_payment_screen())
            return
        await query.message.reply_text("👑 SELECT ROLE:", reply_markup=get_role_menu("premium"))
        return
    
    # ROLE SELECTION
    if data.startswith("N_"):
        role = data.replace("N_", "")
        USERS[cid]["role"] = role
        USERS[cid]["queries"] += 1
        
        if USERS[cid]["queries"] > 2 and cid not in KING_PASS:
            await query.message.reply_text("⏳ LIMIT REACHED", reply_markup=get_ad_screen())
            return
        
        jobs = [row.to_dict() for _, row in df.iterrows() if row['Role'] == role]
        CACHE.setdefault(cid, {})[role] = jobs
        
        await query.message.reply_text(f"🆓 {role}: {len(jobs)} jobs", reply_markup=get_job_swarm(jobs, role, "normal", 0, 5))
        return
    
    if data.startswith("P_"):
        role = data.replace("P_", "")
        USERS[cid]["role"] = role
        
        if USERS[cid]["status"] != "active":
            await query.message.reply_text("🔒 PREMIUM ONLY", reply_markup=get_payment_screen())
            return
        
        jobs = [row.to_dict() for _, row in df.iterrows() if row['Role'] == role]
        CACHE.setdefault(cid, {})[role] = jobs
        
        await query.message.reply_text(f"👑 {role}: {len(jobs)} jobs", reply_markup=get_job_swarm(jobs, role, "premium", 0, 5))
        return
    
    # PAGINATION
    if data.startswith("PAGE_"):
        parts = data.split("_")
        mode = parts[1]
        role = parts[2]
        page = int(parts[3])
        
        jobs = CACHE.get(cid, {}).get(role, [])
        if not jobs:
            return
        
        await query.message.reply_text(f"{'🆓' if mode=='normal' else '👑'} {role} Page {page+1}", reply_markup=get_job_swarm(jobs, role, mode, page, 5))
        return
    
    # VIEW LOCKED
    if data.startswith("LOCK_"):
        parts = data.split("_")
        role = parts[1]
        idx = int(parts[2])
        
        jobs = CACHE.get(cid, {}).get(role, [])
        if not jobs or idx >= len(jobs):
            return
        
        job = jobs[idx]
        mins = int((datetime.now() - datetime.strptime(job['Timestamp'], '%Y-%m-%d %H:%M:%S')).total_seconds() / 60)
        
        text = f"🔒 LOCKED\n\n{job['Job Title']}\n🏥 {job['Employer']}\n⏰ {mins}m ago\n\n🔓 UPGRADE TO SEE"
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔓 UPGRADE", callback_data="unlock_premium")]]))
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
                await query.message.reply_text("📺 AD BREAK", reply_markup=get_ad_screen())
                return
        
        await show_job(query, jobs, idx, role, mode, cid)
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
                await show_job(query, jobs, pending["idx"], pending["role"], pending["mode"], cid)
                return
        
        await query.message.reply_text("✅ CONTINUE", reply_markup=get_normal_dashboard())
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
        await query.message.reply_text(f"📋 SEARCH TERM:\n\n`{job['Link']}`\n\n✅ Paste in www.jobs.nhs.uk", parse_mode="Markdown")
        return
    
    # AI COMPARE
    if data.startswith("AI_"):
        parts = data.split("_")
        mode = parts[1]
        role = parts[2]
        idx = int(parts[3])
        
        if USERS[cid]["status"] != "active":
            await query.message.reply_text("🔒 PREMIUM ONLY", reply_markup=get_payment_screen())
            return
        
        jobs = CACHE.get(cid, {}).get(role, [])
        if not jobs or idx >= len(jobs):
            return
        
        job = jobs[idx]
        await query.message.reply_text(f"📊 AI COMPARE\n\n{job['Job Title']}\n\nSet up profile for scores!")
        return
    
    # TODAY'S JOBS
    if data == "premium_todays_vault":
        if USERS[cid]["status"] != "active":
            await query.message.reply_text("🔒 PREMIUM ONLY", reply_markup=get_payment_screen())
            return
        
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        todays = [row.to_dict() for _, row in df.iterrows() if datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S') >= today_start]
        todays.sort(key=lambda x: datetime.strptime(x['Timestamp'], '%Y-%m-%d %H:%M:%S'), reverse=True)
        
        if not todays:
            await query.message.reply_text("📅 NO JOBS TODAY", reply_markup=get_premium_dashboard())
            return
        
        CACHE.setdefault(cid, {})["todays"] = todays
        
        buttons = []
        for i, job in enumerate(todays[:5]):
            mins = int((now - datetime.strptime(job['Timestamp'], '%Y-%m-%d %H:%M:%S')).total_seconds() / 60)
            buttons.append([InlineKeyboardButton(f"🔥 {job['Role']} ({mins}m)", callback_data=f"TODAYVIEW_{i}")])
        
        buttons.append([InlineKeyboardButton("🔙 BACK", callback_data="back_premium")])
        await query.message.reply_text(f"📅 TODAY'S JOBS: {len(todays)}", reply_markup=InlineKeyboardMarkup(buttons))
        return
    
    if data.startswith("TODAYVIEW_"):
        if USERS[cid]["status"] != "active":
            await query.message.reply_text("🔒 PREMIUM ONLY", reply_markup=get_payment_screen())
            return
        
        idx = int(data.replace("TODAYVIEW_", ""))
        jobs = CACHE.get(cid, {}).get("todays", [])
        if not jobs or idx >= len(jobs):
            return
        
        job = jobs[idx]
        mins = int((datetime.now() - datetime.strptime(job['Timestamp'], '%Y-%m-%d %H:%M:%S')).total_seconds() / 60)
        
        text = f"🔥 {mins}M AGO\n\n{job['Job Title']}\n🏥 {job['Employer']}\n💰 {job['Salary']}\n\n"
        text += f"🔴 ESSENTIAL:\n{job['Essential_Criteria']}\n\n"
        text += f"🔵 DESIRABLE:\n{job['Desirable_Criteria']}\n\n"
        text += f"✅ SEARCH: `{job['Link']}`"
        
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 COPY", callback_data=f"TODAYCOPY_{idx}")],
            [InlineKeyboardButton("🔙 BACK", callback_data="premium_todays_vault")]
        ]))
        return
    
    if data.startswith("TODAYCOPY_"):
        idx = int(data.replace("TODAYCOPY_", ""))
        jobs = CACHE.get(cid, {}).get("todays", [])
        if jobs and idx < len(jobs):
            await query.message.reply_text(f"📋 `{jobs[idx]['Link']}`", parse_mode="Markdown")
        return
    
    # PAYMENT
    if data == "unlock_premium":
        if cid in PENDING and PENDING[cid]["status"] == "pending":
            await query.message.reply_text("⏳ PENDING", reply_markup=get_pending_screen())
            return
        await query.message.reply_text("💰 PAY $10", reply_markup=get_payment_screen())
        return
    
    if data == "pay_submit":
        PENDING[cid] = {"time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "status": "pending"}
        
        try:
            await context.bot.send_message(
                chat_id=int(ADMIN_CHAT_ID),
                text=f"🚨 NEW PAYMENT\n\nUser: {cid}\nAmount: 10 USDT\n\nAPPROVE?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ APPROVE", callback_data=f"ADMIN_APPROVE_{cid}")],
                    [InlineKeyboardButton("❌ REJECT", callback_data=f"ADMIN_REJECT_{cid}")]
                ])
            )
        except:
            pass
        
        await query.message.reply_text("⏳ SUBMITTED. WAIT FOR APPROVAL.", reply_markup=get_pending_screen())
        return
    
    # ADMIN
    if data.startswith("ADMIN_APPROVE_"):
        target = data.replace("ADMIN_APPROVE_", "")
        USERS[target]["status"] = "active"
        if target in PENDING:
            PENDING[target]["status"] = "approved"
        
        try:
            await context.bot.send_message(chat_id=int(target), text="🎉 APPROVED! PREMIUM ACTIVE.", reply_markup=get_main_screen())
        except:
            pass
        
        await query.message.reply_text(f"✅ APPROVED {target}")
        return
    
    if data.startswith("ADMIN_REJECT_"):
        target = data.replace("ADMIN_REJECT_", "")
        if target in PENDING:
            PENDING[target]["status"] = "rejected"
        
        try:
            await context.bot.send_message(chat_id=int(target), text="❌ REJECTED.")
        except:
            pass
        
        await query.message.reply_text(f"❌ REJECTED {target}")
        return


# ==================== SHOW JOB ====================
async def show_job(query, jobs, idx, role, mode, cid):
    job = jobs[idx]
    now = datetime.now()
    t = datetime.strptime(job['Timestamp'], '%Y-%m-%d %H:%M:%S')
    age_hours = (now - t).total_seconds() / 3600
    is_premium = USERS[cid]["status"] == "active"
    
    if age_hours < 1:
        age_text = f"{int(age_hours * 60)}m ago 🔥"
    elif age_hours < 24:
        age_text = f"{int(age_hours)}h ago"
    else:
        age_text = f"{int(age_hours / 24)}d ago"
    
    badge = "👑 " if is_premium else ""
    
    text = f"{badge}📌 Job {idx+1} of {len(jobs)}\n\n"
    text += f"{job['Job Title']}\n"
    text += f"🏥 {job['Employer']}\n"
    text += f"💰 {job['Salary']}\n"
    text += f"🛂 {job['Visa']}\n"
    text += f"📍 {job['Region']}\n"
    text += f"⏰ {age_text}\n\n"
    
    text += f"📋 PERSON SPEC\n\n"
    text += f"🔴 ESSENTIAL:\n{job['Essential_Criteria']}\n\n"
    text += f"🔵 DESIRABLE:\n{job['Desirable_Criteria']}\n\n"
    
    # JOB FINDER
    text += f"✅ HOW TO APPLY:\n"
    text += f"1️⃣ Go to www.jobs.nhs.uk\n"
    text += f"2️⃣ Search: {job['Link']}\n"
    text += f"3️⃣ Filter by: {job['Region']}\n"
    text += f"4️⃣ Upload CV + GMC\n"
    text += f"5️⃣ Apply!\n\n"
    
    text += f"📋 COPY SEARCH:\n`{job['Link']}`"
    
    if is_premium:
        text += f"\n\n✨ PREMIUM ACTIVE"
    
    await query.message.reply_text(text, parse_mode="Markdown", reply_markup=get_job_detail(idx, role, mode, len(jobs), is_premium))


# ==================== MAIN ====================
async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    print("✅ BOT RUNNING!")
    
    while True:
        await asyncio.sleep(3600)

await main()
