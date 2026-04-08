import os
import telebot
from telebot import types
from flask import Flask
from openai import OpenAI
import requests
import threading

# --- CONFIGURATION ---
# These are pulled from Render Environment Variables
TOKEN = os.getenv('BOT_TOKEN')
HF_TOKEN = os.getenv('HF_TOKEN')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
ADMIN_ID = 12345678  # <--- REPLACE with your real Telegram ID (use @userinfobot)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- IN-MEMORY DATABASE ---
bot_settings = {
    "active_model": "gpt-3.5-turbo",
    "available_models": ["gpt-3.5-turbo", "gpt-4", "mistralai/Mistral-7B-v0.1"],
    "openai_key": OPENAI_KEY,
    "hf_token": HF_TOKEN
}

# --- FLASK SERVER FOR RENDER ---
@app.route('/')
def health():
    return "Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- HELPER: URL SHORTENER ---
def shorten_url(url):
    try:
        res = requests.get(f"http://tinyurl.com/api-create.php?url={url}")
        return res.text if res.status_code == 200 else "Error"
    except:
        return "Error"

# --- COMMAND: START ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("➕ Add to Group", url=f"http://t.me/{bot.get_me().username}?startgroup=true")
    btn2 = types.InlineKeyboardButton("🤖 Select Model", callback_data="select_model")
    btn3 = types.InlineKeyboardButton("💎 Premium", callback_data="premium")
    btn4 = types.InlineKeyboardButton("ℹ️ About", callback_data="about")
    btn5 = types.InlineKeyboardButton("📢 More Channels", url="https://t.me/YourChannel")
    btn6 = types.InlineKeyboardButton("👨‍💻 Contact Admin", url="https://t.me/YourAdminUsername")
    
    markup.add(btn1)
    markup.add(btn2, btn3)
    markup.add(btn4, btn5, btn6)

    welcome_text = (
        f"👋 Hello {message.from_user.first_name}!\n\n"
        "Welcome to **GPT Flixora**. I am an AI Bot with multiple models.\n\n"
        "📜 **Commands:**\n"
        "👉 /shorten [url] - Shorten any link\n"
        "👉 /sticker [query] - Sticker search\n"
        "👉 /admin - Admin settings\n\n"
        "💬 Send me any text to chat!"
    )
    bot.reply_to(message, welcome_text, reply_markup=markup, parse_mode="Markdown")

# --- COMMAND: ADMIN ---
@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return bot.reply_to(message, "❌ Access Denied.")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Add New Model", callback_data="admin_add_model"))
    markup.add(types.InlineKeyboardButton("🔑 Update OpenAI Key", callback_data="admin_set_key"))
    bot.send_message(message.chat.id, "🛠 **Admin Panel**\nManage your AI configuration here.", reply_markup=markup, parse_mode="Markdown")

# --- COMMAND: URL SHORTENER ---
@bot.message_handler(commands=['shorten'])
def url_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "❌ Usage: `/shorten https://google.com`", parse_mode="Markdown")
    short = shorten_url(args[1])
    bot.reply_to(message, f"✅ **Short Link:** {short}", parse_mode="Markdown")

# --- CALLBACK HANDLERS ---
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    if call.data == "about":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🤖 **GPT Flixora**\nVersion: 2.0\nHosted on: Render.com\nPowered by: OpenAI & Hugging Face")
    
    elif call.data == "premium":
        bot.send_message(call.message.chat.id, "🌟 **Premium Access**\n- GPT-4 Unlocked\n- No Limits\n- Image Generation\n\nContact @YourAdminUsername to upgrade.")

    elif call.data == "select_model":
        markup = types.InlineKeyboardMarkup()
        for m in bot_settings["available_models"]:
            markup.add(types.InlineKeyboardButton(m, callback_data=f"setmod_{m}"))
        bot.edit_message_text("Choose an AI Model:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("setmod_"):
        new_mod = call.data.split("_")[1]
        bot_settings["active_model"] = new_mod
        bot.answer_callback_query(call.id, f"Model set to {new_mod}")
        bot.send_message(call.message.chat.id, f"✅ Model switched to: `{new_mod}`", parse_mode="Markdown")

    # Admin actions
    elif call.data == "admin_add_model":
        msg = bot.send_message(call.message.chat.id, "Enter the model ID (e.g. `gpt-4` or `mistralai/Mistral-7B`):")
        bot.register_next_step_handler(msg, process_add_model)

def process_add_model(message):
    bot_settings["available_models"].append(message.text)
    bot.reply_to(message, f"✅ Added {message.text} to model list.")

# --- AI CHAT LOGIC ---
@bot.message_handler(func=lambda message: True)
def ai_chat(message):
    if message.from_user.is_bot: return
    
    # Check if we use OpenAI or HuggingFace
    model = bot_settings["active_model"]
    bot.send_chat_action(message.chat.id, 'typing')

    try:
        if "gpt" in model.lower():
            if not bot_settings["openai_key"]:
                return bot.reply_to(message, "❌ OpenAI Key missing!")
            client = OpenAI(api_key=bot_settings["openai_key"])
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": message.text}]
            )
            bot.reply_to(message, response.choices[0].message.content)
        else:
            # Hugging Face Logic
            if not bot_settings["hf_token"]:
                return bot.reply_to(message, "❌ HF Token missing!")
            api_url = f"https://api-inference.huggingface.co/models/{model}"
            headers = {"Authorization": f"Bearer {bot_settings['hf_token']}"}
            res = requests.post(api_url, headers=headers, json={"inputs": message.text})
            bot.reply_to(message, res.json()[0]['generated_text'])
    except Exception as e:
        bot.reply_to(message, "⚠️ Error connecting to AI. Check tokens or model name.")

# --- START ---
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling(skip_pending=True)
