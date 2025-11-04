import asyncio
import os
import time
from telegram import Bot, InputFile
from django.conf import settings
import logging

# Ensure 'name' is defined or use a specific module name
# For this example, assuming 'name' is intended to be the module name.
logger = logging.getLogger(__name__)


async def _send_pdf(bot_token: str, telegram_id: int, pdf_path: str, filename: str, caption: str):
    """Async function to send a PDF via Telegram."""
    bot = Bot(token=bot_token)
    
    file_stats = os.stat(pdf_path)
    logger.info(
        "📊 File details - Size: %d bytes, Modified: %s", 
        file_stats.st_size, 
        time.ctime(file_stats.st_mtime)
    )

    # Read first few bytes to confirm validity
    try:
        with open(pdf_path, "rb") as f:
            header = f.read(10)
            logger.info("🔍 PDF header preview: %s", header)
    except FileNotFoundError:
        logger.error("❌ PDF file not found at path: %s", pdf_path)
        return

    async with bot:
        # Re-open the file for sending within the async context
        try:
            with open(pdf_path, "rb") as f:  # ✅ Send as file object
                logger.info("📤 Uploading '%s' to chat %d...", filename, telegram_id)
                result = await bot.send_document(
                    chat_id=telegram_id,
                    document=InputFile(f, filename=filename),
                    caption=caption,
                    parse_mode="Markdown"
                )
                if hasattr(result, "document"):
                    logger.info("✅ File sent successfully. Telegram file ID: %s", result.document.file_id)
                else:
                    logger.warning("⚠️ Message sent, but document details missing")
        except Exception as e:
            logger.error("❌ File reading error during upload: %s", e, exc_info=True)


def send_pdf_to_telegram(telegram_id: int, pdf_path: str, job_title: str):
    """Sync wrapper to send PDF to Telegram."""
    try:
        # Load bot token from Django settings
        bot_token = settings.TELEGRAM_BOT_TOKEN
    except AttributeError:
        logger.error("❌ TELEGRAM_BOT_TOKEN missing in settings.")
        return

    if not bot_token:
        logger.error("❌ BOT_TOKEN value is empty.")
        return

    if not os.path.exists(pdf_path):
        logger.error("❌ PDF not found: %s", pdf_path)
        return

    file_size = os.path.getsize(pdf_path)
    logger.info("PDF ready: %s (%d bytes)", pdf_path, file_size)

    # Clean the job title for use in the filename
    clean_job_title = "".join(
        c for c in job_title if c.isalnum() or c in (" ", "-", "_")
    ).strip().replace(" ", "_")
    
    filename = f"Harvard_Resume_{clean_job_title}.pdf"
    caption = f"✅ Resume Analysis Complete!\n\nHere is your **Harvard-Style PDF Resume** for *{clean_job_title}*."

    try:
        logger.info("⏳ Waiting 2s before sending...")
        time.sleep(2)

        send_task = _send_pdf(bot_token, telegram_id, pdf_path, filename, caption)
        loop = asyncio.get_event_loop()
        
        # Check if an event loop is already running (e.g., in an async context)
        if loop.is_running():
            asyncio.ensure_future(send_task)
            logger.info("📨 PDF scheduled to send to chat %d", telegram_id)
        else:
            # Run the async task synchronously
            loop.run_until_complete(send_task)
            logger.info("✅ PDF successfully sent to chat %d", telegram_id)
            
    except Exception as e:
        logger.error("❌ Telegram send failed: %s", e, exc_info=True)