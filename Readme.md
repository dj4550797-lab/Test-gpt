# AI Telegram Bot

A feature-rich Telegram bot with AI integration, URL shortener, and Admin controls.

## Features
- **AI Chat:** Uses OpenAI/HuggingFace to answer queries.
- **Admin Panel:** Change models and API keys directly from Telegram.
- **URL Shortener:** Built-in TinyURL integration.
- **Premium Section:** Custom monetization or info buttons.
- **Group Support:** Welcome messages and 'Add to Group' buttons.

## Deployment on Render.com
1. Create a new **Web Service** on Render.
2. Connect your GitHub repository.
3. Use the following settings:
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn main:app & python3 main.py` (Or just `python3 main.py`)
4. Add **Environment Variables**:
   - `BOT_TOKEN`: Your Telegram Bot Token from @BotFather.
   - `HF_TOKEN`: Your Hugging Face Token.
   - `OPENAI_API_KEY`: Your OpenAI API Key.

## Admin Setup
- Change `ADMIN_ID` in `main.py` to your numeric ID.
- Use `/admin` to configure the bot via Telegram.
