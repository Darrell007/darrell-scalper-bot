from flask import Flask, request
import telegram
import os

app = Flask(__name__)

TOKEN = "7646470360:AAH25-iQhphoP5RmZK7vmLoP4yxlqU2R140"
bot = telegram.Bot(token=TOKEN)

@app.route('/')
def index():
    return "Darrell Scalper Bot is running."

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id
    text = update.message.text

    if text.lower() == "/start":
        bot.send_message(chat_id=chat_id, text="📊 Welcome to Darrell Scalper Bot!")
    else:
        bot.send_message(chat_id=chat_id, text="⏳ Scalping signal coming soon...")

    return "ok"
