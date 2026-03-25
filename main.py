import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
from openai import OpenAI
import time
import logging

# Set up logging to see errors in Render logs
logging.basicConfig(level=logging.INFO)

# --- 1. CONFIGURATION ---
# IMPORTANT: Make sure these names match exactly in Render Environment Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
STICKER_ID = "CAACAgIAAxkBAAM1acJAy74JHRwQ2l2fFq1r-hVjcPYAAvUAA_cCyA9HRphh0VDIsR4E"

# --- 2. MODELS LIST ---
# Note: google/gemini-3 and gpt-5 do not exist yet. 
# I am including them as you requested, but they may return errors when used.
AVAILABLE_MODELS = {
    "Gemini 3 Pro (Preview)": "google/gemini-3-pro-image-preview",
    "Gemini 2.5 Pro": "google/gemini-2.5-pro",
    "GPT-4o Mini": "openai/gpt-4o-mini",
    "GPT-5.4 Mini": "openai/gpt-5.4-mini",
    "DeepSeek V3": "deepseek/deepseek-chat"
}

current_model = "openai/gpt-4o-mini"

# --- 3. INITIALIZATION ---
try:
    bot = telebot.TeleBot(BOT_TOKEN)
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
except Exception as e:
    print(f"CRITICAL ERROR during init: {e}")

app = Flask(__name__)

# --- 4. FLASK SERVER ---
@app.route('/')
def home():
    return "Flixora GPT is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 5. BOT LOGIC ---
@bot.message_handler(commands=['model'])
def switch_model(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for name in AVAILABLE_MODELS.keys():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"select_{name}"))
    bot.send_message(message.chat.id, "🤖 *Select a Model:*", reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith('select_'))
def handle_selection(call):
    global current_model
    display_name = call.data.split('_')[1]
    current_model = AVAILABLE_MODELS[display_name]
    bot.answer_callback_query(call.id, f"Switched to {display_name}")
    bot.edit_message_text(f"✅ Model updated to: *{display_name}*", call.message.chat.id, call.message.message_id, parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Welcome! I am **Flixora GPT**.\nUse /model to switch AI models.", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    try:
        searching_msg = bot.send_message(message.chat.id, "🔍 *Flixora GPT is searching...*", parse_mode='Markdown')
        bot.send_sticker(message.chat.id, STICKER_ID)

        response = client.chat.completions.create(
            model=current_model,
            messages=[{"role": "user", "content": message.text}]
        )
        ai_answer = response.choices[0].message.content
        bot.reply_to(message, ai_answer, parse_mode='Markdown')
        bot.delete_message(message.chat.id, searching_msg.message_id)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ *Error:* {str(e)}")

# --- 6. STARTUP ---
if __name__ == "__main__":
    # Start web server
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print("🚀 Starting Flixora GPT...")
    
    # Infinite loop to keep the process alive even if polling fails
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True, timeout=60)
        except Exception as e:
            print(f"Main Loop Error: {e}")
            time.sleep(5) # Wait 5 seconds before restarting if it crashes
