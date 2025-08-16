from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests, json, threading
from datetime import datetime, date

BOT_TOKEN = "8126998281:AAGiO9irbqrgJQNJwYN8_23XbxReZMRSPyw"   # 👉 yahan apna BotFather token daalna
ADMIN_ID = 8264225408                # 👉 apna Telegram user id (int) daalna
API_URL = "https://api-vehicle-osint.vercel.app/"
ADMIN_USERNAME = "@MONSTER_1838"

# --- Logging Function ---
def save_log(user, action, detail=""):
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | User: {user} | Action: {action} | Detail: {detail}\n")

# --- Bots DB ---
def load_bots():
    try:
        with open("bots.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_bots(bots):
    with open("bots.json", "w") as f:
        json.dump(bots, f, indent=2)

# --- Users DB ---
def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f)

# --- Credits DB ---
def load_credits():
    try:
        with open("credits.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_credits(credits):
    with open("credits.json", "w") as f:
        json.dump(credits, f, indent=2)

# --- Referrals DB ---
def load_referrals():
    try:
        with open("referrals.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_referrals(refs):
    with open("referrals.json", "w") as f:
        json.dump(refs, f, indent=2)

# --- Initialize User Credits (3 free per day) ---
def init_credits(user_id):
    credits = load_credits()
    today = str(date.today())
    if str(user_id) not in credits:
        credits[str(user_id)] = {"credits": 3, "last_reset": today, "search_count": 0}
    else:
        # reset daily
        if credits[str(user_id)]["last_reset"] != today:
            credits[str(user_id)]["credits"] = 3
            credits[str(user_id)]["last_reset"] = today
            credits[str(user_id)]["search_count"] = 0
    save_credits(credits)
    return credits[str(user_id)]

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username or update.effective_user.first_name
    chat_id = update.effective_chat.id

    # Check for referral code
    args = context.args
    if args:
        referrer = args[0].replace("@", "")
        if referrer != str(chat_id):
            referrals = load_referrals()
            if referrer not in referrals:
                referrals[referrer] = []
            if str(chat_id) not in referrals[referrer]:
                referrals[referrer].append(str(chat_id))
                save_referrals(referrals)

                # Give 1 credit to referrer
                credits = load_credits()
                if referrer in credits:
                    credits[referrer]["credits"] += 1
                    save_credits(credits)

    keyboard = [["SEARCH 🔍"], ["CLONE 🪬"], ["SUPPORT 📩"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "⚠️ 𝗗𝗜𝗦𝗖𝗟𝗔𝗜𝗠𝗘𝗥 ⚠️\n"
        "𝗧𝗵𝗶𝘀 𝗕𝗼𝘁 𝗶𝘀 𝗺𝗮𝗱𝗲 𝗯𝘆 @monster_1838\n"
        "𝗜𝗳 𝘆𝗼𝘂 𝗳𝗮𝗰𝗲 𝗮𝗻𝘆 𝗶𝘀𝘀𝘂𝗲, 𝘂𝘀𝗲 𝗦𝗨𝗣𝗣𝗢𝗥𝗧 𝗯𝘂𝘁𝘁𝗼𝗻 ✅\n"
        "🚩 Welcome to MONSTER BOT!\nChoose an option:",
        reply_markup=reply_markup
    )
    save_log(username, "START")

    # Save user for broadcast
    users = load_users()
    if chat_id not in users:
        users.append(chat_id)
        save_users(users)

    # Initialize credits
    init_credits(chat_id)

# --- Handle Messages ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    username = update.effective_user.username or update.effective_user.first_name
    chat_id = update.effective_chat.id

    # Initialize credits
    user_cred = init_credits(chat_id)

    # SEARCH Button
    if text == "SEARCH 🔍":
        if user_cred["credits"] <= 0:
            await update.message.reply_text(
                f"⚠️ Your credits are over! Contact {ADMIN_USERNAME} to purchase."
            )
            return
        await update.message.reply_text("👉 Vehicle number bhejo (example: BR05M6477)")
        save_log(username, "CLICK", "SEARCH")
        return

    # SUPPORT Button
    elif text == "SUPPORT 📩":
        await update.message.reply_text(f"📩 Support: Contact {ADMIN_USERNAME}")
        save_log(username, "CLICK", "SUPPORT")
        return

    # CLONE Button
    elif text == "CLONE 🪬":
        await update.message.reply_text("🪬 Apna bot token bhejo:")
        context.user_data["awaiting_token"] = True
        save_log(username, "CLICK", "CLONE")
        return

    # Vehicle number search
    if text and len(text) >= 6 and text[0].isalpha() and not context.user_data.get("awaiting_token"):
        if user_cred["credits"] <= 0:
            await update.message.reply_text(
                f"⚠️ Your credits are over! Contact {ADMIN_USERNAME} to purchase."
            )
            return

        api_url = f"{API_URL}?rc={text}"
        try:
            resp = requests.get(api_url)
            data = resp.json()
        except Exception as e:
            await update.message.reply_text(f"⚠️ API Error: {e}")
            return

        save_log(username, "SEARCH", text)

        if "error" in data:
            await update.message.reply_text(f"❌ {data['error']}")
        else:
            message = "👤 *Owner Information*\n"
            message += f"• Name: {data.get('owner_name', 'N/A')}\n"
            message += f"• Father's Name: {data.get('father_name', 'N/A')}\n"
            message += f"• Address: {data.get('address', 'N/A')}, {data.get('city', 'N/A')}\n"
            message += f"• Phone: {data.get('phone', 'N/A')}\n"
            message += f"• RTO: {data.get('rto', 'N/A')}\n\n"

            message += "🚘 *Vehicle Details*\n"
            message += f"• Model: {data.get('model_name', 'N/A')}\n"
            message += f"• Variant: {data.get('maker_model', 'N/A')}\n"
            message += f"• Class: {data.get('vehicle_class', 'N/A')}\n"
            message += f"• Fuel: {data.get('fuel_type', 'N/A')} ({data.get('fuel_norms', 'N/A')})\n"
            message += f"• Reg Date: {data.get('registration_date', 'N/A')}\n\n"

            message += "📄 *Insurance Details*\n"
            message += f"• Company: {data.get('insurance_company', 'N/A')}\n"
            message += f"• Policy No: {data.get('insurance_no', 'N/A')}\n"
            message += f"• Valid Until: {data.get('insurance_upto', 'N/A')}\n\n"

            message += "📑 *Other Documents*\n"
            message += f"• Fitness Valid Until: {data.get('fitness_upto', 'N/A')}\n"
            message += f"• Tax Paid Until: {data.get('tax_upto', 'N/A')}\n"
            message += f"• PUC Valid Until: {data.get('puc_upto', 'N/A')}\n"

            if data.get('financier_name'):
                message += f"\n🚨 *Financed by:* {data.get('financier_name')}"

            message += "\n\nCredit: MONSTER"
            await update.message.reply_text(message, parse_mode="Markdown")

            # Deduct 1 credit every 2 searches
            user_cred["search_count"] += 1
            if user_cred["search_count"] % 2 == 0:
                user_cred["credits"] -= 1
            credits = load_credits()
            credits[str(chat_id)] = user_cred
            save_credits(credits)
        return

    # Clone bot
    if context.user_data.get("awaiting_token"):
        token = text
        bots = load_bots()
        bots[str(chat_id)] = {"token": token, "active": True}
        save_bots(bots)

        save_log(username, "CLONE", f"Token Added: {token[:6]}...")
        await update.message.reply_text("✅ Bot cloned successfully and is now active!")
        context.user_data["awaiting_token"] = False

        threading.Thread(target=run_clone, args=(token,), daemon=True).start()
        return

# --- Clone Bot Function ---
def run_clone(token):
    clone_app = Application.builder().token(token).build()

    async def clone_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🚩 This is your cloned MONSTER bot!")

    clone_app.add_handler(CommandHandler("start", clone_start))
    print(f"[INFO] Clone bot started with token {token}")
    clone_app.run_polling()

# --- Broadcast Command (Admin Only) ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ You are not authorized to use this command.")

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
