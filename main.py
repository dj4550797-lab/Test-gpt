import os
import telebot
from telebot import types
from flask import Flask
from openai import OpenAI
import requests
import threading

# --- CONFIGURATION ---
TOKEN = os.getenv('BOT_TOKEN')
HF_TOKEN = os.getenv('HF_TOKEN')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
ADMIN_ID = 12345678  # <--- Change to your Telegram ID

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Initialize OpenAI Client (New Version 1.0+)
client = OpenAI(api_key=OPENAI_KEY)

# --- WEB SERVER FOR RENDER ---
@app.route('/')
def health_check():
    return "Bot is alive!", 200

def run_flask():
    # Render provides a PORT environment variable. We must use it.
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- BOT LOGIC ---

@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("➕ Add to Group", url=f"http://t.me/{bot.get_me().username}?startgroup=true")
    btn2 = types.InlineKeyboardButton("ℹ️ About", callback_data="about")
    markup.add(btn1, btn2)
    
    bot.reply_to(message, "👋 Hello! I am your AI Assistant. Send me a message to start chatting!", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_ai(message):
    # Don't reply to other bots
    if message.from_user.is_bot:
        return

    # Show "typing..." action
    bot.send_chat_action(message.chat.id, 'typing')

    try:
        # OpenAI API Call (Updated Syntax)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message.text}]
        )
        answer = response.choices[0].message.content
        bot.reply_to(message, answer)
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "❌ AI Error. Please check if the Admin has set the API Key correctly.")

# --- STARTUP ---
if __name__ == "__main__":
    # 1. Start Flask in background
    threading.Thread(target=run_flask).start()
    print("Flask server started.")
    
    # 2. Start Bot Polling
    print("Bot is polling...")
    bot.infinity_polling()
