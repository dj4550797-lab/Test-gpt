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

# --- ENV VARIABLES ---
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
            res = requests.post(url, headers=headers, json={"inputs": text}, timeout=10)
            return res.json()[0]['generated_text']
        except: pass

    if OPENROUTER_KEY:
        try:
            headers = {"Authorization": f"Bearer {OPENROUTER_KEY}"}
            data = {"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": text}]}
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
            return res.json()['choices'][0]['message']['content']
        except:
            return "❌ `AI Core is currently offline.`"

# --- TELEGRAM LOGIC ---
ptb_app = ApplicationBuilder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("➕ ADD ME TO YOUR GROUP", url=f"https://t.me/{context.bot.username}?startgroup=true")],
          [InlineKeyboardButton("🚀 HELP", callback_data="h"), InlineKeyboardButton("🛰 ABOUT", callback_data="a")]]
    await update.message.reply_text(Script.START_TXT, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text: return
    
    # 1. Send Sticker
    sticker = await update.message.reply_sticker(Script.THINK_STICKER)
    # 2. Send Thinking Text
    status = await update.message.reply_text(Script.AI_THINKING, parse_mode="Markdown")
    
    # 3. AI logic
    answer = await get_ai_response(update.message.text)
    
    # 4. Final Answer
    await status.edit_text(f"✨ **FLIXORA AI:**\n\n{answer}", parse_mode="Markdown")
    # 5. Remove Sticker
    try: await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sticker.message_id)
    except: pass

async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "h": await query.message.edit_text(Script.HELP_TXT, parse_mode="Markdown")

# Register handlers
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(CallbackQueryHandler(cb))
ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))

# --- FLASK WEBHOOK ---
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
async def webhook():
    update = Update.de_json(request.get_json(force=True), ptb_app.bot)
    await ptb_app.process_update(update)
    return "OK", 200

@app.route("/")
def health(): return "Bot is Alive!", 200

# Function to set Webhook
async def setup_webhook():
    await ptb_app.initialize()
    await ptb_app.bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(setup_webhook())
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
