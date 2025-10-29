# tenabot/bot.py
import os
from dotenv import load_dotenv
# from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update 
from telegram import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, Update 
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     keyboard = [
#         [InlineKeyboardButton("🚀 Launch", url="https://tena.bdnsys.com/bot/")]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)

#     await update.message.reply_text(
#         "Welcome to Tenabot! Click below to launch the app 👇",
#         reply_markup=reply_markup
#     )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("🚀 Launch Tenabot", web_app=WebAppInfo(url="https://tena.bdnsys.com/bot/"))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Tap the button below to launch Tenabot 👇",
        reply_markup=reply_markup
    )

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found in environment variables!")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    print("🤖 Tenabot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
