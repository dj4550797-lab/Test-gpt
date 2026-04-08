from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CommandHandler
import info
from script import script

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Check status for text (Premium or Free)
    # (Assuming you have a function to check user status from DB)
    status = "Premium 💎" if False else "Free Tier ⚡" # Placeholder logic
    
    keyboard = [
        [
            InlineKeyboardButton("➕ ADD ME TO YOUR GROUP ➕", url=f"https://t.me/{info.BOT_USERNAME}?startgroup=true")
        ],
        [
            InlineKeyboardButton("🚀 HELP", callback_data="help_menu"),
            InlineKeyboardButton("🛰 ABOUT", callback_data="about_menu")
        ],
        [
            InlineKeyboardButton("📢 UPDATES", url=info.UPDATE_CHANNEL),
            InlineKeyboardButton("🎧 SUPPORT", url=info.SUPPORT_GROUP)
        ],
        [
            InlineKeyboardButton("💎 GO PREMIUM", callback_data="upgrade")
        ]
    ]

    await update.message.reply_text(
        text=script.START_TXT.format(name=user.first_name, status=status),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

start_handler = CommandHandler("start", start)
