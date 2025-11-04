# tenabot/tenabot/notification.py

import asyncio
import os
import time
from telegram import Bot, InputFile
from django.conf import settings
import logging
logger = logging.getLogger(__name__) 

# --- Setup ---
# NOTE: The logger name setup (logger = logging.getLogger(name)) 
# needs to be defined outside this structure for the code to run correctly.
# Assuming 'logger' is defined and configured elsewhere.

# --- Async Core Function ---
async def _send_pdf(bot_token: str, telegram_id: int, pdf_path: str, filename: str, caption: str):
    """
    Async function to send a PDF via Telegram's sendDocument API.
    
    Args:
        bot_token (str): The Telegram Bot API token.
        telegram_id (int): The chat ID to send the document to.
        pdf_path (str): The local path to the PDF file.
        filename (str): The desired filename for the document in Telegram.
        caption (str): The message caption (supports Markdown).
    """
    try:
        # Initialize the bot object
        bot = Bot(token=bot_token)
        
        async with bot:
            logger.info(f"Uploading file: {filename} to chat {telegram_id}")
            await bot.send_document(
                chat_id=telegram_id,
                # InputFile prepares the file for upload
                document=InputFile(pdf_path, filename=filename),
                caption=caption,
                parse_mode="Markdown"
            )
            logger.info(f"Successfully uploaded {filename}.")
            
    except Exception as e:
        # Re-raising the exception to be caught by the calling function
        raise Exception(f"Telegram upload failed: {e}")

# --- Synchronous Wrapper ---
def send_pdf_to_telegram(telegram_id: int, pdf_path: str, job_title: str):
    """
    Synchronous wrapper around the async Telegram PDF sender.
    Handles token/path checks, logging, and managing the asyncio loop.
    
    Args:
        telegram_id (int): The chat ID.
        pdf_path (str): The local path to the PDF file.
        job_title (str): The job title used for filename and caption generation.
    """
    # 1. Configuration and Validation
    bot_token = settings.TELEGRAM_BOT_TOKEN
    if not bot_token:
        logger.error("ERROR: BOT_TOKEN not configured in Django settings.")
        return

    if not os.path.exists(pdf_path):
        logger.error(f"PDF not found at {pdf_path}")
        return

    # 2. File Metadata and Caption
    file_size_bytes = os.path.getsize(pdf_path)
    logger.info(f"PDF exists: {pdf_path} (size: {file_size_bytes} bytes)")
    clean_job_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    clean_job_title = clean_job_title.replace(' ', '_') 

    filename = f"Harvard_Resume_{clean_job_title}.pdf"
    caption = (
        f"✅ Resume Analysis Complete!\n\n"
        f"Here is your **Harvard-Style PDF Resume** for *{clean_job_title}*."
    )
    
    # 3. Execution (Time delay and Async Handling)
    try:
        logger.info("Pausing 2 seconds before sending PDF...")
        time.sleep(2) # Delay for system stability/user experience
        
        # Prepare the async task
        send_task = _send_pdf(bot_token, telegram_id, pdf_path, filename, caption)

        loop = asyncio.get_event_loop()
        
        if loop.is_running():
            # If already inside an event loop (e.g., in an async Django view/consumer)
            asyncio.ensure_future(send_task)
            logger.info(f"✅ PDF scheduled to send to Telegram user {telegram_id}")
        else:
            # If called from a synchronous context (e.g., a standard Django view/signal)
            loop.run_until_complete(send_task)
            logger.info(f"✅ PDF successfully sent to Telegram user {telegram_id}")

    except Exception as e:
        logger.error(f"❌ Error sending PDF to Telegram: {e}", exc_info=True)