import os
import telebot
from telebot import types
from flask import Flask
import openai
import requests
import threading

# --- CONFIGURATION ---
TOKEN = os.getenv('BOT_TOKEN')
HF_TOKEN = os.getenv('HF_TOKEN')
ADMIN_ID = 12345678  # <--- CHANGE THIS TO YOUR TELEGRAM ID

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- IN-MEMORY DATABASE ---
# Note: On Render, these reset if the bot restarts. 
# For permanent storage, connect a database like MongoDB.
bot_config = {
    "openai_key": os.getenv('OPENAI_API_KEY', ""),
    "hf_token": os.getenv('HF_TOKEN', ""),
    "active_model": "gpt-3.5-turbo",
    "model_list": ["gpt-3.5-turbo", "gpt-4", "facebook/blenderbot-400M-distill"] 
}

# --- FLASK SERVER ---
@app.route('/')
def home(): return "Bot is Running"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- ADMIN PANEL ---
@bot.message_handler(commands=['admin'])
def admin_menu(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ Access Denied.")
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➕ Add New Model", callback_data="add_model"),
        types.InlineKeyboardButton("🔄 Switch Model", callback_data="switch_model"),
        types.InlineKeyboardButton("🔑 Update Tokens", callback_data="update_tokens"),
        types.InlineKeyboardButton("📊 Current Status", callback_data="status")
    )
    bot.send_message(message.chat.id, "🛠 **Admin Control Panel**", reply_markup=markup, parse_mode="Markdown")

# --- CALLBACK HANDLER ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "Not authorized")

    if call.data == "add_model":
        msg = bot.send_message(call.message.chat.id, "Type the Model Name exactly (e.g., `gpt-4-0613` or `mistralai/Mistral-7B-v0.1`):")
        bot.register_next_step_handler(msg, save_new_model)

    elif call.data == "switch_model":
        markup = types.InlineKeyboardMarkup()
        for model in bot_config["model_list"]:
            markup.add(types.InlineKeyboardButton(model, callback_data=f"select_{model}"))
        bot.send_message(call.message.chat.id, "Select the model to set as Active:", reply_markup=markup)

    elif call.data.startswith("select_"):
        selected = call.data.replace("select_", "")
        bot_config["active_model"] = selected
        bot.answer_callback_query(call.id, f"Active Model: {selected}")
        bot.send_message(call.message.chat.id, f"✅ **Active model changed to:** `{selected}`", parse_mode="Markdown")

    elif call.data == "update_tokens":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Update OpenAI Key", callback_data="up_oa"),
                   types.InlineKeyboardButton("Update HF Token", callback_data="up_hf"))
        bot.send_message(call.message.chat.id, "Which token do you want to update?", reply_markup=markup)

    elif call.data == "up_oa":
        msg = bot.send_message(call.message.chat.id, "Send your new OpenAI API Key:")
        bot.register_next_step_handler(msg, lambda m: update_token(m, "openai_key"))

    elif call.data == "status":
        status_msg = (
            f"🤖 **Bot Status**\n\n"
            f"📍 **Active Model:** `{bot_config['active_model']}`\n"
            f"🔑 **OpenAI Key:** {'Set ✅' if bot_config['openai_key'] else 'Not Set ❌'}\n"
            f"🔑 **HF Token:** {'Set ✅' if bot_config['hf_token'] else 'Not Set ❌'}\n"
            f"📚 **Available Models:** {len(bot_config['model_list'])}"
        )
        bot.send_message(call.message.chat.id, status_msg, parse_mode="Markdown")

# --- STEP HANDLERS ---
def save_new_model(message):
    model_name = message.text.strip()
    if model_name not in bot_config["model_list"]:
        bot_config["model_list"].append(model_name)
        bot.reply_to(message, f"✅ Added `{model_name}` to your list.", parse_mode="Markdown")
    else:
        bot.reply_to(message, "Model already exists in list.")

def update_token(message, key_type):
    bot_config[key_type] = message.text.strip()
    bot.reply_to(message, f"✅ {key_type} updated successfully!")

# --- AI LOGIC (SWITCHING BETWEEN OPENAI & HF) ---
def get_ai_response(prompt):
    model = bot_config["active_model"]
    
    # Logic for OpenAI
    if "gpt" in model.lower():
        if not bot_config["openai_key"]: return "❌ OpenAI Key is missing!"
        openai.api_key = bot_config["openai_key"]
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    # Logic for Hugging Face
    else:
        if not bot_config["hf_token"]: return "❌ HF Token is missing!"
        API_URL = f"https://api-inference.huggingface.co/models/{model}"
        headers = {"Authorization": f"Bearer {bot_config['hf_token']}"}
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
        try:
            return response.json()[0]['generated_text']
        except:
            return "⚠️ Error: The Hugging Face model might be loading or the name is incorrect."

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # Only respond to text (not stickers) unless it's a private chat
    if message.chat.type == "private":
        loading = bot.reply_to(message, "🔍 Thinking...")
        answer = get_ai_response(message.text)
        bot.edit_message_text(answer, message.chat.id, loading.message_id)

# --- START BOT ---
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()
