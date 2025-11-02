import os
import fitz # PyMuPDF
from google import genai
from google.genai import types
from django.conf import settings
from tenabot.db import get_db
from bot.models import Resume,ResumeInfo
from tenabot.pdf_service import generate_harvard_pdf
from tenabot.notification import send_pdf_to_telegram
import logging
import json
# Assuming you put the schema here or import it
from .models import ResumeAnalysisSchema, FinalResumeOutput # Import the Pydantic schema

# Set up logging for the background thread
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text_from_pdf(file_path: str) -> str:
    """Uses PyMuPDF to reliably extract text from a local PDF file."""
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    text = ""
    try:
        with fitz.open(full_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        logging.error(f"Error reading PDF file {full_path}: {e}") # FIX 2: Use logging.error
        raise

def analyze_resume_with_gemini(resume_text: str) -> dict:
    """
    Sends resume text to Gemini and requests structured JSON output.
    """
    try:
        # Load API Key and initialize client
        api_key = settings.GEMINI_API_TOKEN
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in settings.")
            
        client = genai.Client(api_key=api_key)
        
        # 1. Define the Instruction/Prompt Combination (FIX 1: Combining system instruction and prompt)
        system_instruction = (
            "You are a world-class Resume Parsing AI. Your task is to extract all relevant "
            "information from the provided resume text and return it strictly in the requested JSON format. "
            "Do not output any introductory or explanatory text. Just output the JSON object."
        )

        user_prompt = f"Analyze the following resume text and extract the information into the required JSON schema. Prioritize accuracy and completeness.\n\nRESUME TEXT:\n---\n{resume_text}"
        
        # Combine the system instruction and user prompt to avoid the 'system_instruction' keyword TypeError
        full_contents = system_instruction + "\n\n" + user_prompt

        # 2. Configure the model request for structured output
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FinalResumeOutput, # Use the Pydantic model for schema definition
        )

        # 3. Make the API Call (FIX 1: Removed 'system_instruction' keyword to resolve TypeError)
        # The instruction is now embedded at the start of the content string.
        response = client.models.generate_content(
            model='gemini-2.5-pro', # Use a high-quality model for complex extraction
            contents=[full_contents],
            config=config,
        )
        
        # 4. Parse the JSON string result
        json_string = response.text.strip()
        data = json.loads(json_string)
        
        # The result will be nested under 'resume_data' due to the FinalResumeOutput wrapper
        return data.get('resume_data', data)

    except Exception as e:
        logging.error(f"Gemini API or processing failed: {e}") # FIX 2: Use logging.error
        raise

# --- Main Orchestration Function ---

def process_and_save_resume_info(resume_id: int, file_path: str):
    """Orchestrates the entire process: extract, analyze, save to ResumeInfo, generate PDF, and notify user."""
    db_generator = get_db()
    db = next(db_generator)
    
    telegram_id = None 
    job_title = "Resume"
    
    try:
        # 1. Extract Text
        resume_text = extract_text_from_pdf(file_path)
        
        # 2. Analyze with Gemini
        analysis_data = analyze_resume_with_gemini(resume_text)
        
        logging.info(f"✅ Gemini raw data received for ID {resume_id}.") # FIX 2: Use logging.info
        
        # 3. Find Resume and ResumeInfo records
        # Use a join to efficiently get the user's telegram_id
        resume = db.query(Resume).filter(Resume.id == resume_id).one()
        resume_info = db.query(ResumeInfo).filter(ResumeInfo.resume_id == resume_id).one()

        # Capture data needed for notification *before* DB commit
        telegram_id = resume.user.telegram_id
        job_title = resume.job_title

        # 4. Map data to SQLAlchemy objects and commit
        
        # Simple fields
        resume_info.phone = analysis_data.get('phone')
        resume_info.email = analysis_data.get('email')
        resume_info.linkedin = analysis_data.get('linkedin')
        resume_info.position = analysis_data.get('position_inferred') 
        resume_info.education_level = analysis_data.get('education_level')

        # JSON fields
        resume_info.work_history = analysis_data.get('work_history')
        resume_info.skills = analysis_data.get('skills')
        resume_info.core_values = analysis_data.get('core_values')
        
        # Store the entire structured output
        resume_info.structured_json = analysis_data 
        
        # Set processed flag on the parent Resume record
        resume.processed = True

        db.commit()
        logging.info(f"Successfully processed and saved ResumeInfo for ID: {resume_id}. Data committed.") # FIX 2: Use logging.info

        
        # 5. Generate Harvard-Style PDF
        pdf_path = generate_harvard_pdf(analysis_data, telegram_id)

        # 6. Send the PDF to the user via Telegram
        if pdf_path:
            send_pdf_to_telegram(telegram_id, pdf_path, job_title)
        else:
            logging.warning(f"Skipping Telegram notification: PDF generation failed for {resume_id}.") # FIX 2: Use logging.warning

    except Exception as e:
        db.rollback()
        logging.error(f"Failed to process and save resume info for ID {resume_id}: {e}") # FIX 2: Use logging.error
        
        # Optional: Send a failure notification if processing failed after file upload
        if telegram_id:
            try:
                import telegram
                bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
                bot.send_message(
                    chat_id=telegram_id,
                    text=f"❌ **Resume Analysis Failed**\n\nThere was an error processing your resume for the role: *{job_title}*.",
                    parse_mode='Markdown'
                )
            except Exception as bot_e:
                logging.error(f"Failed to send error notification to Telegram: {bot_e}") # FIX 2: Use logging.error

    finally:
        db_generator.close()
