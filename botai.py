import os
import threading
import asyncio
from flask import Flask
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from groq import AsyncGroq

# 1. FLASK ДЛЯ RENDER
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running"
def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
threading.Thread(target=run_flask, daemon=True).start()


TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = AsyncGroq(api_key=GROQ_API_KEY)

user_data = {}
SERVICES = """УСЛУГИ САЛОНА GLAMOUR:
1. Маникюр с покрытием - 6000 тг
2. Педикюр - 8000 тг
3. Стрижка женская - 8000 тг
4. Стрижка мужская - 5000 тг
5. Окрашивание - от 15000 тг
Работаем: 10:00 - 21:00
"""

def save_to_file(user_id, data):
    with open("zayavki.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | ID:{user_id} | {data}\n")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"step": "start"}
    await update.message.reply_text("Привет! " + SERVICES + "\n\nВыберите услугу цифрой:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id not in user_data:
        user_data[user_id] = {"step": "start"}
    
    step = user_data[user_id]["step"]
    
    if step == "start":
        user_data[user_id]["service"] = text
        user_data[user_id]["step"] = "name"
        await update.message.reply_text("Как вас зовут?")
    elif step == "name":
        user_data[user_id]["name"] = text
        user_data[user_id]["step"] = "phone"
        await update.message.reply_text("И ваш номер телефона?")
    elif step == "phone":
        user_data[user_id]["phone"] = text
        data = user_data[user_id]
        save_to_file(user_id, data)
        await update.message.reply_text(f"✅ Готово! Вы записаны!\nУслуга: {data['service']}\nИмя: {data['name']}")
        user_data[user_id] = {"step": "start"}
    else:
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": f"Ты админ салона Glamour. {SERVICES}"}, {"role": "user", "content": text}]
        )
        await update.message.reply_text(response.choices[0].message.content)

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
