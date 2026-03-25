import os
import telebot
from telebot import types
from flask import Flask
from threading import Thread
from openai import OpenAI

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
STICKER_ID = "CAACAgIAAxkBAAM1acJAy74JHRwQ2l2fFq1r-hVjcPYAAvUAA_cCyA9HRphh0VDIsR4E"

# 1. ADD MODELS HERE
# Format: "Display Name": "OpenRouter Model ID"
AVAILABLE_MODELS = {
    "DeepSeek V3": "deepseek/deepseek-chat",
    "DeepSeek R1": "deepseek/deepseek-r1",
    "Gemini Flash 2.0": "google/gemini-2.0-flash-001",
    "GPT-4o Mini": "openai/gpt-4o-mini"
}

# Default model
current_model = "deepseek/deepseek-chat"

# Initialize OpenRouter Client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- FLASK FOR RENDER ---
@app.route('/')
def home():
    return "Flixora GPT is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- COMMAND: CHANGE MODEL ---
@bot.message_handler(commands=['model'])
def switch_model(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for name in AVAILABLE_MODELS.keys():
        button = types.InlineKeyboardButton(name, callback_data=f"select_{name}")
        markup.add(button)
    
    bot.send_message(message.chat.id, "🤖 *Select a Model for Flixora GPT:*", 
                     reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith('select_'))
def callback_reponse(call):
    global current_model
    model_display_name = call.data.split('_')[1]
    current_model = AVAILABLE_MODELS[model_display_name]
    
    bot.answer_callback_query(call.id, f"Switched to {model_display_name}")
    bot.edit_message_text(f"✅ Model updated to: *{model_display_name}*", 
                          call.message.chat.id, call.message.message_id, parse_mode='Markdown')

# --- MAIN CHAT LOGIC ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Welcome! I am **Flixora GPT**.\n\nUse /model to change AI settings.", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    try:
        # 1. Send the "Searching" text
        searching_msg = bot.send_message(message.chat.id, "🔍 *Flixora GPT is searching...*", parse_mode='Markdown')
        
        # 2. Send the specific Sticker
        bot.send_sticker(message.chat.id, STICKER_ID)

        # 3. Get response from OpenRouter
        response = client.chat.completions.create(
            model=current_model,
            messages=[
                {"role": "system", "content": "You are Flixora GPT, a helpful assistant. Use clear formatting and Markdown."},
                {"role": "user", "content": message.text}
            ]
        )

        ai_answer = response.choices[0].message.content

        # 4. Final Answer
        # Using reply_to ensures the user knows which question is being answered
        bot.reply_to(message, ai_answer, parse_mode='Markdown')
        
        # Clean up: Delete the "searching" text message to keep the chat tidy
        bot.delete_message(message.chat.id, searching_msg.message_id)

    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(message.chat.id, "❌ Error connecting to the model. Try switching models with /model")

# --- STARTUP ---
if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    print(f"Flixora GPT Bot started with model: {current_model}")
    bot.infinity_polling()
