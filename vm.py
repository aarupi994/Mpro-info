from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests, json, asyncio
from datetime import datetime, date

BOT_TOKEN = "8126998281:AAE-zsNndnO5MmTE0B_5MqoUeHvmGK6svD4"   # 👉 apna BotFather token
ADMIN_ID = 8264225408                 # 👉 apna Telegram user id (int)
API_URL = "https://api-vehicle-osint.vercel.app/?rc="
ADMIN_USERNAME = "@MONSTER_1838"

# --- Logging Function ---
def save_log(user, action, detail=""):
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | User: {user} | Action: {action} | Detail: {detail}\n")

# --- Simple DB helpers ---
def load_json(fname, default):
    try:
        with open(fname, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(fname, data):
    with open(fname, "w") as f:
        json.dump(data, f, indent=2)

# DB Files
def load_bots(): return load_json("bots.json", {})
def save_bots(b): save_json("bots.json", b)
def load_users(): return load_json("users.json", [])
def save_users(u): save_json("users.json", u)
def load_credits(): return load_json("credits.json", {})
def save_credits(c): save_json("credits.json", c)
def load_referrals(): return load_json("referrals.json", {})
def save_referrals(r): save_json("referrals.json", r)

# --- Initialize User Credits (3 free per day) ---
def init_credits(user_id):
    credits = load_credits()
    today = str(date.today())
    if str(user_id) not in credits:
        credits[str(user_id)] = {"credits": 3, "last_reset": today, "search_count": 0}
    else:
        if credits[str(user_id)]["last_reset"] != today:
            credits[str(user_id)] = {"credits": 3, "last_reset": today, "search_count": 0}
    save_credits(credits)
    return credits[str(user_id)]

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username or update.effective_user.first_name
    chat_id = update.effective_chat.id

    args = context.args
    if args:
        referrer = args[0].replace("@", "")
        if referrer != str(chat_id):
            refs = load_referrals()
            if referrer not in refs:
                refs[referrer] = []
            if str(chat_id) not in refs[referrer]:
                refs[referrer].append(str(chat_id))
                save_referrals(refs)
                credits = load_credits()
                if referrer in credits:
                    credits[referrer]["credits"] += 1
                    save_credits(credits)

    keyboard = [["SEARCH 🔍"], ["CLONE 🪬"], ["SUPPORT 📩"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "⚠️ 𝗗𝗜𝗦𝗖𝗟𝗔𝗜𝗠𝗘𝗥 ⚠️\n"
        "𝗧𝗵𝗶𝘀 𝗕𝗼𝘁 𝗶𝘀 𝗺𝗮𝗱𝗲 𝗯𝘆 @monster_1838\n"
        "🚩 Welcome to MONSTER BOT!\nChoose an option:",
        reply_markup=reply_markup
    )
    save_log(username, "START")

    users = load_users()
    if chat_id not in users:
        users.append(chat_id)
        save_users(users)

    init_credits(chat_id)

# --- Handle Messages ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    username = update.effective_user.username or update.effective_user.first_name
    chat_id = update.effective_chat.id

    user_cred = init_credits(chat_id)

    if text == "SEARCH 🔍":
        if user_cred["credits"] <= 0:
            await update.message.reply_text(f"⚠️ Your credits are over! Contact {ADMIN_USERNAME}")
            return
        await update.message.reply_text("👉 Vehicle number bhejo (example: BR05M6477)")
        save_log(username, "CLICK", "SEARCH")
        return

    elif text == "SUPPORT 📩":
        await update.message.reply_text(f"📩 Support: Contact {ADMIN_USERNAME}")
        save_log(username, "CLICK", "SUPPORT")
        return

    elif text == "CLONE 🪬":
        await update.message.reply_text("🪬 Apna bot token bhejo:")
        context.user_data["awaiting_token"] = True
        save_log(username, "CLICK", "CLONE")
        return

    # Vehicle search
    if text and len(text) >= 6 and text[0].isalpha() and not context.user_data.get("awaiting_token"):
        if user_cred["credits"] <= 0:
            await update.message.reply_text(f"⚠️ Your credits are over! Contact {ADMIN_USERNAME}")
            return

        api_url = f"{API_URL}?rc={text}"
        try:
            resp = requests.get(api_url, timeout=10)
            data = resp.json()
        except Exception as e:
            await update.message.reply_text(f"⚠️ API Error: {e}")
            return

        save_log(username, "SEARCH", text)

        if "error" in data:
            await update.message.reply_text(f"❌ {data['error']}")
        else:
            msg = "👤 *Owner Information*\n"
            msg += f"• Name: {data.get('owner_name', 'Not Found')}\n"
            msg += f"• Father's Name: {data.get('father_name', 'Not Found')}\n"
            address = f"{data.get('address','Not Found')}"
            if data.get("city"): 
                address += f", {data['city']}"
            msg += f"• Address: {address}\n"
            msg += f"• Phone: {data.get('phone', 'Not Found')}\n"
            msg += f"• RTO: {data.get('rto', 'Not Found')}\n\n"

            msg += "🚘 *Vehicle Details*\n"
            msg += f"• Model: {data.get('model_name', 'Not Found')}\n"
            msg += f"• Variant: {data.get('maker_model', 'Not Found')}\n"
            msg += f"• Class: {data.get('vehicle_class', 'Not Found')}\n"
            msg += f"• Fuel: {data.get('fuel_type', 'Not Found')} ({data.get('fuel_norms', 'Not Found')})\n"
            msg += f"• Reg Date: {data.get('registration_date', 'Not Found')}\n\n"

            msg += "📄 *Insurance Details*\n"
            msg += f"• Company: {data.get('insurance_company', 'Not Found')}\n"
            msg += f"• Policy No: {data.get('insurance_no', 'Not Found')}\n"
            msg += f"• Valid Until: {data.get('insurance_expiry', data.get('insurance_upto', 'Not Found'))}\n\n"

            msg += "📑 *Other Documents*\n"
            msg += f"• Fitness Valid Until: {data.get('fitness_upto', 'Not Found')}\n"
            msg += f"• Tax Paid Until: {data.get('tax_upto', 'Not Found')}\n"
            msg += f"• PUC Valid Until: {data.get('puc_upto', 'Not Found')}\n"

            if data.get('financier_name'):
                msg += f"\n🚨 *Financed by:* {data.get('financier_name')}"

            msg += "\n\nCredit: MONSTER"
            await update.message.reply_text(msg, parse_mode="Markdown")

            user_cred["credits"] -= 1
            credits = load_credits()
            credits[str(chat_id)] = user_cred
            save_credits(credits)
        return

    # Clone bot
    if context.user_data.get("awaiting_token"):
        token = text.strip()
        bots = load_bots()
        bots[str(chat_id)] = {"token": token, "active": True}
        save_bots(bots)
        save_log(username, "CLONE", f"Token Added: {token[:6]}...")
        await update.message.reply_text("✅ Bot cloned successfully and is now active!")
        context.user_data["awaiting_token"] = False

        # Proper async clone run
        asyncio.create_task(run_clone(token))
        return

# --- Clone Bot Function ---
async def run_clone(token):
    clone_app = Application.builder().token(token).build()

    async def clone_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🚩 This is your cloned MONSTER bot!")

    clone_app.add_handler(CommandHandler("start", clone_start))
    print(f"[INFO] Clone bot started with token {token}")
    await clone_app.run_polling()

# --- Broadcast Command (Admin Only) ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ You are not authorized.")

    users = load_users()
    if not context.args:
        return await update.message.reply_text("⚠️ Usage: /broadcast Your_Message")

    msg = " ".join(context.args)
    sent = 0
    for uid in users:
        try:
            await context.bot.send_message(uid, f"📢 {msg}")
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ Broadcast sent to {sent} users.")

# --- Run Master Bot ---
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🚩 Master Bot running...")
app.run_polling()
