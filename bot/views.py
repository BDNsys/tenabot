import logging
import os
from datetime import date
import threading

from django.conf import settings
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import SessionAuthentication

from sqlalchemy.orm.exc import NoResultFound

# Local/Project Imports
from .serializers import ResumeUploadSerializer, ResumeListSerializer, ResumeInfoSerializer
from tenabot.db import get_db
from .models import Resume, ResumeInfo, UsageTracker, User as SQLAlchemyUser
from analytics.services import process_and_save_resume_info

# Initialize logger
# Assuming 'name' is defined or replaced with '__name__'
logger = logging.getLogger(__name__) 

# --- Django Views ---

def home(request):
    """Simple view to render the base page."""
    return render(request, 'bot/bot.html')



""" 💾 Resume Upload View (`ResumeUploadView`)

This view handles the resume file upload, saves it to disk, creates database records (Resume, ResumeInfo, UsageTracker), and **asynchronously** launches the AI processing service. 
"""
@method_decorator(csrf_exempt, name='dispatch')
class ResumeUploadView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logger.info("📥 [UPLOAD INIT] Incoming resume upload request.")
        
        # 1. Validation and Authentication
        serializer = ResumeUploadSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"⚠️ Validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        pdf_file = serializer.validated_data['pdf_file']
        job_title = serializer.validated_data['job_title']
        django_user = request.user

        logger.info(f"👤 Authenticated user: {django_user.username} (telegram_id={django_user.telegram_id})")

        # 2. File Saving Logic
        pdf_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs')
        os.makedirs(pdf_dir, exist_ok=True)
        filename = f"{django_user.telegram_id}_{pdf_file.name}"
        file_path = os.path.join(pdf_dir, filename)
        db_file_path = os.path.join('pdfs', filename) # Relative path for DB

        try:
            with open(file_path, 'wb+') as destination:
                for chunk in pdf_file.chunks():
                    destination.write(chunk)
            logger.info(f"✅ File saved successfully: {file_path}")
        except Exception as e:
            logger.error(f"❌ File saving failed: {e}", exc_info=True)
            return Response({"detail": f"File saving failed: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 3. Database Transaction (SQLAlchemy)
        db_gen = get_db()
        db = next(db_gen)
        new_resume_id = None

        try:
            # Map Django user to SQLAlchemy user
            sqla_user = db.query(SQLAlchemyUser).filter(SQLAlchemyUser.telegram_id == django_user.telegram_id).one_or_none()
            if not sqla_user:
                logger.error("❌ SQLAlchemy user not found for this telegram_id.")
                return Response({"detail": "Corresponding SQLAlchemy User not found."}, status=status.HTTP_404_NOT_FOUND)
            user_id = sqla_user.id

            # Create Resume Record
            new_resume = Resume(user_id=user_id, file_path=db_file_path, job_title=job_title)
            db.add(new_resume)
            db.flush() # Get ID before commit
            new_resume_id = new_resume.id
            logger.info(f"🧾 Created Resume ID={new_resume_id}")

            # Create ResumeInfo Placeholder
            new_resume_info = ResumeInfo(resume_id=new_resume.id)
            db.add(new_resume_info)
            logger.debug("📄 Placeholder ResumeInfo created.")

            # Update Usage Tracker
            today = date.today()
            usage = db.query(UsageTracker).filter(UsageTracker.user_id == user_id).one_or_none()
            if usage and usage.date == today:
                usage.count += 1
                logger.debug(f"🔁 Updated usage count for today: {usage.count}")
            else:
                usage = UsageTracker(user_id=user_id, date=today, count=1)
                db.add(usage)
                logger.debug("🆕 Created new usage tracker entry.")

            db.commit()
            logger.info(f"💾 [COMMIT] Database committed successfully for resume_id={new_resume_id}")

            # 4. Asynchronous Processing
            threading.Thread(
                target=process_and_save_resume_info, 
                args=(new_resume_id, db_file_path)
            ).start()
            logger.info(f"🚀 [THREAD START] Background resume analysis launched for resume_id={new_resume_id}")

            return Response({
                "message": "Resume uploaded successfully. Processing started in background.",
                "resume_id": new_resume.id,
                "file_path": db_file_path,
                "uploads_today": usage.count
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            db.rollback() # Rollback on any transaction error
            logger.error(f"💥 [ROLLBACK] Transaction failed: {e}", exc_info=True)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.warning(f"🧹 Cleaned up file: {file_path}")
            return Response({"detail": f"Database transaction failed: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            db_gen.close()
            logger.info("🔚 [UPLOAD END] Database session closed.")



""" 📑 Resume List Views

These views provide paginated read access to the database records.

 Resume List (`ResumeListView`)"""

class ResumeListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        logger.info("📄 [LIST] Fetching paginated resumes.")
        db_gen = get_db()
        db = next(db_gen)
        try:
            # Pagination Logic
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 10)), 50)
            offset = (page - 1) * page_size
            
            # Fetch Data
            total = db.query(Resume).count()
            resumes = db.query(Resume).order_by(Resume.created_at.desc()).limit(page_size).offset(offset).all()
            logger.debug(f"📦 Retrieved {len(resumes)} resumes from DB (page={page}, size={page_size})")

            # Response
            data = ResumeListSerializer(resumes, many=True).data
            return Response({"count": total, "page": page, "page_size": page_size, "results": data})
            
        except Exception as e:
            logger.error(f"❌ Error fetching resumes: {e}", exc_info=True)
            return Response({"detail": "A server error occurred while fetching resumes."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            db_gen.close()
            logger.info("🔚 [LIST END] Database session closed.")

### Resume Info List (`ResumeInfoListView`)

class ResumeInfoListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        logger.info("📊 [INFO LIST] Fetching resume info list.")
        db_gen = get_db()
        db = next(db_gen)
        try:
            # Pagination Logic
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 10)), 50)
            offset = (page - 1) * page_size
            
            # Fetch Data
            total = db.query(ResumeInfo).count()
            infos = db.query(ResumeInfo).order_by(ResumeInfo.created_at.desc()).limit(page_size).offset(offset).all()
            logger.debug(f"📦 Retrieved {len(infos)} resume info records (page={page}, size={page_size})")

            # Response
            data = ResumeInfoSerializer(infos, many=True).data
            return Response({"count": total, "page": page, "page_size": page_size, "results": data})
            
        except Exception as e:
            logger.error(f"❌ Error fetching resume info: {e}", exc_info=True)
            return Response({"detail": "A server error occurred while fetching resume info."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            db_gen.close()
            logger.info("🔚 [INFO LIST END] Database session closed.")