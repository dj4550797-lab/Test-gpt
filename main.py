import os
import asyncio
import requests
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from script import Script

# --- CONFIG ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)

# --- AI LOGIC ---
async def get_ai_reply(text):
    if HF_TOKEN:
        try:
            url = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            payload = {"inputs": f"<s>[INST] {text} [/INST]"}
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            return res.json()[0]['generated_text'].split("[/INST]")[-1].strip()
        except: pass

    # Fallback
    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}"}
    data = {"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": text}]}
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        return res.json()['choices'][0]['message']['content']
    except:
        return "❌ `AI Core Offline.`"

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("➕ ADD ME TO GROUP", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("🚀 HELP", callback_data="h"), InlineKeyboardButton("🛰 ABOUT", callback_data="a")]
    ]
    await update.message.reply_text(Script.START_TXT, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text: return
    
    # 1. Sticker Bhejna (Aesthetic Look)
    # Note: Agar ye sticker ID kaam na kare, toh apna fav sticker id yahan daal dein.
    try:
        sent_sticker = await update.message.reply_sticker(sticker="CAACAgIAAxkBAAENW_Rnz38m9-KToUfT5Nl9h-L0S7l7AAIBAQACVp29Ci_fS5vF9gABNgQ")
    except:
        sent_sticker = None

    # 2. Thinking Text
    status = await update.message.reply_text(Script.AI_THINKING, parse_mode="Markdown")
    
    # 3. Get AI Answer
    answer = await get_ai_reply(update.message.text)
    
    # 4. Final Reply & Sticker Delete (Taaki chat ganda na ho)
    await status.edit_text(f"✨ **FLIXORA:**\n\n{answer}", parse_mode="Markdown")
    
    # Option: Agar aap chahte ho ki sticker delete ho jaye answer ke baad, toh niche wali line rakho:
    # if sent_sticker: await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_sticker.message_id)

async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "h": await q.message.edit_text(Script.HELP_TXT, parse_mode="Markdown")

# --- APP SETUP ---
ptb_app = ApplicationBuilder().token(BOT_TOKEN).build()
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(CallbackQueryHandler(cb))
ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
async def webhook():
    update = Update.de_json(request.get_json(force=True), ptb_app.bot)
    await ptb_app.process_update(update)
    return "OK", 200

@app.route("/")
def index(): return "ALIVE", 200

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ptb_app.initialize())
    ptb_app.bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=PORT)
