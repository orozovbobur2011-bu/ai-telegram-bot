import os
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL")  # https://your-app.onrender.com
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ================= MEMORY =================
user_memory = {}

# ================= FLASK + BOT =================
app = Flask(__name__)
bot_app = Application.builder().token(TOKEN).build()

# ================= AI FUNCTION =================
def ask_ai(user_id, text):
    if user_id not in user_memory:
        user_memory[user_id] = []

    history = user_memory[user_id][-6:]  # oxirgi 6 xabar

    messages = [
        {"role": "system", "content": "Siz yordamchi AI botsiz. Faqat aniq va foydali javob bering."}
    ]

    for h in history:
        messages.append(h)

    messages.append({"role": "user", "content": text})

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": messages
        }
    )

    result = response.json()
    answer = result["choices"][0]["message"]["content"]

    # memory update
    user_memory[user_id].append({"role": "user", "content": text})
    user_memory[user_id].append({"role": "assistant", "content": answer})

    return answer

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Men AI chat botman 🤖\nSavol bering!")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_memory[update.effective_user.id] = []
    await update.message.reply_text("Memory tozalandi 🧹")

# ================= MESSAGE HANDLER =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    await update.message.chat.send_action("typing")

    try:
        answer = ask_ai(user_id, text)
        await update.message.reply_text(answer)
    except Exception as e:
        await update.message.reply_text("Xatolik yuz berdi 😕")

# ================= WEBHOOK =================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    bot_app.update_queue.put_nowait(update)
    return "ok"

@app.route("/")
def home():
    return "AI Bot is running 🤖"

def set_webhook():
    url = f"{APP_URL}/{TOKEN}"
    requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={url}")

# ================= RUN =================
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("reset", reset))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
