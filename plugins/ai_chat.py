import requests
import info
from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes
from script import script

async def get_ai_reply(text, model):
    # Try Hugging Face first if token exists
    if info.HF_TOKEN:
        try:
            API_URL = f"https://api-inference.huggingface.co/models/{model}"
            headers = {"Authorization": f"Bearer {info.HF_TOKEN}"}
            res = requests.post(API_URL, headers=headers, json={"inputs": text}, timeout=10)
            return res.json()[0]['generated_text']
        except:
            pass # Fallback to OpenRouter

    # OpenRouter Logic
    headers = {"Authorization": f"Bearer {info.OPENROUTER_API_KEY}"}
    data = {"model": model, "messages": [{"role": "user", "content": text}]}
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        return res.json()['choices'][0]['message']['content']
    except:
        return "❌ `System Error: AI core is currently unresponsive.`"

async def ai_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text: return
    
    status_msg = await update.message.reply_text(script.AI_THINKING, parse_mode="Markdown")
    
    # Get response
    model = info.MODELS["model_1"]
    reply = await get_ai_reply(update.message.text, model)
    
    await status_msg.edit_text(f"⚡ **FLIXORA:**\n\n{reply}", parse_mode="Markdown")

ai_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, ai_message_handler)
