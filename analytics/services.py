#tenabot/analytics/services.py
import os
import fitz  # PyMuPDF
from google import genai
from google.genai import types
from django.conf import settings
from tenabot.db import get_db
from bot.models import Resume, ResumeInfo
from .pdf_service import generate_harvard_pdf
from tenabot.notification import send_pdf_to_telegram
import json

import telegram

from .models import ResumeAnalysisSchema, FinalResumeOutput

import logging
logger = logging.getLogger(__name__)  # ✅ Correct logger usage


MANDATORY_RESUME_KEYWORDS = [
    "experience", "education", "skills", "history", "summary", "profile", "contact"
]

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

def analyze_resume_with_gemini(resume_text: str, job_description: str = "") -> dict:
    """
    Sends resume text to Gemini for structured JSON analysis.
    Uses the job_description (if provided) to tailor the extracted resume content.
    """
    try:
        logger.info("🧠 [STEP 2] Preparing Gemini request...")
        api_key = settings.GEMINI_API_TOKEN
        if not api_key:
            raise ValueError("GEMINI_API_TOKEN missing in settings.")
        
        client = genai.Client(api_key=api_key)
        
        # --- 1. Define the System Instruction ---
        
        system_instruction = (
            "You are a professional Resume Parsing and Tailoring AI. "
            "Your primary goal is to extract structured JSON data from the resume. "
            "If a job description is provided, prioritize and emphasize skills, "
            "experience, and achievements that are most relevant to that description. "
            "Ensure the output strictly adheres to the provided JSON schema."
        )

        # --- 2. Construct the Full Content ---
        
        full_contents = f"--- RESUME TO ANALYZE ---\n{resume_text}"
        
        # 🆕 Conditionally add the job description to the prompt
        if job_description and job_description.strip():
            logger.info("🎯 Tailoring response using provided job description.")
            full_contents = (
                f"--- TARGET JOB DESCRIPTION ---\n{job_description.strip()}\n\n"
                f"{full_contents}"
            )
        else:
            logger.info("🔎 Analyzing resume without job description.")
        
        # 🆕 Prepend the system instruction to the final content list for clarity
        contents_list = [system_instruction, full_contents]


        clean_schema = strip_additional_props(FinalResumeOutput.model_json_schema())

        # Configuration for structured JSON output
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=clean_schema,
        )

        logger.info("🔍 Sending content to Gemini model...")
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            # Use the structured contents list
            contents=contents_list,
            config=config,
        )

        json_string = response.text.strip()
        data = json.loads(json_string)
        logger.info("✅ Gemini analysis successful.")
        
        # Return the parsed data
        return data.get("resume_data", data) 

    except Exception as e:
        logger.error(f"❌ Gemini API call failed: {e}", exc_info=True)
        raise

# --- Main Processing Pipeline ---

def process_and_save_resume_info(resume_id: int, file_path: str, job_description: str):
    """
    Main function: extract → analyze → validate content → update DB → generate/send PDF.
    """
    db_gen = get_db()
    db = next(db_gen)
    telegram_id = None
    job_title = "Resume"
    
    # Pre-fetch user/job info for error reporting outside the main try block
    try:
        resume_record = db.query(Resume).filter(Resume.id == resume_id).one_or_none()
        if resume_record:
            telegram_id = resume_record.user.telegram_id
            job_title = resume_record.job_title
        else:
            logger.error(f"❌ Resume record not found for ID={resume_id}. Cannot proceed.")
            return
    except Exception as e:
        logger.error(f"❌ Failed to retrieve initial resume/user data: {e}", exc_info=True)
        db_gen.close()
        return


    try:
        logger.info(f"🚀 [STEP 0] Starting processing for Resume ID={resume_id}")
        
        # 1. Extract Text
        resume_text = extract_text_from_pdf(file_path)

        # 🆕 1.5. Validate Extracted Content
        logger.info("🔍 [STEP 1.5] Validating extracted PDF content...")
        if not resume_text or len(resume_text.strip()) < 50:
            raise ValueError("PDF text extraction failed or resulted in a blank document.")

        text_lower = resume_text.lower()
        keyword_found = any(keyword in text_lower for keyword in MANDATORY_RESUME_KEYWORDS)

        if not keyword_found:
            db.rollback() # Rollback any pending operations
            error_msg = f"PDF validation failed. The document does not appear to be a resume (missing keywords: {', '.join(MANDATORY_RESUME_KEYWORDS[:3])}...)."
            logger.warning(f"⚠️ [VALIDATION FAIL] Resume ID={resume_id}: {error_msg}")
            
            # Send specific validation failure message to Telegram
            bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
            bot.send_message(
                chat_id=telegram_id,
                text=(
                    f"⚠️ *Resume Analysis Halted - Invalid Content*\n\n"
                    f"The file you uploaded for *{job_title}* does not contain typical resume content "
                    f"(e.g., *Education*, *Skills*, *Experience*). Please ensure you are uploading a clear resume PDF."
                ),
                parse_mode="Markdown",
            )
            return

        logger.info("✅ PDF content validated successfully.")

        # 2. Analyze with Gemini
        logger.info(f"🧾 [STEP 2] Text extracted, sending to Gemini...")
        analysis_data = analyze_resume_with_gemini(resume_text, job_description)

        # Retrieve relevant records (Use existing resume_record from pre-fetch, or query again)
        resume_info = db.query(ResumeInfo).filter(ResumeInfo.resume_id == resume_id).one_or_none()
        
        # --- Continue with the rest of the original logic ---
        
        # 3. Update Database Records
        logger.info(f"🗂 [STEP 3] Updating database records...")
        
        # Use .get() with defaults for safe dictionary access
        resume_info.phone = analysis_data.get("phone")
        resume_info.email = analysis_data.get("email")
        resume_info.linkedin = analysis_data.get("linkedin")
        resume_info.position = analysis_data.get("position_inferred")
        resume_info.education_level = analysis_data.get("education_level")
        resume_info.work_history = analysis_data.get("work_history")
        resume_info.skills = analysis_data.get("skills")
        resume_info.core_values = analysis_data.get("core_values")
        resume_info.structured_json = json.dumps(analysis_data)
        
        # Mark as processed
        resume_record.processed = True
        db.commit()
        logger.info(f"💾 [COMMIT] Database updated successfully for resume_id={resume_id}")

        # 4. Generate and Send PDF
        logger.info(f"🧾 [STEP 4] All data processed. Proceeding to generate Harvard PDF...")
        pdf_path = generate_harvard_pdf(analysis_data, telegram_id)

        if pdf_path:
            logger.info(f"✅ [STEP 5] PDF generated. Sending to Telegram user {telegram_id}...")
            send_pdf_to_telegram(telegram_id, pdf_path, job_title)
            logger.info(f"📨 [STEP 6] PDF sent successfully.")
        else:
            logger.error(f"⚠️ PDF generation failed for resume ID={resume_id}")
            # Consider sending a failure message here too, if generation failed.

    except Exception as e:
        db.rollback()  # Ensure database integrity on failure
        logger.error(f"💥 [FAILURE] Resume processing failed for {resume_id}: {e}", exc_info=True)
        
        # Send General Failure Notification to Telegram
        if telegram_id:
            try:
                # Use existing bot if defined, or create a new one
                bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
                bot.send_message(
                    chat_id=telegram_id,
                    text=(
                        f"❌ *Resume Analysis Failed*\n\n"
                        f"An unexpected error occurred while processing your resume for *{job_title}*. "
                        f"Please try again or contact support."
                    ),
                    parse_mode="Markdown",
                )
            except Exception as bot_e:
                logger.error(f"⚠️ Telegram notification failed: {bot_e}", exc_info=True)
    finally:
        db_gen.close()
        logger.info(f"🔚 [END] Database connection closed for resume_id={resume_id}")    
        
def strip_additional_props(schema: dict) -> dict:
    if isinstance(schema, dict):
        return {
            k: strip_additional_props(v)
            for k, v in schema.items()
            if k != "additionalProperties"
        }
    elif isinstance(schema, list):
        return [strip_additional_props(i) for i in schema]
    return schema