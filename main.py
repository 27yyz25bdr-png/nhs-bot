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
        [InlineKeyboardButton("🆓 ━━━━━━━━━ NORMAL BOT ━━━━━━━━━", callback_data="enter_normal")],
        [InlineKeyboardButton("   FREE • Browse Jobs • Ads", callback_data="enter_normal")],
        [InlineKeyboardButton("👑 ━━━━━━━━━ PREMIUM BOT ━━━━━━━━━", callback_data="enter_premium")],
        [InlineKeyboardButton("   $10/mo • Instant • No Ads", callback_data="enter_premium")],
        [InlineKeyboardButton("📊 Compare Normal vs Premium", callback_data="compare_modes")]
    ])

def get_normal_dashboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 SEARCH JOBS BY ROLE", callback_data="normal_search_roles")],
        [InlineKeyboardButton("📋 BROWSE ALL OPEN JOBS", callback_data="normal_browse_all")],
        [InlineKeyboardButton("🔒 SEE PREMIUM-LOCKED JOBS", callback_data="normal_see_premium")],
        [InlineKeyboardButton("━" * 18, callback_data="noop")],
        [InlineKeyboardButton("👑 UPGRADE TO PREMIUM", callback_data="unlock_premium")],
        [InlineKeyboardButton("🏠 BACK TO MAIN", callback_data="back_main")]
    ])

def get_premium_dashboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 SEARCH JOBS BY ROLE", callback_data="premium_search_roles")],
        [InlineKeyboardButton("📅 TODAY'S JOBS (PREMIUM VAULT)", callback_data="premium_todays_vault")],
        [InlineKeyboardButton("⚡ REAL-TIME ALERT SETTINGS", callback_data="premium_alerts")],
        [InlineKeyboardButton("📊 AI MATCH COMPARISON", callback_data="premium_compare")],
        [InlineKeyboardButton("━" * 18, callback_data="noop")],
        [InlineKeyboardButton("👤 MY PROFILE", callback_data="premium_profile")],
        [InlineKeyboardButton("🏠 BACK TO MAIN", callback_data="back_main")]
    ])

def get_role_menu(mode):
    prefix = "N_" if mode == "normal" else "P_"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎓 JUNIOR CLINICAL FELLOW (JCF)", callback_data=f"{prefix}JCF"),
         InlineKeyboardButton("🎓 SENIOR CLINICAL FELLOW (SCF)", callback_data=f"{prefix}SCF")],
        [InlineKeyboardButton("🏫 TEACHING & RESEARCH", callback_data=f"{prefix}Teaching"),
         InlineKeyboardButton("🏥 TRUST GRADE / SHO", callback_data=f"{prefix}TrustGrade")],
        [InlineKeyboardButton("🚨 LAS (LOCUM ST1/2)", callback_data=f"{prefix}LAS"),
         InlineKeyboardButton("💼 LOCUM / BANK", callback_data=f"{prefix}Locum")],
        [InlineKeyboardButton("🩻 FOUNDATION YEAR 1", callback_data=f"{prefix}FY1"),
         InlineKeyboardButton("🩻 FOUNDATION YEAR 2", callback_data=f"{prefix}FY2")],
        [InlineKeyboardButton("🧬 CORE TRAINEE (CT1-CT3)", callback_data=f"{prefix}CT"),
         InlineKeyboardButton("🧬 ST1-ST2 REGISTRAR", callback_data=f"{prefix}ST_Junior")],
        [InlineKeyboardButton("🧬 ST3-ST8 REGISTRAR", callback_data=f"{prefix}ST_Senior"),
         InlineKeyboardButton("👑 SAS GRADE DOCTOR", callback_data=f"{prefix}SAS")],
        [InlineKeyboardButton("👑 SPECIALIST GRADE", callback_data=f"{prefix}Specialist"),
         InlineKeyboardButton("🩺 SALARIED GP", callback_data=f"{prefix}GP")],
        [InlineKeyboardButton("🦷 DENTAL TRACKS", callback_data=f"{prefix}Dental")],
        [InlineKeyboardButton("━" * 18, callback_data="noop")],
        [InlineKeyboardButton("🔙 BACK TO DASHBOARD", callback_data=f"back_{mode}")]
    ])

def get_job_swarm(jobs, role, mode, page=0, per_page=8):
    buttons = []
    now = datetime.now()
    start = page * per_page
    end = min(start + per_page, len(jobs))
    
    buttons.append([InlineKeyboardButton(f"📚 {role} — {len(jobs)} JOBS FOUND", callback_data="noop")])
    buttons.append([InlineKeyboardButton("━" * 18, callback_data="noop")])
    
    for i in range(start, end):
        job = jobs[i]
        t = datetime.strptime(job['Timestamp'], '%Y-%m-%d %H:%M:%S')
        age_hours = (now - t).total_seconds() / 3600
        
        if mode == "normal" and age_hours < 12:
            label = f"🔒 {job['Employer'][:28]}... (PREMIUM ONLY)"
            cb = f"LOCK_{role}_{i}"
        else:
            label = f"✅ {job['Employer'][:32]}..."
            cb = f"VIEW_{mode}_{role}_{i}"
        
        buttons.append([InlineKeyboardButton(label, callback_data=cb)])
    
    buttons.append([InlineKeyboardButton("━" * 18, callback_data="noop")])
    
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ PREV", callback_data=f"PAGE_{mode}_{role}_{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{(len(jobs)-1)//per_page + 1}", callback_data="noop"))
    if end < len(jobs):
        nav.append(InlineKeyboardButton("NEXT ➡️", callback_data=f"PAGE_{mode}_{role}_{page+1}"))
    if nav:
        buttons.append(nav)
    
    if end < len(jobs):
        remaining = len(jobs) - end
        buttons.append([InlineKeyboardButton(f"📥 LOAD MORE ({remaining} remaining)", 
                                            callback_data=f"PAGE_{mode}_{role}_{page+1}")])
    
    buttons.append([InlineKeyboardButton("🔙 BACK TO ROLES", callback_data=f"{mode}_search_roles"),
                    InlineKeyboardButton("🏠 MAIN MENU", callback_data="back_main")])
    
    return InlineKeyboardMarkup(buttons)

def get_ad_screen(jobs_viewed, ad_views_today, earnings_so_far):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 ━━━━━━━ SPONSORED ADVERTISEMENT ━━━━━━━", callback_data="noop")],
        [InlineKeyboardButton("━" * 18, callback_data="noop")],
        [InlineKeyboardButton("🚀 UK VISA & IMG CONSULTING SERVICES", url="https://t.me/your_channel")],
        [InlineKeyboardButton("💼 NHS JOB APPLICATION ASSISTANCE", url="https://t.me/your_channel")],
        [InlineKeyboardButton("📚 PLAB 1/2 PREPARATION COURSES", url="https://t.me/your_channel")],
        [InlineKeyboardButton("━" * 18, callback_data="noop")],
        [InlineKeyboardButton(f"📊 Your Stats: {jobs_viewed} jobs viewed", callback_data="noop")],
        [InlineKeyboardButton(f"💰 Ad Views Today: {ad_views_today}", callback_data="noop")],
        [InlineKeyboardButton("━" * 18, callback_data="noop")],
        [InlineKeyboardButton("✅ AD VIEWED — CONTINUE SEARCHING", callback_data="ad_dismiss")],
        [InlineKeyboardButton("👑 UPGRADE TO REMOVE ADS FOREVER", callback_data="unlock_premium")]
    ])

def get_job_detail(idx, role, mode, total, is_premium):
    buttons = []
    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"NAV_{mode}_{role}_{idx-1}"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{total}", callback_data="noop"))
    if idx < total - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"NAV_{mode}_{role}_{idx+1}"))
    buttons.append(nav)
    
    buttons.append([InlineKeyboardButton("📋 COPY SEARCH TERM", callback_data=f"COPY_{mode}_{role}_{idx}")])
    
    if is_premium:
        buttons.append([InlineKeyboardButton("📊 AI COMPARE ME VS JOB", callback_data=f"AI_{mode}_{role}_{idx}")])
    
    buttons.append([InlineKeyboardButton("🔙 BACK TO LIST", callback_data=f"PAGE_{mode}_{role}_0"),
                    InlineKeyboardButton("🏠 MAIN", callback_data="back_main")])
    
    return InlineKeyboardMarkup(buttons)

def get_locked_job(idx, role, total):
    buttons = []
    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"NAV_normal_{role}_{idx-1}"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{total}", callback_data="noop"))
    if idx < total - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"NAV_normal_{role}_{idx+1}"))
    buttons.append(nav)
    
    buttons.append([InlineKeyboardButton("🔒 PREMIUM VAULT — UNLOCK NOW", callback_data="unlock_premium")])
    buttons.append([InlineKeyboardButton("🔙 BACK TO LIST", callback_data=f"PAGE_normal_{role}_0"),
                    InlineKeyboardButton("🏠 MAIN", callback_data="back_main")])
    
    return InlineKeyboardMarkup(buttons)

def get_todays_vault(jobs, page=0, per_page=5):
    buttons = []
    start = page * per_page
    end = min(start + per_page, len(jobs))
    
    buttons.append([InlineKeyboardButton("🔐 PREMIUM VAULT — TODAY'S JOBS", callback_data="noop")])
    buttons.append([InlineKeyboardButton("━" * 18, callback_data="noop")])
    
    for i in range(start, end):
        job = jobs[i]
        mins = int((datetime.now() - datetime.strptime(job['Timestamp'], '%Y-%m-%d %H:%M:%S')).total_seconds() / 60)
        label = f"🔥 {job['Role']} @ {job['Employer'][:22]}... ({mins}m)"
        buttons.append([InlineKeyboardButton(label, callback_data=f"TODAYVIEW_{i}")])
    
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"TODAYPAGE_{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{(len(jobs)-1)//per_page + 1}", callback_data="noop"))
    if end < len(jobs):
        nav.append(InlineKeyboardButton("➡️", callback_data=f"TODAYPAGE_{page+1}"))
    if nav:
        buttons.append(nav)
    
    buttons.append([InlineKeyboardButton("🏠 MAIN MENU", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)

def get_payment_screen():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 PAYMENT: $10/month", callback_data="noop")],
        [InlineKeyboardButton("━" * 18, callback_data="noop")],
        [InlineKeyboardButton("🪙 Binance ID: 1251705066", callback_data="noop")],
        [InlineKeyboardButton("Send 10.00 USDT", callback_data="noop")],
        [InlineKeyboardButton("━" * 18, callback_data="noop")],
        [InlineKeyboardButton("🧾 I'VE PAID — SUBMIT RECEIPT", callback_data="pay_submit")],
        [InlineKeyboardButton("↩️ CANCEL", callback_data="back_main")]
    ])

def get_pending_screen():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏳ PAYMENT PENDING", callback_data="noop")],
        [InlineKeyboardButton("━" * 18, callback_data="noop")],
        [InlineKeyboardButton("Awaiting admin approval...", callback_data="noop")],
        [InlineKeyboardButton("You'll be notified within 24h", callback_data="noop")],
        [InlineKeyboardButton("━" * 18, callback_data="noop")],
        [InlineKeyboardButton("🏠 MAIN MENU", callback_data="back_main")]
    ])

def get_admin_approval(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✅ APPROVE USER {user_id}", callback_data=f"ADMIN_APPROVE_{user_id}")],
        [InlineKeyboardButton(f"❌ REJECT USER {user_id}", callback_data=f"ADMIN_REJECT_{user_id}")]
    ])

def get_revenue_dashboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 ━━━ AD REVENUE DASHBOARD ━━━", callback_data="noop")],
        [InlineKeyboardButton("━" * 18, callback_data="noop")],
        [InlineKeyboardButton("📊 View Today's Stats", callback_data="admin_today_stats")],
        [InlineKeyboardButton("📈 View Monthly Report", callback_data="admin_monthly_stats")],
        [InlineKeyboardButton("💸 Withdraw to Binance", callback_data="admin_withdraw")],
        [InlineKeyboardButton("━" * 18, callback_data="noop")],
        [InlineKeyboardButton("🔙 BACK", callback_data="back_main")]
    ])

# ==================== START ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = str(update.message.chat_id)
    
    if cid not in USERS:
        USERS[cid] = {
            "status": "active" if cid in KING_PASS else "free",
            "mode": None, "role": None, "queries": 0,
            "notified": [], "banned": False,
            "jobs_viewed": 0, "ad_views": 0, "last_ad_date": None
        }
    
    if USERS[cid].get("banned"):
        await update.message.reply_text("❌ ACCOUNT BANNED", parse_mode="Markdown")
        return
    
    if cid in KING_PASS:
        USERS[cid]["status"] = "active"
        await update.message.reply_text(
            "👑 *WELCOME BACK, KING!*\n\n"
            "You have **UNLIMITED FREE PREMIUM**.\n\n"
            "💰 *Admin Commands:*\n/revenue — View ad earnings\n/withdraw — Withdraw to Binance\n\n"
            "Select your mode:",
            parse_mode="Markdown",
            reply_markup=get_main_screen()
        )
        return
    
    if cid in PENDING and PENDING[cid]["status"] == "pending":
        await update.message.reply_text(
            "⏳ *PAYMENT PENDING*\n\nAwaiting admin approval.",
            parse_mode="Markdown",
            reply_markup=get_pending_screen()
        )
        return
    
    await update.message.reply_text(
        "🏥 *NHS UK MEDICAL & DENTAL JOBS BOT* 🇬🇧\n\n"
        "*Choose your access level:*\n\n"
        "🆓 *NORMAL BOT — FREE*\n"
        "• Browse jobs posted 12+ hours ago\n"
        "• Full Person Specifications\n"
        "• 2 searches per session\n"
        "• 📺 Ads every 3 job views\n\n"
        "👑 *PREMIUM BOT — $10/month*\n"
        "• ⚡ ALL jobs including today's fresh postings\n"
        "• 📅 Today's Jobs vault\n"
        "• 🔔 Real-time alerts (< 1 hour)\n"
        "• 📊 AI 'You vs Job' comparison\n"
        "• 🚫 **NO ADS EVER**\n"
        "• 🔓 Unlimited searches\n\n"
        "👇 *Select below:*",
        parse_mode="Markdown",
        reply_markup=get_main_screen()
    )

# ==================== ADMIN COMMANDS ====================
async def revenue_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = str(update.message.chat_id)
    if cid != ADMIN_CHAT_ID:
        return
    
    today = date.today().strftime('%Y-%m-%d')
    month = date.today().strftime('%Y-%m')
    
    today_stats = AD_REVENUE.get(today, {"views": 0, "earnings": 0.0})
    month_earnings = sum(v["earnings"] for k, v in AD_REVENUE.items() if k.startswith(month))
    total_earnings = sum(v["earnings"] for v in AD_REVENUE.values())
    total_views = sum(v["views"] for v in AD_REVENUE.values())
    
    text = (
        f"💰 *AD REVENUE DASHBOARD*\n\n"
        f"📅 *Today ({today}):*\n"
        f"   Views: {today_stats['views']}\n"
        f"   Earnings: ${today_stats['earnings']:.2f}\n\n"
        f"📈 *This Month:*\n"
        f"   Earnings: ${month_earnings:.2f}\n\n"
        f"💵 *All Time:*\n"
        f"   Total Views: {total_views}\n"
        f"   Total Earnings: ${total_earnings:.2f}\n\n"
        f"🪙 *Binance ID:* `{BINANCE_ID}`\n"
        f"Withdraw anytime!"
    )
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_revenue_dashboard())

async def withdraw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = str(update.message.chat_id)
    if cid != ADMIN_CHAT_ID:
        return
    
    total = sum(v["earnings"] for v in AD_REVENUE.values())
    
    await update.message.reply_text(
        f"💸 *WITHDRAWAL REQUEST*\n\n"
        f"Amount: ${total:.2f}\n"
        f"Destination: Binance ID {BINANCE_ID}\n\n"
        f"Processing...",
        parse_mode="Markdown"
    )

# ==================== BUTTON HANDLER ====================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cid = str(query.message.chat_id)
    data = query.data
    
    if cid not in USERS:
        USERS[cid] = {
            "status": "active" if cid in KING_PASS else "free",
            "mode": None, "role": None, "queries": 0,
            "notified": [], "banned": False,
            "jobs_viewed": 0, "ad_views": 0, "last_ad_date": None
        }
    
    if USERS[cid].get("banned"):
        return
    
    try:
        df = pd.read_csv("traced_nhs_jobs.csv")
    except:
        await query.message.reply_text("⚠️ Database error.")
        return
    
    if data == "noop":
        return
    
    # ADMIN ACTIONS
    if data.startswith("ADMIN_APPROVE_"):
        target = data.replace("ADMIN_APPROVE_", "")
        USERS[target]["status"] = "active"
        if target in PENDING:
            PENDING[target]["status"] = "approved"
        
        try:
            await context.bot.send_message(
                chat_id=int(target),
                text="🎉 *PAYMENT APPROVED!*\n\nPremium is now **ACTIVE**!\n\nEnjoy:\n• ⚡ Real-time alerts\n• 📅 Today's Jobs vault\n• 📊 AI Comparison\n• 🚫 **NO ADS**\n• 🔓 All jobs unlocked\n\nTap 👑 PREMIUM BOT to start!",
                parse_mode="Markdown",
                reply_markup=get_main_screen()
            )
        except:
            pass
        await query.message.reply_text(f"✅ Approved {target}")
        return
    
    if data.startswith("ADMIN_REJECT_"):
        target = data.replace("ADMIN_REJECT_", "")
        if target in PENDING:
            PENDING[target]["status"] = "rejected"
        
        try:
            await context.bot.send_message(
                chat_id=int(target),
                text="❌ *PAYMENT REJECTED*\n\nYour payment could not be verified.",
                parse_mode="Markdown"
            )
        except:
            pass
        await query.message.reply_text(f"❌ Rejected {target}")
        return
    
    if data == "admin_today_stats":
        today = date.today().strftime('%Y-%m-%d')
        stats = AD_REVENUE.get(today, {"views": 0, "earnings": 0.0})
        await query.message.reply_text(
            f"📊 *TODAY'S STATS*\n\n"
            f"Ad Views: {stats['views']}\n"
            f"Earnings: ${stats['earnings']:.2f}\n"
            f"Rate: ${AD_EARNINGS_PER_VIEW}/view",
            parse_mode="Markdown",
            reply_markup=get_revenue_dashboard()
        )
        return
    
    if data == "admin_monthly_stats":
        month = date.today().strftime('%Y-%m')
        month_data = {k: v for k, v in AD_REVENUE.items() if k.startswith(month)}
        total = sum(v["earnings"] for v in month_data.values())
        views = sum(v["views"] for v in month_data.values())
        
        text = f"📈 *MONTHLY REPORT ({month})*\n\n"
        for d, s in sorted(month_data.items()):
            text += f"{d}: {s['views']} views = ${s['earnings']:.2f}\n"
        text += f"\nTotal: {views} views = ${total:.2f}"
        
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=get_revenue_dashboard())
        return
    
    if data == "admin_withdraw":
        total = sum(v["earnings"] for v in AD_REVENUE.values())
        await query.message.reply_text(
            f"💸 *WITHDRAWAL INITIATED*\n\n"
            f"Amount: ${total:.2f}\n"
            f"To: Binance ID `{BINANCE_ID}`\n\n"
            f"Processing...",
            parse_mode="Markdown",
            reply_markup=get_revenue_dashboard()
        )
        return
    
    # MAIN NAVIGATION
    if data == "enter_normal":
        USERS[cid]["mode"] = "normal"
        await query.message.reply_text(
            "🆓 *NORMAL BOT ACTIVATED*\n\n"
            "✅ Browse jobs 12+ hours old\n"
            "✅ Full Person Specifications\n"
            "✅ Copy application links\n\n"
            "⚠️ **ADS:** Every 3 job views\n"
            "❌ Fresh jobs locked\n"
            "❌ 2 searches per session\n\n"
            "👇 What would you like to do?",
            parse_mode="Markdown",
            reply_markup=get_normal_dashboard()
        )
        return
    
    if data == "enter_premium":
        if USERS[cid]["status"] == "active":
            USERS[cid]["mode"] = "premium"
            await query.message.reply_text(
                "👑 *PREMIUM BOT ACTIVATED*\n\n"
                "✅ ALL jobs unlocked\n"
                "✅ Today's Jobs vault\n"
                "✅ Real-time alerts\n"
                "✅ AI Comparison\n"
                "🚫 **NO ADS EVER**\n"
                "✅ Unlimited searches\n\n"
                "👇 What would you like to do?",
                parse_mode="Markdown",
                reply_markup=get_premium_dashboard()
            )
        else:
            await query.message.reply_text(
                "🔒 *PREMIUM ACCESS REQUIRED*\n\n"
                "Upgrade to unlock everything!\n\n"
                "💰 $10/month via Binance",
                parse_mode="Markdown",
                reply_markup=get_payment_screen()
            )
        return
    
    if data == "compare_modes":
        text = (
            "📊 *NORMAL vs PREMIUM*\n\n"
            "```\nFEATURE               | NORMAL | PREMIUM\n"
            "----------------------|--------|--------\n"
            "Jobs >12h old         |   ✅   |   ✅\n"
            "Jobs <12h (TODAY)     |   ❌   |   ✅\n"
            "Today's Jobs vault    |   ❌   |   ✅\n"
            "Real-time alerts      |   ❌   |   ✅\n"
            "Person Specification  |   ✅   |   ✅\n"
            "AI You vs Job         |   ❌   |   ✅\n"
            "Search limit          |   2    |   ∞\n"
            "ADS                   |   ✅   |   ❌\n"
            "Copy links            |   ✅   |   ✅\n"
            "Price                 |  FREE  | $10/mo\n```\n\n"
            "💡 *Tip:* Normal users see ads every 3 job views. "
            "Premium = zero ads forever!"
        )
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_screen())
        return
    
    if data == "how_it_works":
        text = (
            "❓ *HOW IT WORKS*\n\n"
            "1️⃣ Choose NORMAL (free with ads) or PREMIUM ($10/mo, no ads)\n"
            "2️⃣ Select your target role\n"
            "3️⃣ Browse ALL jobs for that role\n"
            "4️⃣ Click any job for full details\n"
            "5️⃣ Copy link and apply!\n\n"
            "📺 *Ads in Normal Mode:*\nEvery 3 job views, you'll see a sponsored message. "
            "This keeps the bot free for everyone. Upgrade to Premium to remove ads forever!"
        )
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_screen())
        return
    
    # BACK NAVIGATION
    if data == "back_main":
        await query.message.reply_text("🏥 *NHS JOBS BOT*", parse_mode="Markdown", reply_markup=get_main_screen())
        return
    
    if data == "back_normal":
        USERS[cid]["mode"] = "normal"
        await query.message.reply_text("🆓 *NORMAL BOT*", parse_mode="Markdown", reply_markup=get_normal_dashboard())
        return
    
    if data == "back_premium":
        USERS[cid]["mode"] = "premium"
        await query.message.reply_text("👑 *PREMIUM BOT*", parse_mode="Markdown", reply_markup=get_premium_dashboard())
        return
    
    # NORMAL ACTIONS
    if data == "normal_search_roles":
        await query.message.reply_text(
            "🆓 *SELECT A ROLE*\n\n"
            "Showing jobs 12+ hours old.\n"
            "🔒 Fresh jobs are Premium-only.",
            parse_mode="Markdown",
            reply_markup=get_role_menu("normal")
        )
        return
    
    if data == "normal_browse_all":
        now = datetime.now()
        old_jobs = []
        for _, row in df.iterrows():
            t = datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S')
            if (now - t).total_seconds() / 3600 >= 12:
                old_jobs.append(row.to_dict())
        
        if not old_jobs:
            await query.message.reply_text("😕 No old jobs available.", reply_markup=get_normal_dashboard())
            return
        
        CACHE.setdefault(cid, {})["browse_all"] = old_jobs
        
        await query.message.reply_text(
            f"📚 *ALL OPEN JOBS*\n\n"
            f"Found {len(old_jobs)} jobs (12+ hours old):\n\n"
            f"👇 Click to view:",
            parse_mode="Markdown",
            reply_markup=get_job_swarm(old_jobs, "ALL", "normal", 0, 8)
        )
        return
    
    if data == "normal_see_premium":
        now = datetime.now()
        fresh = []
        for _, row in df.iterrows():
            t = datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S')
            if (now - t).total_seconds() / 3600 < 12:
                fresh.append(row.to_dict())
        
        if not fresh:
            await query.message.reply_text("😕 No fresh jobs locked.", reply_markup=get_normal_dashboard())
            return
        
        text = f"🔒 *PREMIUM VAULT — {len(fresh)} JOBS LOCKED*\n\n"
        for j in fresh[:5]:
            t = datetime.strptime(j['Timestamp'], '%Y-%m-%d %H:%M:%S')
            mins = int((now - t).total_seconds() / 60)
            text += f"• *{j['Role']}* @ {j['Employer'][:30]}... ({mins}m ago)\n"
        
        if len(fresh) > 5:
            text += f"\n... and {len(fresh) - 5} more!\n"
        
        text += "\n👑 *Upgrade to unlock all:*"
        
        await query.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔓 UNLOCK PREMIUM ($10/mo)", callback_data="unlock_premium")],
                [InlineKeyboardButton("🔙 BACK", callback_data="back_normal")]
            ])
        )
        return
    
    # PREMIUM ACTIONS
    if data == "premium_search_roles":
        if USERS[cid]["status"] != "active":
            await query.message.reply_text("🔒 Premium only!", reply_markup=get_payment_screen())
            return
        
        await query.message.reply_text(
            "👑 *SELECT A ROLE*\n\n"
            "ALL jobs unlocked including today's fresh postings!",
            parse_mode="Markdown",
            reply_markup=get_role_menu("premium")
        )
        return
    
    if data == "premium_todays_vault":
        if USERS[cid]["status"] != "active":
            await query.message.reply_text("🔒 Premium only!", reply_markup=get_payment_screen())
            return
        
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        todays = []
        for _, row in df.iterrows():
            t = datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S')
            if t >= today_start:
                todays.append(row.to_dict())
        
        todays.sort(key=lambda x: datetime.strptime(x['Timestamp'], '%Y-%m-%d %H:%M:%S'), reverse=True)
        
        if not todays:
            await query.message.reply_text(
                "📅 *TODAY'S JOBS VAULT*\n\n"
                "No new postings today.\n"
                "Real-time alerts are ON!",
                parse_mode="Markdown",
                reply_markup=get_premium_dashboard()
            )
            return
        
        CACHE.setdefault(cid, {})["todays"] = todays
        
        await query.message.reply_text(
            f"🔐 *PREMIUM VAULT — TODAY'S JOBS*\n\n"
            f"📅 {len(todays)} new postings today\n\n"
            f"🔥 Sorted by freshness:\n\n"
            f"👇 Click for details:",
            parse_mode="Markdown",
            reply_markup=get_todays_vault(todays, 0, 5)
        )
        return
    
    if data == "premium_alerts":
        if USERS[cid]["status"] != "active":
            await query.message.reply_text("🔒 Premium only!", reply_markup=get_payment_screen())
            return
        
        await query.message.reply_text(
            "⚡ *REAL-TIME ALERTS*\n\n"
            "✅ ACTIVE for your selected role\n"
            "You'll get instant notifications for jobs < 1 hour old.",
            parse_mode="Markdown",
            reply_markup=get_premium_dashboard()
        )
        return
    
    if data == "premium_compare":
        if USERS[cid]["status"] != "active":
            await query.message.reply_text("🔒 Premium only!", reply_markup=get_payment_screen())
            return
        
        await query.message.reply_text(
            "📊 *AI MATCH COMPARISON*\n\n"
            "Select a job from any role to see:\n"
            "• ✅ What you have\n"
            "• ❌ What you need\n"
            "• 📊 Match percentage\n\n"
            "Go to Search Jobs → Select role → Click 📊 AI COMPARE",
            parse_mode="Markdown",
            reply_markup=get_premium_dashboard()
        )
        return
    
    if data == "premium_profile":
        await query.message.reply_text(
            "👤 *MY PROFILE*\n\n"
            "Profile setup coming soon!\n"
            "Set your qualifications for accurate match scores.",
            parse_mode="Markdown",
            reply_markup=get_premium_dashboard()
        )
        return
    
    # AD DISMISS
    if data == "ad_dismiss":
        USERS[cid]["queries"] = 0
        today = date.today().strftime('%Y-%m-%d')
        if today not in AD_REVENUE:
            AD_REVENUE[today] = {"views": 0, "earnings": 0.0}
        AD_REVENUE[today]["views"] += 1
        AD_REVENUE[today]["earnings"] += AD_EARNINGS_PER_VIEW
        
        USERS[cid]["ad_views"] += 1
        USERS[cid]["last_ad_date"] = today
        
        pending = CACHE.get(cid, {}).get("pending_job")
        if pending:
            CACHE[cid]["pending_job"] = None
            jobs = CACHE.get(cid, {}).get(pending["role"], [])
            if jobs and pending["idx"] < len(jobs):
                await show_job(query, jobs, pending["idx"], pending["role"], pending["mode"], cid)
                return
        
        await query.message.reply_text(
            "✅ *Ad dismissed!* Continue browsing.\n\n"
            f"📊 Your ad views today: {USERS[cid]['ad_views']}\n"
            f"💰 Thank you for supporting the bot!",
            reply_markup=get_normal_dashboard()
        )
        return
    
    # ROLE SELECTION
    if data.startswith("N_"):
        role = data.replace("N_", "")
        USERS[cid]["role"] = role
        
        USERS[cid]["queries"] += 1
        if USERS[cid]["queries"] > 2 and cid not in KING_PASS:
            await query.message.reply_text(
                "⏳ *LIMIT REACHED*\n\n"
                "Watch ad to continue or upgrade to Premium!",
                parse_mode="Markdown",
                reply_markup=get_ad_screen(USERS[cid]["jobs_viewed"], USERS[cid]["ad_views"], 
                                           sum(v["earnings"] for v in AD_REVENUE.values()))
            )
            return
        
        jobs = []
        for _, row in df.iterrows():
            if row['Role'] == role:
                jobs.append(row.to_dict())
        
        CACHE.setdefault(cid, {})[role] = jobs
        
        now = datetime.now()
        old = sum(1 for j in jobs if (now - datetime.strptime(j['Timestamp'], '%Y-%m-%d %H:%M:%S')).total_seconds()/3600 >= 12)
        fresh = len(jobs) - old
        
        await query.message.reply_text(
            f"🆓 *NORMAL MODE — {role}*\n\n"
            f"📊 Total: {len(jobs)} jobs\n"
            f"✅ Available: {old}\n"
            f"🔒 Locked: {fresh}\n\n"
            f"👇 Click any job:",
            parse_mode="Markdown",
            reply_markup=get_job_swarm(jobs, role, "normal", 0, 8)
        )
        return
    
    if data.startswith("P_"):
        role = data.replace("P_", "")
        USERS[cid]["role"] = role
        
        if USERS[cid]["status"] != "active":
            await query.message.reply_text("🔒 Premium only!", reply_markup=get_payment_screen())
            return
        
        jobs = []
        for _, row in df.iterrows():
            if row['Role'] == role:
                jobs.append(row.to_dict())
        
        CACHE.setdefault(cid, {})[role] = jobs
        
        now = datetime.now()
        fresh = sum(1 for j in jobs if (now - datetime.strptime(j['Timestamp'], '%Y-%m-%d %H:%M:%S')).total_seconds()/3600 < 12)
        
        await query.message.reply_text(
            f"👑 *PREMIUM MODE — {role}*\n\n"
            f"📊 Total: **{len(jobs)}** jobs\n"
            f"🔥 Fresh (< 12h): {fresh}\n"
            f"✅ ALL JOBS UNLOCKED\n"
            f"🚫 NO ADS\n\n"
            f"👇 Click any job:",
            parse_mode="Markdown",
            reply_markup=get_job_swarm(jobs, role, "premium", 0, 8)
        )
        return
    
    # PAGINATION
    if data.startswith("PAGE_"):
        parts = data.split("_")
        mode = parts[1]
        role = parts[2]
        page = int(parts[3])
        
        jobs = CACHE.get(cid, {}).get(role, [])
        if not jobs:
            await query.message.reply_text("⚠️ Session expired.")
            return
        
        await query.message.reply_text(
            f"{'🆓' if mode=='normal' else '👑'} *{role} — Page {page+1}*",
            parse_mode="Markdown",
            reply_markup=get_job_swarm(jobs, role, mode, page, 8)
        )
        return
    
    # VIEW LOCKED JOB
    if data.startswith("LOCK_"):
        parts = data.split("_")
        role = parts[1]
        idx = int(parts[2])
        
        jobs = CACHE.get(cid, {}).get(role, [])
        if not jobs or idx >= len(jobs):
            return
        
        job = jobs[idx]
        now = datetime.now()
        t = datetime.strptime(job['Timestamp'], '%Y-%m-%d %H:%M:%S')
        mins = int((now - t).total_seconds() / 60)
        
        text = (
            f"🔒 *PREMIUM VAULT — LOCKED*\n\n"
            f"*{job['Job Title']}*\n"
            f"🏥 {job['Employer']}\n"
            f"💰 {job['Salary']}\n"
            f"🛂 {job['Visa']}\n"
            f"⏰ Posted {mins} minutes ago 🔥🔥🔥\n\n"
            f"❌ *HIDDEN:*\n"
            f"• Full Person Specification\n"
            f"• Essential & Desirable Criteria\n"
            f"• Application Link\n"
            f"• AI Match Comparison\n\n"
            f"💡 *Premium members applied {mins}m ago!*\n"
            f"Don't miss out!"
        )
        
        await query.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_locked_job(idx, role, len(jobs))
        )
        return
    
    # VIEW JOB (FULL)
    if data.startswith("VIEW_"):
        parts = data.split("_")
        mode = parts[1]
        role = parts[2]
        idx = int(parts[3])
        
        jobs = CACHE.get(cid, {}).get(role, [])
        if not jobs or idx >= len(jobs):
            await query.message.reply_text("⚠️ Job not found.")
            return
        
        # AD TRIGGER
        if mode == "normal" and cid not in KING_PASS:
            USERS[cid]["jobs_viewed"] += 1
            if USERS[cid]["jobs_viewed"] % AD_INTERVAL == 0:
                today = date.today().strftime('%Y-%m-%d')
                if today not in AD_REVENUE:
                    AD_REVENUE[today] = {"views": 0, "earnings": 0.0}
                
                CACHE.setdefault(cid, {})["pending_job"] = {"mode": mode, "role": role, "idx": idx}
                
                await query.message.reply_text(
                    f"📺 *AD BREAK — Job {idx+1} of {len(jobs)}*\n\n"
                    f"📊 You've viewed {USERS[cid]['jobs_viewed']} jobs\n"
                    f"💰 Supporting free access for IMGs worldwide!\n\n"
                    f"👇 Watch sponsor to continue:",
                    parse_mode="Markdown",
                    reply_markup=get_ad_screen(USERS[cid]["jobs_viewed"], USERS[cid]["ad_views"],
                                               AD_REVENUE[today]["earnings"])
                )
                return
        
        # Show job
        await show_job(query, jobs, idx, role, mode, cid)
        return
    
    # NAVIGATION
    if data.startswith("NAV_"):
        parts = data.split("_")
        mode = parts[1]
        role = parts[2]
        idx = int(parts[3])
        
        jobs = CACHE.get(cid, {}).get(role, [])
        if not jobs or idx < 0 or idx >= len(jobs):
            return
        
        if mode == "normal" and cid not in KING_PASS:
            USERS[cid]["jobs_viewed"] += 1
            if USERS[cid]["jobs_viewed"] % AD_INTERVAL == 0:
                today = date.today().strftime('%Y-%m-%d')
                if today not in AD_REVENUE:
                    AD_REVENUE[today] = {"views": 0, "earnings": 0.0}
                
                CACHE.setdefault(cid, {})["pending_job"] = {"mode": mode, "role": role, "idx": idx}
                
                await query.message.reply_text(
                    f"📺 *AD BREAK*\n\n"
                    f"📊 Jobs viewed: {USERS[cid]['jobs_viewed']}\n"
                    f"💰 Thank you for supporting free access!",
                    parse_mode="Markdown",
                    reply_markup=get_ad_screen(USERS[cid]["jobs_viewed"], USERS[cid]["ad_views"],
                                               AD_REVENUE[today]["earnings"])
                )
                return
        
        await show_job(query, jobs, idx, role, mode, cid)
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
        # job['Link'] now contains the SEARCH TERM from new CSV
        await query.message.reply_text(
            f"📋 *COPY THIS SEARCH TERM:*\n\n"
            f"`{job['Link']}`\n\n"
            f"✅ Go to www.jobs.nhs.uk and paste this in the search box!",
            parse_mode="Markdown"
        )
        return
    
    # AI COMPARISON
    if data.startswith("AI_"):
        parts = data.split("_")
        mode = parts[1]
        role = parts[2]
        idx = int(parts[3])
        
        if USERS[cid]["status"] != "active":
            await query.message.reply_text("🔒 Premium only!", reply_markup=get_payment_screen())
            return
        
        jobs = CACHE.get(cid, {}).get(role, [])
        if not jobs or idx >= len(jobs):
            return
        
        job = jobs[idx]
        ess = job['Essential_Criteria'].split(", ")
        des = job['Desirable_Criteria'].split(", ")
        
        text = (
            f"📊 *AI COMPARISON: YOU vs JOB*\n\n"
            f"*{job['Job Title']}*\n"
            f"🏥 {job['Employer']}\n\n"
            f"```\n{'REQUIREMENT':<<30} | {'YOU':<<10} | {'STATUS'}\n"
            f"{'-'*30}-+-{'-'*10}-+-{'-'*6}\n"
        )
        for e in ess:
            text += f"{e[:30]:<<30} | {'?':<<10} | {'❓'}\n"
        text += f"{'-'*30}-+-{'-'*10}-+-{'-'*6}\n"
        text += f"{'BONUS POINTS':<<30} | {'YOU':<<10} | {'BONUS'}\n"
        text += f"{'-'*30}-+-{'-'*10}-+-{'-'*6}\n"
        for d in des:
            text += f"{d[:30]:<<30} | {'?':<<10} | {'💡'}\n"
        text += "```\n\n"
        text += "💡 *Set up your profile for accurate scores!*"
        
        await query.message.reply_text(text, parse_mode="Markdown")
        return
    
    # TODAY'S JOBS VIEW
    if data.startswith("TODAYVIEW_"):
        if USERS[cid]["status"] != "active":
            await query.message.reply_text("🔒 Premium only!", reply_markup=get_payment_screen())
            return
        
        idx = int(data.replace("TODAYVIEW_", ""))
        jobs = CACHE.get(cid, {}).get("todays", [])
        
        if not jobs or idx >= len(jobs):
            return
        
        job = jobs[idx]
        now = datetime.now()
        t = datetime.strptime(job['Timestamp'], '%Y-%m-%d %H:%M:%S')
        mins = int((now - t).total_seconds() / 60)
        
        text = (
            f"🔥 *TODAY'S JOB — {mins} MINUTES AGO*\n\n"
            f"*{job['Job Title']}*\n"
            f"🏥 {job['Employer']}\n"
            f"💰 {job['Salary']}\n"
            f"🛂 {job['Visa']}\n\n"
            f"📋 *PERSON SPEC*\n"
            f"🔴 Essential:\n"
        )
        for i, c in enumerate(job['Essential_Criteria'].split(", "), 1:
            text += f"   {i}. {c.strip()}\n"
        text += f"\n🔵 Desirable:\n"
        for i, c in enumerate(job['Desirable_Criteria'].split(", "), 1:
            text += f"   {i}. {c.strip()}\n"
        
        # JOB FINDER GUIDANCE
        text += f"\n✅ *HOW TO APPLY FOR THIS ROLE:*\n"
        text += f"1️⃣ Go to: www.jobs.nhs.uk\n"
        text += f"2️⃣ Search: `{job['Link']}`\n"
        text += f"3️⃣ Filter by: {job['Region']}\n"
        text += f"4️⃣ Upload CV + GMC certificate\n"
        text += f"5️⃣ Apply before deadline!\n\n"
        
        text += f"📋 *Copy this search term:*\n`{job['Link']}`"
        
        await query.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 COPY SEARCH TERM", callback_data=f"TODAYCOPY_{idx}")],
                [InlineKeyboardButton("📊 AI COMPARE", callback_data=f"TODAYAI_{idx}")],
                [InlineKeyboardButton("🔙 BACK", callback_data="premium_todays_vault"),
                 InlineKeyboardButton("🏠 MAIN", callback_data="back_main")]
            ])
        )
        return
    
    if data.startswith("TODAYPAGE_"):
        if USERS[cid]["status"] != "active":
            await query.message.reply_text("🔒 Premium only!", reply_markup=get_payment_screen())
            return
        
        page = int(data.replace("TODAYPAGE_", ""))
        jobs = CACHE.get(cid, {}).get("todays", [])
        
        if not jobs:
            return
        
        await query.message.reply_text(
            f"🔐 *TODAY'S JOBS — Page {page+1}*",
            parse_mode="Markdown",
            reply_markup=get_todays_vault(jobs, page, 5)
        )
        return
    
    if data.startswith("TODAYCOPY_"):
        idx = int(data.replace("TODAYCOPY_", ""))
        jobs = CACHE.get(cid, {}).get("todays", [])
        if jobs and idx < len(jobs):
            job = jobs[idx]
            await query.message.reply_text(
                f"📋 *COPY THIS SEARCH TERM:*\n\n`{job['Link']}`\n\n"
                f"✅ Paste this in www.jobs.nhs.uk search box!",
                parse_mode="Markdown"
            )
        return
    
    if data.startswith("TODAYAI_"):
        if USERS[cid]["status"] != "active":
            await query.message.reply_text("🔒 Premium only!", reply_markup=get_payment_screen())
            return
        
        idx = int(data.replace("TODAYAI_", ""))
        jobs = CACHE.get(cid, {}).get("todays", [])
        if not jobs or idx >= len(jobs):
            return
        
        job = jobs[idx]
        await query.message.reply_text(f"📊 *AI COMPARISON*\n\n*{job['Job Title']}*\n\nSet up profile for scores!", parse_mode="Markdown")
        return
    
    # PAYMENT
    if data == "unlock_premium":
        if cid in PENDING and PENDING[cid]["status"] == "pending":
            await query.message.reply_text("⏳ Payment already pending!", parse_mode="Markdown", reply_markup=get_pending_screen())
            return
        
        await query.message.reply_text(
            f"🔒 *UNLOCK PREMIUM*\n\n"
            f"💰 $10/month\n\n"
            f"🪙 Binance ID: `{BINANCE_ID}`\n"
            f"Send 10.00 USDT\n\n"
            f"Then submit receipt:",
            parse_mode="Markdown",
            reply_markup=get_payment_screen()
        )
        return
    
    if data == "pay_submit":
        PENDING[cid] = {
            "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "status": "pending"
        }
        
        try:
            await context.bot.send_message(
                chat_id=int(ADMIN_CHAT_ID),
                text=f"🚨 *NEW PAYMENT*\n\n"
                     f"User: `{cid}`\n"
                     f"Amount: 10 USDT\n"
                     f"Time: {PENDING[cid]['time']}\n\n"
                     f"Verify on Binance:",
                parse_mode="Markdown",
                reply_markup=get_admin_approval(cid)
            )
        except Exception as e:
            print(f"Admin notify failed: {e}")
        
        await query.message.reply_text(
            "⏳ *PAYMENT SUBMITTED!*\n\n"
            "Admin will verify within 24h.\n"
            "You'll be notified once approved.",
            parse_mode="Markdown",
            reply_markup=get_pending_screen()
        )
        return


# ==================== SHOW JOB HELPER (JOB FINDER) ====================
async def show_job(query, jobs, idx, role, mode, cid):
    job = jobs[idx]
    now = datetime.now()
    t = datetime.strptime(job['Timestamp'], '%Y-%m-%d %H:%M:%S')
    age_hours = (now - t).total_seconds() / 3600
    is_premium = USERS[cid]["status"] == "active"
    
    if age_hours < 1:
        age_text = f"{int(age_hours * 60)} minutes ago 🔥"
    elif age_hours < 24:
        age_text = f"{int(age_hours)} hours ago"
    else:
        age_text = f"{int(age_hours / 24)} days ago"
    
    badge = "👑 " if is_premium else ""
    fresh = "🔥 FRESH! " if age_hours < 12 else ""
    
    text = f"{badge}{fresh}📌 *Job {idx+1} of {len(jobs)}*\n\n"
    text += f"*{job['Job Title']}*\n"
    text += f"🏥 {job['Employer']}\n"
    text += f"💰 {job['Salary']}\n"
    text += f"🛂 {job['Visa']}\n"
    text += f"📍 {job['Region']}\n"
    text += f"⏰ Posted: {age_text}\n\n"
    
    # PERSON SPECIFICATION
    text += f"📋 *PERSON SPECIFICATION*\n\n"
    text += f"🔴 *ESSENTIAL (Must Have):*\n"
    for i, c in enumerate(job['Essential_Criteria'].split(", "), 1):
        text += f"   {i}. {c.strip()}\n"
    text += f"\n"
    text += f"🔵 *DESIRABLE (Nice to Have):*\n"
    for i, c in enumerate(job['Desirable_Criteria'].split(", "), 1):
        text += f"   {i}. {c.strip()}\n"
    text += f"\n"
    
    # JOB FINDER — REAL APPLICATION GUIDANCE
    # job['Link'] now contains the SEARCH TERM from new CSV
    text += f"✅ *HOW TO APPLY FOR REAL NHS JOBS:*\n"
    text += f"1️⃣ Go to: www.jobs.nhs.uk\n"
    text += f"2️⃣ Search: `{job['Link']}`\n"
    text += f"3️⃣ Filter by: {job['Region']}\n"
    text += f"4️⃣ Upload CV + GMC certificate\n"
    text += f"5️⃣ Apply before deadline!\n\n"
    
    text += f"💡 *Pro Tip:*\n"
    text += f"Use this Person Spec as your checklist!\n\n"
    
    text += f"📋 *COPY THIS SEARCH TERM:*\n`{job['Link']}`"
    
    if is_premium:
        text += f"\n\n✨ *PREMIUM ACTIVE*"
    
    await query.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_job_detail(idx, role, mode, len(jobs), is_premium)
    )


# ==================== ALERT DAEMON ====================
async def alert_daemon(app):
    while True:
        try:
            now = datetime.now()
            df = pd.read_csv("traced_nhs_jobs.csv")
            
            for cid, profile in USERS.items():
                if profile.get("status") != "active" or not profile.get("role"):
                    continue
                
                role = profile["role"]
                for _, row in df[df['Role'] == role].iterrows():
                    t = datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S')
                    mins = (now - t).total_seconds() / 60
                    
                    if mins < 60 and row['Job Title'] not in profile.get("notified", []):
                        text = (
                            f"⚡ *PREMIUM RADAR ALERT!*\n\n"
                            f"🔥 *{row['Job Title']}*\n"
                            f"🏥 {row['Employer']}\n"
                            f"⏰ {int(mins)} minutes ago!\n\n"
                            f"📋 *PERSON SPEC:*\n"
                            f"🔴 {row['Essential_Criteria'][:80]}...\n"
                            f"🔵 {row['Desirable_Criteria'][:80]}...\n\n"
                            f"✅ *Go to www.jobs.nhs.uk and search: {row['Link']}*"
                        )
                        try:
                            await app.bot.send_message(chat_id=int(cid), text=text, parse_mode="Markdown")
                            profile.setdefault("notified", []).append(row['Job Title'])
                        except:
                            pass
            
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Daemon error: {e}")
            await asyncio.sleep(60)


# ==================== MAIN ====================
async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("revenue", revenue_cmd))
    app.add_handler(CommandHandler("withdraw", withdraw_cmd))
    app.add_handler(CallbackQueryHandler(button))
    
    asyncio.create_task(alert_daemon(app))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    print("=" * 50)
    print("✅ NHS JOBS BOT — JOB FINDER MODE RUNNING!")
    print(f"👑 Admin: {ADMIN_CHAT_ID}")
    print(f"📺 Ad Interval: Every {AD_INTERVAL} job views")
    print(f"💰 Ad Rate: ${AD_EARNINGS_PER_VIEW}/view")
    print("=" * 50)
    
    while True:
        await asyncio.sleep(3600)

await main()
