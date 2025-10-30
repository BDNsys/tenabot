import os
from dotenv import load_dotenv
from telegram import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from users.models import User
import django
import sys

# Ensure Django is initialized
sys.path.append('/path/to/your/project')  # e.g. "/home/nazri/tenabot"
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tenabot.settings')
django.setup()

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def register_telegram_user(telegram_user):
    """Registers the Telegram user in Django if not already registered."""
    user, created = User.objects.get_or_create(
        telegram_id=str(telegram_user.id),
        defaults={
            'username': telegram_user.username,
            'first_name': telegram_user.first_name,
            'last_name': telegram_user.last_name,
            'avatar_url': None,  # Telegram API v6 no longer exposes avatar directly
        },
    )
    return user, created


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_user = update.effective_user
    user, created = register_telegram_user(telegram_user)

    if created:
        message = f"👋 Welcome, {telegram_user.first_name}! Your Tenabot account has been created."
    else:
        message = f"Welcome back, {telegram_user.first_name or telegram_user.username}!"

    keyboard = [
        [KeyboardButton("🚀 Launch Tenabot", web_app=WebAppInfo(url="https://tena.bdnsys.com/bot/"))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

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
