import os
from dotenv import load_dotenv

load_dotenv()

# --- BOT CREDENTIALS ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MONGO_URI = os.environ.get("MONGO_URI", "")
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x]
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-100"))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# --- AI TOKENS ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
HF_TOKEN = os.environ.get("HF_TOKEN", "") # Hugging Face Token

# --- LINKS & STUFF ---
SUPPORT_GROUP = "https://t.me/YourSupportGroup"
UPDATE_CHANNEL = "https://t.me/YourUpdateChannel"
BOT_USERNAME = "FlixoraAiBot" # Without @

# --- MODELS ---
MODELS = {
    "model_1": "openai/gpt-4o-mini",
    "model_2": "meta-llama/llama-3.1-8b-instruct",
    "model_3": "mistralai/mixtral-8x7b-instruct"
}
