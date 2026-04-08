import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder
import info

# Handlers Imports
from start import start_handler, callback_handler
from plugins.auth import auth_handler
from plugins.ai_chat import chat_handler
from plugins.admin import admin_handlers

# Flask App for Webhook
app = Flask(__name__)

# PTB App
ptb_app = ApplicationBuilder().token(info.BOT_TOKEN).build()

# Register Handlers
ptb_app.add_handler(start_handler)
ptb_app.add_handler(auth_handler)
for h in admin_handlers: ptb_app.add_handler(h)
ptb_app.add_handler(chat_handler) # AI chat last me

@app.route(f"/{info.BOT_TOKEN}", methods=['POST'])
async def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), ptb_app.bot)
        await ptb_app.process_update(update)
        return "OK", 200

@app.route("/")
def index():
    return "<h1>FLIXORA AI IS ALIVE 🤖</h1>", 200

if __name__ == "__main__":
    # Start Webhook
    import asyncio
    asyncio.get_event_loop().run_until_complete(ptb_app.initialize())
    ptb_app.bot.set_webhook(url=f"{info.WEBHOOK_URL}/{info.BOT_TOKEN}")
    
    app.run(host="0.0.0.0", port=info.PORT)
