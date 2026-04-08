import os
import telebot
from telebot import types
from flask import Flask
from openai import OpenAI
import threading

# --- CONFIGURATION ---
TOKEN = os.getenv('BOT_TOKEN')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
ADMIN_ID = 12345678  # Replace with your actual Telegram ID

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- WEB SERVER FOR RENDER ---
@app.route('/')
def health_check():
    return "Bot is active", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- COMMANDS ---

@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("➕ Add to Group", url=f"http://t.me/{bot.get_me().username}?startgroup=true")
    btn2 = types.InlineKeyboardButton("👨‍💻 Admin", url="https://t.me/YourUsername")
    btn3 = types.InlineKeyboardButton("📢 Channel", url="https://t.me/YourChannel")
    markup.add(btn1, btn2, btn3)
    
    welcome_text = (
        f"👋 Welcome {message.from_user.first_name}!\n\n"
        "I am **GPT Flixora**, your AI assistant.\n\n"
        "✨ **How to use:**\n"
        "Just send me a message and I will reply using AI.\n\n"
        "🛠 **Admin Commands:** /admin (Admin only)"
    )
    bot.reply_to(message, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        bot.reply_to(message, "❌ You are not authorized.")
        return
    bot.reply_to(message, "✅ Welcome Admin. Tokens are managed via Render Dashboard.")

# --- CHAT LOGIC ---

@bot.message_handler(func=lambda message: True)
def handle_ai(message):
    if not OPENAI_KEY:
        bot.reply_to(message, "❌ OpenAI Key is missing in Render Environment Variables!")
        return

    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message.text}]
        )
        bot.reply_to(message, response.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

# --- START ---
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("Bot is starting...")
    bot.infinity_polling()
