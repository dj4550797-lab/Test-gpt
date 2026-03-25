import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
from openai import OpenAI
import time

# --- 1. CONFIGURATION ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
STICKER_ID = "CAACAgIAAxkBAAM1acJAy74JHRwQ2l2fFq1r-hVjcPYAAvUAA_cCyA9HRphh0VDIsR4E"

# --- 2. UPDATED MODELS (Guaranteed Correct OpenRouter IDs) ---
AVAILABLE_MODELS = {
    "Gemini 2.0 Flash (Free)": "google/gemini-2.0-flash-exp:free",
    "Llama 3.1 8B (Free)": "meta-llama/llama-3.1-8b-instruct:free",
    "Mistral 7B (Free)": "mistralai/mistral-7b-instruct:free",
    "Qwen 2 7B (Free)": "qwen/qwen-2-7b-instruct:free",
    "GPT-4o Mini (Paid)": "openai/gpt-4o-mini"
}

# Default to a Free model so it works with 0 credits
current_model = "google/gemini-2.0-flash-exp:free"

# --- 3. INITIALIZATION ---
bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

app = Flask(__name__)

@app.route('/')
def home():
    return "Flixora GPT is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 4. BOT COMMANDS ---

@bot.message_handler(commands=['model'])
def switch_model(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for name in AVAILABLE_MODELS.keys():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"select_{name}"))
    bot.send_message(message.chat.id, "🤖 *Select a Model for Flixora GPT:*", reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith('select_'))
def handle_selection(call):
    global current_model
    display_name = call.data.split('_')[1]
    current_model = AVAILABLE_MODELS[display_name]
    bot.answer_callback_query(call.id, f"Switched to {display_name}")
    bot.edit_message_text(f"✅ Model updated to: *{display_name}*", call.message.chat.id, call.message.message_id, parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Welcome to **Flixora GPT**!\nI can chat using various AI models. Use /model to switch.", parse_mode='Markdown')

# --- 5. MAIN CHAT LOGIC ---

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    try:
        # 1. Send Searching Status
        searching_msg = bot.send_message(message.chat.id, "🔍 *Flixora GPT is searching...*", parse_mode='Markdown')
        
        # 2. Send the Sticker
        bot.send_sticker(message.chat.id, STICKER_ID)

        # 3. Request from OpenRouter
        # max_tokens=1000 ensures it doesn't fail due to low credits
        response = client.chat.completions.create(
            model=current_model,
            messages=[
                {"role": "system", "content": "You are Flixora GPT. Provide clear, perfectly formatted answers."},
                {"role": "user", "content": message.text}
            ],
            max_tokens=1000
        )
        
        ai_answer = response.choices[0].message.content

        # 4. Reply with AI Answer
        # Use a safe way to send Markdown; if it fails, send as plain text
        try:
            bot.reply_to(message, ai_answer, parse_mode='Markdown')
        except:
            bot.reply_to(message, ai_answer) # Plain text fallback
        
        # 5. Delete "Searching" message
        bot.delete_message(message.chat.id, searching_msg.message_id)
        
    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(message.chat.id, f"❌ *Error:* {str(e)}", parse_mode='Markdown')

# --- 6. STARTUP ---
if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print(f"🚀 Flixora GPT started with: {current_model}")
    
    while True:
        try:
            bot.remove_webhook()
            bot.infinity_polling(skip_pending=True, timeout=60)
        except Exception as e:
            print(f"Restarting polling due to: {e}")
            time.sleep(5)
