# tenabot/tenabot/notification.py
import os
import asyncio
import telegram
from django.conf import settings
from telegram import InputFile

async def _send_pdf_async(bot_token, telegram_id, pdf_path, job_title):
    bot = telegram.Bot(token=bot_token)
    caption = (
        f"✅ Resume Analysis Complete!\n\n"
        f"Here is your new *Harvard-Style PDF Resume* for the role: *{job_title}*."
    )
    async with bot:
        async with open(pdf_path, "rb") as pdf_file:
            await bot.send_document(
                chat_id=telegram_id,
                document=InputFile(pdf_file, filename=f"Harvard_Resume_{job_title}.pdf"),
                caption=caption,
                parse_mode="Markdown",
            )

def send_pdf_to_telegram(telegram_id: int, pdf_path: str, job_title: str):
    """
    Runs async telegram send_document safely from synchronous code.
    """
    bot_token = settings.TELEGRAM_BOT_TOKEN

    if not bot_token:
        print("ERROR: BOT_TOKEN not configured.")
        return

    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found at {pdf_path}")
        return

    try:
        asyncio.run(_send_pdf_async(bot_token, telegram_id, pdf_path, job_title))
        print(f"✅ Successfully sent PDF to Telegram user {telegram_id}")
    except Exception as e:
        print(f"❌ Telegram send failed for {telegram_id}: {e}")
