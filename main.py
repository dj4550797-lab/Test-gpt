import os
import telebot
from telebot import types
from flask import Flask
from openai import OpenAI
import threading
import time

# --- CONFIGURATION ---
TOKEN = os.getenv('BOT_TOKEN')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')

# ❗ APNA ID YAHAN DAALEIN (Userinfo bot se mil jayega)
ADMIN_ID = 123456789 

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- RENDER PORT FIX ---
@app.route('/')
def home():
    return "Bot is Running Safe and Sound!"

def run_flask():
    # Render ke liye port bind karna zaroori hai
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- START COMMAND ---
@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("➕ Add to Group", url=f"http://t.me/{bot.get_me().username}?startgroup=true")
    markup.add(btn)
    bot.reply_to(message, "✅ GPT Flixora is Online!\nMessage bhejein AI se baat karne ke liye.", reply_markup=markup)

# --- CHAT LOGIC ---
@bot.message_handler(func=lambda message: True)
def ai_reply(message):
    if not OPENAI_KEY:
        bot.reply_to(message, "❌ OpenAI Key missing in Render settings!")
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
        bot.reply_to(message, f"⚠️ AI Error: {str(e)}")

# --- BOT RUNNING LOGIC ---
if __name__ == "__main__":
    # Flask ko alag thread mein chalayein
    threading.Thread(target=run_flask).start()
    
    # 409 Conflict fix karne ke liye 5 second ka wait
    print("Waiting for old sessions to clear...")
    time.sleep(5)
    
    print("Bot is starting...")
    # skip_pending=True se purane messages ignore honge
    bot.infinity_polling(skip_pending=True)
