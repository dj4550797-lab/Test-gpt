from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder
import info
import asyncio

# Import Handlers
from plugins.start import start_handler
from plugins.ai_chat import ai_handler

app = Flask(__name__)
ptb_app = ApplicationBuilder().token(info.BOT_TOKEN).build()

# Add Handlers
ptb_app.add_handler(start_handler)
ptb_app.add_handler(ai_handler)

@app.route(f"/{info.BOT_TOKEN}", methods=['POST'])
async def webhook():
    update = Update.de_json(request.get_json(force=True), ptb_app.bot)
    await ptb_app.process_update(update)
    return "OK", 200

@app.route("/")
def health_check():
    return "Bot is Running!", 200

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ptb_app.initialize())
    ptb_app.bot.set_webhook(url=f"{info.WEBHOOK_URL}/{info.BOT_TOKEN}")
    app.run(host="0.0.0.0", port=10000)
