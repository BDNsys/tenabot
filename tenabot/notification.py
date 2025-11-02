import os
import telegram
from django.conf import settings
from telegram import InputFile

# This utility uses the same token as the main bot to send a message
# Note: This runs outside the main Application loop, using a simple blocking client.

def send_pdf_to_telegram(telegram_id: int, pdf_path: str, job_title: str):
    """
    Initializes a bot client and sends the generated PDF to the specified user.
    """
    bot_token = settings.TELEGRAM_BOT_TOKEN
    
    if not bot_token:
        print("ERROR: BOT_TOKEN not configured for notification helper.")
        return

    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF file not found at path: {pdf_path}")
        return

    try:
        # Initialize a new Bot client
        bot = telegram.Bot(token=bot_token)
        
        caption = f"✅ Resume Analysis Complete!\n\nHere is your new **Harvard-Style PDF Resume** based on your uploaded document for the role: *{job_title}*."

        # Send the document
        with open(pdf_path, 'rb') as pdf_file:
            bot.send_document(
                chat_id=telegram_id,
                document=InputFile(pdf_file, filename=f"Harvard_Resume_{job_title}.pdf"),
                caption=caption,
                parse_mode='Markdown'
            )
        print(f"Successfully sent PDF to Telegram user: {telegram_id}")

    except telegram.error.TelegramError as e:
        print(f"Telegram failed to send PDF to {telegram_id}: {e}")
    except Exception as e:
        print(f"Unexpected error in sending Telegram notification: {e}")
