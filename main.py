import os
import telebot
from telebot import types
from flask import Flask
import openai
import requests
import threading

# --- CONFIGURATION ---
TOKEN = os.getenv('BOT_TOKEN')
HF_TOKEN = os.getenv('HF_TOKEN') # Hugging Face Token
ADMIN_ID = 12345678  # REPLACE WITH YOUR NUMERIC TELEGRAM ID
DEFAULT_MODEL = "gpt-3.5-turbo"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Temporary storage (Note: Render disk is ephemeral, data resets on restart)
user_data = {}
bot_settings = {
    "current_model": DEFAULT_MODEL,
    "openai_key": os.getenv('OPENAI_API_KEY')
}

# --- FLASK SERVER FOR RENDER ---
@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- HELPER FUNCTIONS ---
def shorten_url(long_url):
    try:
        res = requests.get(f"http://tinyurl.com/api-create.php?url={long_url}")
        return res.text
    except:
        return "Error shortening URL."

# --- WELCOME & START ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("➕ Add to Group", url=f"http://t.me/{bot.get_me().username}?startgroup=true")
    btn2 = types.InlineKeyboardButton("💎 Premium", callback_data="premium")
    btn3 = types.InlineKeyboardButton("ℹ️ About", callback_data="about")
    btn4 = types.InlineKeyboardButton("👨‍💻 Admin", url="https://t.me/YourAdminUsername")
    btn5 = types.InlineKeyboardButton("📢 More Channels", url="https://t.me/YourChannel")
    
    markup.add(btn1, btn2, btn3, btn4, btn5)
    
    welcome_text = (
        f"Hello {message.from_user.first_name}!\n\n"
        "I am an AI Powered Bot.\n"
        "✨ **Commands:**\n"
        "/shorten [url] - Shorten a link\n"
        "/sticker [query] - Search stickers\n"
        "/model - Change AI Model\n\n"
        "Send me any message to chat!"
    )
    bot.reply_to(message, welcome_text, reply_markup=markup, parse_mode="Markdown")

# --- ADMIN COMMANDS ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "❌ Access Denied.")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Update OpenAI Key", callback_data="set_key"))
    markup.add(types.InlineKeyboardButton("Change Global Model", callback_data="set_model"))
    bot.send_message(message.chat.id, "🛠 **Admin Panel**", reply_markup=markup)

# --- URL SHORTENER ---
@bot.message_handler(commands=['shorten'])
def handle_shorten(message):
    url = message.text.split(maxsplit=1)
    if len(url) < 2:
        return bot.reply_to(message, "Usage: /shorten https://example.com")
    short = shorten_url(url[1])
    bot.reply_to(message, f"🔗 Shortened Link: {short}")

# --- STICKER SEARCH ---
@bot.message_handler(commands=['sticker'])
def search_sticker(message):
    query = message.text.split(maxsplit=1)
    if len(query) < 2:
        return bot.reply_to(message, "Usage: /sticker [name]")
    bot.reply_to(message, f"🔍 Searching for stickers related to: {query[1]}... (Feature requires Sticker Set API)")

# --- CHATGPT LOGIC ---
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.chat.type != 'private' and not message.text.startswith('/'):
        if not bot.get_me().username in message.text:
            return # Only reply in groups if mentioned

    try:
        openai.api_key = bot_settings['openai_key']
        response = openai.ChatCompletion.create(
            model=bot_settings['current_model'],
            messages=[{"role": "user", "content": message.text}]
        )
        bot.reply_to(message, response.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, "⚠️ AI Error: Ensure Admin has configured the API Key.")

# --- CALLBACK HANDLERS ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "about":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "This bot is created using pyTelegramBotAPI and hosted on Render.")
    elif call.data == "premium":
        bot.send_message(call.message.chat.id, "🌟 **Premium Features:**\n- Faster response\n- No limits\n- GPT-4 Access\nContact @Admin for pricing.")
    elif call.data == "set_model":
        if call.from_user.id == ADMIN_ID:
            bot.send_message(call.message.chat.id, "Send the model name (e.g., gpt-4 or gpt-3.5-turbo)")
            bot.register_next_step_handler(call.message, update_model)

def update_model(message):
    bot_settings['current_model'] = message.text
    bot.reply_to(message, f"✅ Model updated to {message.text}")

if __name__ == "__main__":
    # Start Flask in a separate thread
    threading.Thread(target=run_flask).start()
    # Start Bot polling
    bot.infinity_polling()
