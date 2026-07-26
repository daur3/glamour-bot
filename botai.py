import sys
import types

# ФИКС ДЛЯ RENDER
if 'imghdr' not in sys.modules:
    sys.modules['imghdr'] = types.ModuleType('imghdr')

try:
    import pkg_resources

except ModuleNotFoundError:
    import setuptools.pkg_resources as pkg_resources
    sys.modules['pkg_resourses'] = pkg_resources

import os
import threading
from flask import Flask
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters
from groq import Groq

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
ADMIN_CHAT_ID = 8349612634 # твой ID от @userinfobot
client = Groq(api_key=GROQ_API_KEY)

user_data = {}

# 1. СДЕЛАЛИ КРАСИВОЕ МЕНЮ
SERVICES = {
    "1": "Маникюр - 6000 тг",
    "2": "Педикюр - 8000 тг"
}
SERVICES_TEXT = "💎 Добро пожаловать в GLAMOUR!\n\nВыберите услугу:\n1. Маникюр - 6000 тг\n2. Педикюр - 8000 тг\n⏰ Работаем: 10:00 - 21:00"



def save_to_file(user_id, data, context): # <- context тут должен быть
    service_name = SERVICES.get(data['service'], data['service'])
    
    admin_message = (
        f"🔔 НОВАЯ ЗАЯВКА В GLAMOUR!\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"💅 Услуга: {service_name}\n"
        f"⏰ Время: {datetime.now().strftime('%H:%M %d.%m.%Y')}"
    )
    context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data[user_id] = {"step": "start"}

    # 2. ДОБАВИЛИ КНОПКИ
    keyboard = [['1', '2']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(SERVICES_TEXT, reply_markup=reply_markup)

def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_data:
        user_data[user_id] = {"step": "start"}
    step = user_data[user_id]["step"]

    if step == "start":
        if text not in SERVICES:
            update.message.reply_text("Пожалуйста, выберите 1 или 2")
            return
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

        # 3. ИСПРАВИЛИ ВЫВОД УСЛУГИ
        service_name = SERVICES.get(data['service'], data['service'])

        update.message.reply_text(
            f"✅ Готово, {data['name']}!\n\n"
            f"Вы записаны на: {service_name}\n"
            f"Мы свяжемся с вами для подтверждения времени.\n\n"
            f"GLAMOUR - ждем вас! 💅"
        )
        user_data[user_id] = {"step": "start"}

    else: # ИИ для остальных вопросов
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": f"Ты админ салона Glamour. Услуги: {SERVICES_TEXT}. Отвечай вежливо и коротко."}, {"role": "user", "content": text}]
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
