import os
import telebot
from flask import Flask
from threading import Thread
from openai import OpenAI

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
# You can change this to any OpenRouter model (e.g., "google/gemini-2.0-flash-001" or "deepseek/deepseek-r1")
MODEL_NAME = "deepseek/deepseek-chat" 
STICKER_ID = "CAACAgIAAxkBAAM1acJAy74JHRwQ2l2fFq1r-hVjcPYAAvUAA_cCyA9HRphh0VDIsR4E"

# Initialize OpenRouter Client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    default_headers={
        "HTTP-Referer": "https://render.com", # Optional, for OpenRouter rankings
        "X-Title": "Flixora GPT",             # Optional
    }
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

# --- BOT LOGIC ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! I am **Flixora GPT**. Send me a message to start chatting!", parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    try:
        # 1. Send the "Searching" text
        searching_msg = bot.send_message(message.chat.id, "🔍 *Flixora GPT is searching...*", parse_mode='Markdown')
        
        # 2. Send the specific Sticker
        bot.send_sticker(message.chat.id, STICKER_ID)

        # 3. Get response from OpenRouter
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are Flixora GPT, a helpful and professional AI assistant."},
                {"role": "user", "content": message.text}
            ]
        )

        ai_answer = response.choices[0].message.content

        # 4. Send the final answer
        # We use Markdown to ensure the text is "perfectly written" with formatting
        bot.reply_to(message, ai_answer, parse_mode='Markdown')
        
        # Optional: Delete the "searching" message to keep chat clean
        # bot.delete_message(message.chat.id, searching_msg.message_id)

    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(message.chat.id, "❌ Sorry, I couldn't process that request.")

# --- STARTUP ---
if __name__ == "__main__":
    # Start Web Server
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Start Bot
    print("Flixora GPT Bot is running...")
    bot.infinity_polling()
