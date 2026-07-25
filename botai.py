import sys
import types

if 'imghdr' not in sys.modules:
    sys.modules['imghdr'] = types.ModuleType('imghdr')

import os
import threading
from flask import Flask
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters
from groq import Groq

# FLASK ДЛЯ RENDER
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running OK"
def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
threading.Thread(target=run_flask, daemon=True).start()

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

user_data = {}
SERVICES = "УСЛУГИ САЛОНА GLAMOUR:\n1. Маникюр - 6000 тг\n2. Педикюр - 8000 тг\nРаботаем: 10:00 - 21:00\n"

def save_to_file(user_id, data):
    with open("zayavki.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | ID:{user_id} | {data}\n")

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data[user_id] = {"step": "start"}
    update.message.reply_text("Привет! " + SERVICES + "\n\nВыберите услугу цифрой:")

def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text
    if user_id not in user_data: user_data[user_id] = {"step": "start"}
    step = user_data[user_id]["step"]
    
    if step == "start":
        user_data[user_id]["service"] = text
        user_data[user_id]["step"] = "name"
        update.message.reply_text("Как вас зовут?")
    elif step == "name":
        user_data[user_id]["name"] = text
        user_data[user_id]["step"] = "phone"
        update.message.reply_text("И ваш номер телефона?")
    elif step == "phone":
        user_data[user_id]["phone"] = text
        data = user_data[user_id]
        save_to_file(user_id, data)
        update.message.reply_text(f"✅ Готово! Вы записаны!\nУслуга: {data['service']}")
        user_data[user_id] = {"step": "start"}
    else:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=[{"role": "system", "content": f"Ты админ салона Glamour. {SERVICES}"}, {"role": "user", "content": text}]
        )
        update.message.reply_text(response.choices[0].message.content)

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
