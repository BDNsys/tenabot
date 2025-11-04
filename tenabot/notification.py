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
        logger.error("ERROR: BOT_TOKEN not configured.")
        return

    if not os.path.exists(pdf_path):
        logger.error(f"PDF not found at {pdf_path}")
        return

    # Log file size
    file_size_bytes = os.path.getsize(pdf_path)
    logger.info(f"PDF exists: {pdf_path} (size: {file_size_bytes} bytes)")

    async def _send():
        bot = telegram.Bot(token=bot_token)
        caption = (
            f"✅ Resume Analysis Complete!\n\n"
            f"Here is your **Harvard-Style PDF Resume** for *{job_title}*."
        )
       
        async with bot:
            logger.info(f"✅ Sending file: {pdf_path} as Harvard_Resume_{job_title}.pdf")
            await bot.send_document(
                chat_id=telegram_id,
                document=InputFile(pdf_path, filename=f"Harvard_Resume_{job_title}.pdf"),
                caption=caption,
                parse_mode="Markdown"
            )

    try:
        print("Pausing 2 seconds before sending PDF...")
        time.sleep(2)
        asyncio.run(_send())
        print(f"✅ PDF successfully sent to Telegram user {telegram_id}")
    except Exception as e:
        logger.error(f"❌ Error sending PDF to Telegram: {e}", exc_info=True)
