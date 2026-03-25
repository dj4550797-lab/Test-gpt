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

# --- 2. MODELS (Using Free Models to avoid 402 errors) ---
AVAILABLE_MODELS = {
    "Gemini 2.0 Flash Lite (Free)": "google/gemini-2.0-flash-lite-preview-02-05:free",
    "Llama 3.1 8B (Free)": "meta-llama/llama-3.1-8b-instruct:free",
    "Mistral 7B (Free)": "mistralai/mistral-7b-instruct:free",
    "GPT-4o Mini": "openai/gpt-4o-mini"
}

current_model = "google/gemini-2.0-flash-lite-preview-02-05:free"

# --- 3. INITIALIZATION ---
bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 4. BOT LOGIC ---

@bot.message_handler(commands=['model'])
def switch_model(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for name in AVAILABLE_MODELS.keys():
        markup.add(types.InlineKeyboardButton(name, callback_data=f"select_{name}"))
    bot.send_message(message.chat.id, "🤖 Select an AI model:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('select_'))
def handle_selection(call):
    global current_model
    display_name = call.data.split('_')[1]
    current_model = AVAILABLE_MODELS[display_name]
    bot.edit_message_text(f"✅ Switched to: {display_name}", call.message.chat.id, call.message.message_id)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 I am Flixora GPT! Send me a message.")

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    print(f"📩 New Message from {message.from_user.first_name}: {message.text}")
    
    # 1. Send Searching Status
    searching_msg = bot.send_message(message.chat.id, "🔍 Flixora GPT is searching...")
    
    try:
        # 2. Send Sticker
        bot.send_sticker(message.chat.id, STICKER_ID)

        # 3. Request from OpenRouter
        print(f"🤖 Calling OpenRouter with model: {current_model}")
        response = client.chat.completions.create(
            model=current_model,
            messages=[{"role": "user", "content": message.text}],
            max_tokens=500 
        )
        
        ai_answer = response.choices[0].message.content
        print(f"✅ AI Response Received: {ai_answer[:50]}...")

        # 4. Reply (Removing Markdown formatting for now to ensure it sends)
        bot.reply_to(message, ai_answer)
        
        # 5. Delete "Searching" message
        bot.delete_message(message.chat.id, searching_msg.message_id)
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, searching_msg.message_id)

# --- 5. STARTUP ---
if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print("🚀 Bot process started...")
    
    while True:
        try:
            bot.remove_webhook()
            # Bot waits for messages
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Polling crashed, restarting... Error: {e}")
            time.sleep(5)
