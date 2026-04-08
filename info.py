import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "").strip().rstrip('/')
PORT = int(os.environ.get("PORT", 10000))
MONGO_URI = os.environ.get("MONGO_URI", "")
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", 0))
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x]

# AI KEYS
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
HF_TOKEN = os.environ.get("HF_TOKEN", "") # Hugging Face Token

MODELS = {
    "model_1": "openai/gpt-4o-mini",
    "model_2": "meta-llama/llama-3.1-8b-instruct", # HF Model Example
    "model_3": "mistralai/mixtral-8x7b-instruct"
}

WELCOME_IMAGE_URL = os.environ.get("WELCOME_IMAGE_URL", "https://graph.org/file/abc.jpg")
