import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
import json

# Pulls your token securely from Render's settings
TOKEN = os.environ.get('TOKEN', '9055184850:AAFLDyMRQ0HISZ89jUG3De_QHmUtMkIFl4w')
CHANNEL_USERNAME = "@english_movies_zone_000"
DB_FILE = "videos.json"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def load_database():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_database(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

@bot.message_handler(content_types=['video'])
def handle_video(message):
    file_id = message.video.file_id
    bot.reply_to(message, f"Video received!\n\nReply to this video with:\n`/add videoA Movie Title Here`", parse_mode="Markdown")

@bot.message_handler(commands=['add'])
def add_video(message):
    if not message.reply_to_message or not message.reply_to_message.video:
        bot.reply_to(message, "⚠️ Please reply to a video with `/add videoA Description`", parse_mode="Markdown")
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "⚠️ Missing description!", parse_mode="Markdown")
        return
    key = parts[1]
    description = parts[2]
    file_id = message.reply_to_message.video.file_id
    db = load_database()
    db[key] = {"file_id": file_id, "description": description}
    save_database(db)
    bot.reply_to(message, f"✅ Successfully saved `{key}`!", parse_mode="Markdown")

@bot.message_handler(commands=['post'])
def post_video(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Usage: `/post videoA`", parse_mode="Markdown")
        return
    key = parts[1]
    db = load_database()
    if key not in db:
        bot.reply_to(message, f"❌ Key `{key}` not found!", parse_mode="Markdown")
        return
    item = db[key]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("▶️ Watch Video", url=f"https://t.me/deriiibot?start={key}"))
    try:
        bot.send_message(CHANNEL_USERNAME, item['description'], reply_markup=markup)
        bot.reply_to(message, f"🚀 Posted `{key}` to channel!", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['start'])
def handle_start(message):
    text_parts = message.text.split()
    if len(text_parts) > 1:
        payload = text_parts[1]
        db = load_database()
        if payload in db:
            bot.send_video(message.chat.id, db[payload]['file_id'])
            return
    bot.send_message(message.chat.id, "Welcome! Use the buttons in the channel.")

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    return "Forbidden", 403

@app.route('/')
def index():
    return "Bot is running on Webhook!", 200

if __name__ == "__main__":
    RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL', '')
    if RENDER_EXTERNAL_URL:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
  
