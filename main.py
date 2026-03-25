import os
import telebot
from flask import Flask
from threading import Thread
from openai import OpenAI

# 1. Setup Environment Variables
# These will be pulled from Render's Environment Variables dashboard
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')

# 2. Initialize Clients
bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

# 3. Flask Server for Render
# Render requires a web server to be running to stay alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    # Render provides a PORT environment variable automatically
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 4. Telegram Bot Logic
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hello! I am powered by DeepSeek via Hugging Face. Ask me anything!")

@bot.message_handler(func=lambda message: True)
def chat_with_ai(message):
    try:
        # Show "typing..." status in Telegram
        bot.send_chat_action(message.chat.id, 'typing')

        # Call Hugging Face Router
        chat_completion = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3", # Using the DeepSeek model
            messages=[
                {"role": "user", "content": message.text}
            ],
            max_tokens=500
        )

        # Get response content
        ai_response = chat_completion.choices[0].message.content
        bot.reply_to(message, ai_response)

    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Sorry, I encountered an error processing that request.")

# 5. Execution
if __name__ == "__main__":
    # Start Flask in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Start Telegram Bot Polling
    print("Bot is starting...")
    bot.infinity_polling()
