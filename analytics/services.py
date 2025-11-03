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
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    text = ""
    try:
        logger.info(f"Extracting text from: {full_path}")
        with fitz.open(full_path) as doc:
            for page in doc:
                text += page.get_text()
        logger.info(f"✅ Extracted {len(text)} characters from {file_path}")
        return text
    except Exception as e:
        logger.error(f"❌ Error reading PDF file {full_path}: {e}", exc_info=True)
        raise

def analyze_resume_with_gemini(resume_text: str) -> dict:
    try:
        api_key = settings.GEMINI_API_TOKEN
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in settings.")
            
        client = genai.Client(api_key=api_key)

        system_instruction = (
            "You are a world-class Resume Parsing AI. Extract all relevant "
            "information from the resume text and return it strictly in JSON."
        )
        user_prompt = f"Analyze the following resume text:\n---\n{resume_text}"
        full_contents = system_instruction + "\n\n" + user_prompt

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FinalResumeOutput,
        )

        logger.info("🔍 Sending resume data to Gemini for structured analysis...")
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=[full_contents],
            config=config,
        )
        
        json_string = response.text.strip()
        data = json.loads(json_string)
        logger.info("✅ Gemini analysis completed successfully.")
        return data.get('resume_data', data)

    except Exception as e:
        logger.error(f"❌ Gemini API call failed: {e}", exc_info=True)
        raise

def process_and_save_resume_info(resume_id: int, file_path: str):
    db_generator = get_db()
    db = next(db_generator)
    telegram_id = None 
    job_title = "Resume"
    
    try:
        logger.info(f"🚀 Starting resume processing for ID: {resume_id}")

        resume_text = extract_text_from_pdf(file_path)
        analysis_data = analyze_resume_with_gemini(resume_text)

        resume = db.query(Resume).filter(Resume.id == resume_id).one()
        resume_info = db.query(ResumeInfo).filter(ResumeInfo.resume_id == resume_id).one()

        telegram_id = resume.user.telegram_id
        job_title = resume.job_title

        resume_info.phone = analysis_data.get('phone')
        resume_info.email = analysis_data.get('email')
        resume_info.linkedin = analysis_data.get('linkedin')
        resume_info.position = analysis_data.get('position_inferred')
        resume_info.education_level = analysis_data.get('education_level')
        resume_info.work_history = analysis_data.get('work_history')
        resume_info.skills = analysis_data.get('skills')
        resume_info.core_values = analysis_data.get('core_values')
        resume_info.structured_json = analysis_data

        resume.processed = True
        db.commit()

        logger.info(f"✅ Resume {resume_id} processed successfully. Generating PDF...")

        pdf_path = generate_harvard_pdf(analysis_data, telegram_id)

        if pdf_path:
            send_pdf_to_telegram(telegram_id, pdf_path, job_title)
            logger.info(f"📨 PDF sent to Telegram user {telegram_id}.")
        else:
            logger.warning(f"⚠️ PDF generation failed for resume {resume_id}")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to process resume {resume_id}: {e}", exc_info=True)
        if telegram_id:
            try:
                import telegram
                bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
                bot.send_message(
                    chat_id=telegram_id,
                    text=f"❌ **Resume Analysis Failed**\n\nThere was an error processing your resume for: *{job_title}*.",
                    parse_mode='Markdown'
                )
            except Exception as bot_e:
                logger.error(f"Failed to send Telegram error message: {bot_e}", exc_info=True)
    finally:
        db_generator.close()
