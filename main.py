import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
from openai import OpenAI

# --- 1. CONFIGURATION ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
STICKER_ID = "CAACAgIAAxkBAAM1acJAy74JHRwQ2l2fFq1r-hVjcPYAAvUAA_cCyA9HRphh0VDIsR4E"

# --- 2. UPDATED MODELS LIST ---
AVAILABLE_MODELS = {
    "Gemini 3 Pro (Preview)": "google/gemini-3-pro-image-preview",
    "Gemini 2.5 Pro": "google/gemini-2.5-pro",
    "GPT-4o Mini": "openai/gpt-4o-mini",
    "GPT-5.4 Mini": "openai/gpt-5.4-mini",
    "DeepSeek V3": "deepseek/deepseek-chat"
}

# Set default model
current_model = "openai/gpt-4o-mini"

# --- 3. INITIALIZE CLIENTS ---
bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

app = Flask(__name__)

# --- 4. FLASK SERVER (For Render Health Check) ---
@app.route('/')
def home():
    return "Flixora GPT is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 5. BOT COMMANDS ---

@bot.message_handler(commands=['model'])
def switch_model(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for name in AVAILABLE_MODELS.keys():
        button = types.InlineKeyboardButton(name, callback_data=f"select_{name}")
        markup.add(button)
    
    bot.send_message(
        message.chat.id, 
        "🤖 *Select a Model for Flixora GPT:*", 
        reply_markup=markup, 
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('select_'))
def handle_model_selection(call):
    global current_model
    display_name = call.data.split('_')[1]
    current_model = AVAILABLE_MODELS[display_name]
    
    bot.answer_callback_query(call.id, f"Switched to {display_name}")
    bot.edit_message_text(
        f"✅ Model updated to: *{display_name}*", 
        call.message.chat.id, 
        call.message.message_id, 
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Welcome! I am **Flixora GPT**.\n\nUse /model to switch between Gemini, GPT, and DeepSeek.", parse_mode='Markdown')

# --- 6. MAIN CHAT LOGIC ---

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    try:
        # 1. Show "Searching" status
        searching_msg = bot.send_message(message.chat.id, "🔍 *Flixora GPT is searching...*", parse_mode='Markdown')
        
        # 2. Show the specific Sticker
        bot.send_sticker(message.chat.id, STICKER_ID)

        # 3. Request completion
        response = client.chat.completions.create(
            model=current_model,
            messages=[
                {"role": "system", "content": "You are Flixora GPT, a professional AI. Provide perfectly formatted answers using Markdown."},
                {"role": "user", "content": message.text}
            ]
        )

        ai_answer = response.choices[0].message.content

        # 4. Reply with the formatted answer
        bot.reply_to(message, ai_answer, parse_mode='Markdown')
        
        # 5. Delete "Searching" text
        bot.delete_message(message.chat.id, searching_msg.message_id)

    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(message.chat.id, "❌ *Error:* Model is unavailable or API key is incorrect. Try switching models with /model.")

# --- 7. STARTUP LOGIC ---
if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print(f"🚀 Flixora GPT running on model: {current_model}")
    
    try:
        bot.remove_webhook()
        # skip_pending=True ignores messages sent while the bot was offline
        bot.infinity_polling(skip_pending=True, timeout=60)
    except Exception as e:
        print(f"Polling conflict error: {e}")
