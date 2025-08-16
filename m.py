from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests, json, asyncio
from datetime import datetime

BOT_TOKEN = "8126998281:AAG7b4r7iDrA6gobWr7af8X4HYP_sWOEeOI"   # 👉 yahan apna BotFather se liya token daalo

# --- Logging Function ---
def save_log(user, action, detail=""):
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | User: {user} | Action: {action} | Detail: {detail}\n")

# --- Clone DB ---
def load_bots():
    try:
        with open("bots.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_bots(bots):
    with open("bots.json", "w") as f:
        json.dump(bots, f, indent=2)

# --- Users DB (for broadcast) ---
def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f)

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["SEARCH 🔍"], ["CLONE 🪬"], ["SUPPORT 📩"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🚩 Welcome to MONSTER BOT!\nChoose an option:",
        reply_markup=reply_markup
    )

    username = update.effective_user.username or update.effective_user.first_name
    save_log(username, "START")

    # ✅ Save user for broadcast
    chat_id = update.effective_chat.id
    users = load_users()
    if chat_id not in users:
        users.append(chat_id)
        save_users(users)

# --- Handle Messages ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    username = update.effective_user.username or update.effective_user.first_name

    # SEARCH Button
    if text == "SEARCH 🔍":
        await update.message.reply_text("👉 Vehicle number bhejo (example: BR05M6477)")
        save_log(username, "CLICK", "SEARCH")
        return

    # SUPPORT Button
    elif text == "SUPPORT 📩":
        await update.message.reply_text("📩 Support: Contact @Monster_1838")
        save_log(username, "CLICK", "SUPPORT")
        return

    # CLONE Button
    elif text == "CLONE 🪬":
        await update.message.reply_text("🪬 Apna bot token bhejo:")
        context.user_data["awaiting_token"] = True
        save_log(username, "CLICK", "CLONE")
        return

    # Agar user vehicle number bheje (SEARCH)
    if text and len(text) >= 6 and text[0].isalpha() and not context.user_data.get("awaiting_token"):
        api_url = f"https://api-vehicle-osint.vercel.app/?rc={text}"
        resp = requests.get(api_url)
        data = resp.json()

        save_log(username, "SEARCH", text)  # ✅ Log vehicle number

        if "error" in data:
            await update.message.reply_text(f"❌ {data['error']}")
        else:
            msg = f"""
🚗 Vehicle Info
RC: {data.get('rc_number','N/A')}
Owner: {data.get('owner_name','N/A')}
Model: {data.get('model_name','N/A')}
RTO: {data.get('rto','N/A')}

Credit: MONSTER
"""
            await update.message.reply_text(msg)
        return

    # Agar user token bheje (CLONE)
    if context.user_data.get("awaiting_token"):
        token = text
        bots = load_bots()
        bots[str(update.effective_user.id)] = {"token": token, "active": True}
        save_bots(bots)

        save_log(username, "CLONE", f"Token Added: {token[:6]}...")

        await update.message.reply_text("✅ Bot cloned successfully and is now active!")
        context.user_data["awaiting_token"] = False

        asyncio.create_task(start_clone(token))  # background me clone bot start hoga
        return

# --- Clone Bot Start ---
async def start_clone(token):
    app = Application.builder().token(token).build()

    async def clone_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🚩 This is your cloned MONSTER bot!")

    app.add_handler(CommandHandler("start", clone_start))
    print(f"[INFO] Clone bot started with token {token}")
    await app.run_polling()

# --- Broadcast Command ---
ADMIN_ID = 8264225408   # 👉 apna Telegram User ID daalna ( @userinfobot se le lena )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized for broadcast.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    
    message = " ".join(context.args)
    users = load_users()
    count = 0

    for uid in users:
        try:
            await context.bot.send_message(uid, f"📢 Broadcast:\n{message}")
            count += 1
        except:
            pass
    
    await update.message.reply_text(f"✅ Broadcast sent to {count} users.")

# --- Run Master Bot ---
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("broadcast", broadcast))  # ✅ Broadcast handler
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🚩 Master Bot running...")
app.run_polling()
