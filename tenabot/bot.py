import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from asgiref.sync import sync_to_async
import django
import sys

from . import views

from django.contrib.auth import get_user_model


User = get_user_model()

# Ensure Django is initialized
sys.path.append('/path/to/your/project')  # e.g. "/home/nazri/tenabot"
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tenabot.settings')
django.setup()

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


@sync_to_async
def register_telegram_user(telegram_user):
    user, created = User.objects.get_or_create(
        telegram_id=telegram_user.id,
        defaults={
            "username": telegram_user.username or f"user_{telegram_user.id}",
            "first_name": telegram_user.first_name or "",
            "last_name": telegram_user.last_name or "",
        },
    )
    return user, created



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_user = update.effective_user

    # ✅ Register or get user
    user, created = await register_telegram_user(telegram_user)

    # ✅ Prepare message
    if created:
        message = f"👋 Welcome, {telegram_user.first_name or telegram_user.username}! Your Tenabot account has been created."
    else:
        message = f"Welcome back, {telegram_user.first_name or telegram_user.username}!"

    # ✅ Web App button (your mini app)
    web_app = WebAppInfo(url="https://tena.bdnsys.com/bot/")  # Note: trailing slash included


    keyboard = [
        [InlineKeyboardButton("🚀 Launch TenaBot", web_app=web_app)]
    ]
    
    
    # ✅ Web App button (your mini app)

   
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup)

  

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found in environment variables!")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    print("🤖 Tenabot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
