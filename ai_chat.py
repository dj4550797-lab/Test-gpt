import requests
import asyncio
import info
from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes
from database import db_client
from utils.helpers import verify_access, check_rate_limit
from script import script

async def get_ai_response(messages, model):
    # Agar model HuggingFace ka hai (Example: meta-llama/...)
    if info.HF_TOKEN and ("llama" in model.lower() or "mistral" in model.lower()):
        API_URL = f"https://api-inference.huggingface.co/models/{model}"
        headers = {"Authorization": f"Bearer {info.HF_TOKEN}"}
        prompt = messages[-1]['content']
        try:
            response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
            return response.json()[0]['generated_text']
        except:
            pass # Fallback to OpenRouter

    # OpenRouter Logic
    headers = {
        "Authorization": f"Bearer {info.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {"model": model, "messages": messages}
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"❌ Error: {str(e)}"

async def handle_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await verify_access(update, context): return
    
    status = await update.message.reply_text(script.AI_THINKING, parse_mode="Markdown")
    
    user = db_client.get_user(user_id)
    model = user.get("selected_model", info.MODELS["model_1"])
    
    # Simple history
    history = context.user_data.get('history', [])
    history.append({"role": "user", "content": update.message.text})
    
    response = await get_ai_response(history[-5:], model)
    
    await status.edit_text(f"✨ **JARVIS:**\n\n{response}", parse_mode="Markdown")
    history.append({"role": "assistant", "content": response})
    context.user_data['history'] = history[-10:]

chat_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_chat)
