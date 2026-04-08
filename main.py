import os
import asyncio
import requests
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from script import Script

# Logging
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# --- ENV ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# --- AI CORE ---
async def get_ai_response(text):
    if HF_TOKEN:
        try:
            url = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            res = requests.post(url, headers=headers, json={"inputs": f"User: {text}\nAssistant:"}, timeout=10)
            return res.json()[0]['generated_text'].split("Assistant:")[-1].strip()
        except: pass

    if OPENROUTER_KEY:
        try:
            headers = {"Authorization": f"Bearer {OPENROUTER_KEY}"}
            data = {"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": text}]}
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
            return res.json()['choices'][0]['message']['content']
        except:
            return "❌ `AI Core is currently unresponsive.`"

# --- PTB APP ---
# Hum 'Application' ko manually setup karenge taaki 'Updater' error na aaye
ptb_app = ApplicationBuilder().token(BOT_TOKEN).build()

async def start(u, c):
    kb = [[InlineKeyboardButton("➕ ADD ME TO GROUP", url=f"https://t.me/{c.bot.username}?startgroup=true")],
          [InlineKeyboardButton("🚀 HELP", callback_data="h")]]
    await u.message.reply_text(Script.START_TXT, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def chat(u, c):
    if not u.message.text: return
    sticker = await u.message.reply_sticker(Script.THINK_STICKER)
    status = await u.message.reply_text(Script.AI_THINKING, parse_mode="Markdown")
    
    ans = await get_ai_response(u.message.text)
    await status.edit_text(f"✨ **FLIXORA AI:**\n\n{ans}", parse_mode="Markdown")
    try: await c.bot.delete_message(chat_id=u.effective_chat.id, message_id=sticker.message_id)
    except: pass

async def cb(u, c):
    await u.callback_query.answer()
    if u.callback_query.data == "h": await u.callback_query.message.edit_text(Script.HELP_TXT, parse_mode="Markdown")

# Register
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(CallbackQueryHandler(cb))
ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

# --- WEBHOOK LOGIC ---
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
async def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), ptb_app.bot)
        # Manual processing to avoid Updater crash
        await ptb_app.process_update(update)
        return "OK", 200

@app.route("/")
def health(): return "SYSTEM ONLINE", 200

# Initialization
async def setup():
    await ptb_app.initialize()
    await ptb_app.start()
    await ptb_app.bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")

# Run setup
asyncio.get_event_loop().run_until_complete(setup())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
