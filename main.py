import os
import asyncio
import requests
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from script import Script

# Logging for Debugging
logging.basicConfig(level=logging.INFO)

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)

# --- AI LOGIC (Hybrid Model) ---
async def get_ai_reply(text):
    # Try Hugging Face (Fast & Human-like)
    if HF_TOKEN:
        try:
            url = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            payload = {"inputs": f"User: {text}\nAssistant:", "parameters": {"max_new_tokens": 500}}
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            return res.json()[0]['generated_text'].split("Assistant:")[-1].strip()
        except: pass

    # Fallback to OpenRouter (Reliable)
    if OPENROUTER_KEY:
        try:
            headers = {"Authorization": f"Bearer {OPENROUTER_KEY}"}
            data = {"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": text}]}
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=10)
            return res.json()['choices'][0]['message']['content']
        except:
            return "❌ `System failure: AI Core disconnected.`"

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ ADD ME TO YOUR GROUP ➕", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("🚀 HELP", callback_data="h"), InlineKeyboardButton("🛰 ABOUT", callback_data="a")],
        [InlineKeyboardButton("💎 GET PREMIUM ACCESS", callback_data="p")]
    ]
    await update.message.reply_text(Script.START_TXT, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text: return
    
    # 1. Send Thinking Sticker
    sticker_msg = await update.message.reply_sticker(sticker=Script.THINK_STICKER)
    
    # 2. Send Thinking Text
    status_msg = await update.message.reply_text(Script.AI_THINKING, parse_mode="Markdown")
    
    # 3. Get Answer
    response = await get_ai_reply(update.message.text)
    
    # 4. Update with final answer
    await status_msg.edit_text(f"✨ **FLIXORA AI:**\n\n{response}", parse_mode="Markdown")
    
    # 5. Delete sticker (Optional: taaki chat clean rahe)
    try: await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sticker_msg.message_id)
    except: pass

async def cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "h": await q.message.edit_text(Script.HELP_TXT, parse_mode="Markdown")
    elif q.data == "a": await q.message.edit_text(Script.ABOUT_TXT, parse_mode="Markdown")

# --- WEBHOOK LOGIC ---
ptb_app = ApplicationBuilder().token(BOT_TOKEN).build()
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(CallbackQueryHandler(cb_handler))
ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai))

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
async def process_update():
    update = Update.de_json(request.get_json(force=True), ptb_app.bot)
    await ptb_app.process_update(update)
    return "OK", 200

@app.route("/")
def health(): return "FLIXORA IS ONLINE", 200

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ptb_app.initialize())
    # Webhook setup
    ptb_app.bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=PORT)
