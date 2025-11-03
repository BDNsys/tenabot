import os
import fitz  # PyMuPDF
from google import genai
from google.genai import types
from django.conf import settings
from tenabot.db import get_db
from bot.models import Resume, ResumeInfo
from tenabot.pdf_service import generate_harvard_pdf
from tenabot.notification import send_pdf_to_telegram
import json

from .models import ResumeAnalysisSchema, FinalResumeOutput

import logging
logger = logging.getLogger(__name__)  # ✅ Correct logger usage
def extract_text_from_pdf(file_path: str) -> str:
    """Extracts all text from the provided PDF file."""
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    text = ""
    try:
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"PDF file not found: {full_path}")
        
        logger.info(f"📄 [STEP 1] Opening PDF for text extraction: {full_path}")

        with fitz.open(full_path) as doc:
            logger.info(f"Opened PDF with {len(doc)} pages.")
            for i, page in enumerate(doc, start=1):
                page_text = page.get_text()
                logger.debug(f"Extracted {len(page_text)} chars from page {i}")
                text += page_text

        if not text.strip():
            logger.warning(
                f"⚠️ No text extracted from {file_path}. Possibly scanned or image-based PDF."
            )
        else:
            logger.info(f"✅ Extracted {len(text)} characters from {file_path}")

        return text
    except Exception as e:
        logger.error(
            f"❌ PDF extraction failed for {full_path}: {e}", exc_info=True
        )
        raise

# --- Gemini Analysis ---

def analyze_resume_with_gemini(resume_text: str) -> dict:
    """Sends resume text to Gemini for structured JSON analysis."""
    try:
        logger.info("🧠 [STEP 2] Preparing Gemini request...")
        api_key = settings.GEMINI_API_TOKEN
        if not api_key:
            raise ValueError("GEMINI_API_TOKEN missing in settings.")
        
        client = genai.Client(api_key=api_key)
        
        system_instruction = (
            "You are a professional Resume Parsing AI. "
            "Return structured JSON based on the resume text."
        )
        full_contents = f"{system_instruction}\n\n---\n{resume_text}"

        # Configuration for structured JSON output
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FinalResumeOutput,  # Uses the defined schema
        )

        logger.info("🔍 Sending content to Gemini model...")
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[full_contents],
            config=config,
        )

        json_string = response.text.strip()
        data = json.loads(json_string)
        logger.info("✅ Gemini analysis successful.")
        # Return the parsed data, handling potential nested structure
        return data.get("resume_data", data) 

    except Exception as e:
        logger.error(f"❌ Gemini API call failed: {e}", exc_info=True)
        raise

# --- Main Processing Pipeline ---

def process_and_save_resume_info(resume_id: int, file_path: str):
    """Main function: extract → analyze → update DB → generate/send PDF."""
    # Use a generator for the database connection
    db_gen = get_db()
    db = next(db_gen)
    telegram_id = None
    job_title = "Resume"

    try:
        logger.info(f"🚀 [STEP 0] Starting processing for Resume ID={resume_id}")
        
        # 1. Extract Text
        resume_text = extract_text_from_pdf(file_path)

        # 2. Analyze with Gemini
        logger.info(f"🧾 [STEP 2] Text extracted, sending to Gemini...")
        analysis_data = analyze_resume_with_gemini(resume_text)

        # Retrieve relevant records
        resume = db.query(Resume).filter(Resume.id == resume_id).one_or_none()
        resume_info = db.query(ResumeInfo).filter(ResumeInfo.resume_id == resume_id).one_or_none()

        telegram_id = resume.user.telegram_id
        job_title = resume.job_title

        # 3. Update Database Records
        db_gen.close() 
        db_gen = get_db()
        db = next(db_gen) # Get a fresh session object


        logger.info(f"🗂 [STEP 3] Updating database records...")
        resume_info.phone = analysis_data.get("phone")
        resume_info.email = analysis_data.get("email")
        resume_info.linkedin = analysis_data.get("linkedin")
        resume_info.position = analysis_data.get("position_inferred")
        resume_info.education_level = analysis_data.get("education_level")
        resume_info.work_history = analysis_data.get("work_history")
        resume_info.skills = analysis_data.get("skills")
        resume_info.core_values = analysis_data.get("core_values")
        resume_info.structured_json = json.dumps(analysis_data) # Save the full structured output

        resume.processed = True
        db.commit()

        # 4. Generate and Send PDF
        logger.info(f"✅ [STEP 4] Resume {resume_id} processed successfully. Generating Harvard PDF...")
        pdf_path = generate_harvard_pdf(analysis_data, telegram_id)

        if pdf_path:
            send_pdf_to_telegram(telegram_id, pdf_path, job_title)
            logger.info(f"📨 [STEP 5] PDF sent to Telegram user {telegram_id}")
        else:
            logger.warning(f"⚠️ PDF generation returned None for resume {resume_id}")

    except Exception as e:
        db.rollback() # Ensure database integrity on failure
        logger.error(f"💥 [FAILURE] Resume processing failed for {resume_id}: {e}", exc_info=True)
        
        # Send Failure Notification to Telegram
        if telegram_id:
            try:
                import telegram
                bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
                bot.send_message(
                    chat_id=telegram_id,
                    text=f"❌ *Resume Analysis Failed*\n\nAn error occurred while processing your resume for *{job_title}*.",
                    parse_mode="Markdown",
                )
            except Exception as bot_e:
                logger.error(f"⚠️ Telegram notification failed: {bot_e}", exc_info=True)
    finally:
        db_gen.close()
        logger.info("🔚 [END] Database connection closed.")