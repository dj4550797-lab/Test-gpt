import os
import asyncio
import requests
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
HF_TOKEN = os.environ.get("HF_TOKEN", "") # Hugging Face Token
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "") # E.g. https://your-app.onrender.com
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)

# --- AESTHETIC TEXTS (Human Touch) ---
class Script:
    START_TXT = """
✨ **Greetings, Commander!** ⚡

I am **FLIXORA AI**, your advanced neural assistant. I’ve been calibrated to provide high-speed responses and intelligent solutions.

**How can I assist you today?**
◈ Ask me anything (Science, Code, Art)
◈ Use premium AI models
◈ Deploy me in your groups

**System Status:** `Running smoothly 🟢`
"""
    HELP_TXT = """
🛠 **COMMAND CENTER**
━━━━━━━━━━━━━━━━━━━━
Here is how you can utilize my core:

🚀 `/start` - Restart the interface.
📝 `/register` - Create your identity.
💎 `/upgrade` - Access elite features.
🧠 `/settings` - Modify AI intelligence.

**Pro-Tip:** Just send a voice or text message, and I'll analyze it!
"""
    ABOUT_TXT = """
🛰 **SYSTEM SPECS**
━━━━━━━━━━━━━━━━━━━━
‣ **Core:** Hybrid Neural Engine (HF + GPT)
‣ **Version:** 4.0.1 (Pro)
‣ **Latency:** ~0.8s
‣ **Safety:** End-to-End Encrypted

*Designed for those who demand excellence.*
"""

# --- AI CORE LOGIC ---
async def get_ai_response(text):
    # 1. Try Hugging Face first (Fast & Free)
    if HF_TOKEN:
        try:
            API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            payload = {"inputs": text, "parameters": {"max_new_tokens": 500}}
            res = requests.post(API_URL, headers=headers, json=payload, timeout=10)
            return res.json()[0]['generated_text']
        except: pass 

    # 2. Fallback to OpenRouter
    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}"}
    data = {"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": text}]}
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        return res.json()['choices'][0]['message']['content']
    except:
        return "❌ `System overloaded. Please try again in a moment.`"

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ ADD ME TO YOUR GROUP ➕", url=f"https://t.me/FlixoraAiBot?startgroup=true")],
        [InlineKeyboardButton("🚀 HELP", callback_data="help"), InlineKeyboardButton("🛰 ABOUT", callback_data="about")],
        [InlineKeyboardButton("🌐 UPDATE CHANNEL", url="https://t.me/YourChannel"), InlineKeyboardButton("🎧 SUPPORT", url="https://t.me/YourSupport")],
        [InlineKeyboardButton("💎 GET PREMIUM ACCESS", callback_data="upgrade")]
    ]
    await update.message.reply_text(Script.START_TXT, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "help":
        await query.message.edit_text(Script.HELP_TXT, parse_mode="Markdown")
    elif query.data == "about":
        await query.message.edit_text(Script.ABOUT_TXT, parse_mode="Markdown")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text: return
    status = await update.message.reply_text("⚡ `Analyzing...`", parse_mode="Markdown")
    response = await get_ai_response(update.message.text)
    await status.edit_text(f"✨ **JARVIS:**\n\n{response}", parse_mode="Markdown")

# --- BOT INITIALIZATION ---
ptb_app = ApplicationBuilder().token(BOT_TOKEN).build()
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(CallbackQueryHandler(handle_callback))
ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

# --- FLASK & WEBHOOK ---
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
async def webhook():
    update = Update.de_json(request.get_json(force=True), ptb_app.bot)
    await ptb_app.process_update(update)
    return "OK", 200

@app.route("/")
def index(): return "Bot is Alive!", 200

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ptb_app.initialize())
    ptb_app.bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=PORT)
