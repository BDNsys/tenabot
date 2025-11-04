#tenabot/tenabot/notification.py
import asyncio
import time
import telegram
from telegram import InputFile
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__) 

def send_pdf_to_telegram(telegram_id: int, pdf_path: str, job_title: str):
    """Synchronous wrapper around async Telegram send_document."""
    bot_token = settings.TELEGRAM_BOT_TOKEN

    if not bot_token:
        print("ERROR: BOT_TOKEN not configured.")
        return

    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found at {pdf_path}")
        return

    async def _send():
        bot = telegram.Bot(token=bot_token)
        caption = (
            f"✅ Resume Analysis Complete!\n\n"
            f"Here is your **Harvard-Style PDF Resume** for *{job_title}*."
        )
       
        async with bot:
            logger.info(f"✅ sending file{pdf_path} filename Harvard_Resume_{job_title}.pdf")
            
            await bot.send_document(
                chat_id=telegram_id,
                document=InputFile(pdf_path, filename=f"Harvard_Resume_{job_title}.pdf"),
                caption=caption,
                parse_mode="Markdown"
            )

    try:
        if not os.path.exists(pdf_path):
            logger.error(f"PDF path does not exist: {pdf_path}")
        else:
            logger.info(f"PDF exists. Proceeding to send {pdf_path}")
        print("Pausing 2 seconds before sending PDF...")
        time.sleep(2)
        asyncio.run(_send())
        print(f"✅ PDF successfully sent to Telegram user {telegram_id}")
    except Exception as e:
        print(f"❌ Error sending PDF to Telegram: {e}")
