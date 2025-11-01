from django.shortcuts import render
import os
from datetime import date
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
# --- NEW/UPDATED IMPORTS ---
from rest_framework.authentication import TokenAuthentication
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Import Serializer
from .serializers import ResumeUploadSerializer 

# Import SQLAlchemy components
from tenabot.db import get_db
from .models import Resume, ResumeInfo, UsageTracker, User as SQLAlchemyUser # Alias User to avoid conflict
from sqlalchemy.orm.exc import NoResultFound



# Create your views here.


def home(request):
    return render(request, 'bot/bot.html')


# Removed @method_decorator(csrf_exempt, name='dispatch')
class ResumeUploadView(APIView):
    """
    Handles PDF file upload, validation, and creation of associated SQLAlchemy models.
    
    Uses TokenAuthentication, which makes it inherently safe from CSRF attacks
    and removes the need for the csrf_exempt decorator.
    """
    # Use TokenAuthentication for session-less, CSRF-exempt API usage
    authentication_classes = [TokenAuthentication] 
    # Use Django's IsAuthenticated permission
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # 1. Validation & Authentication
        serializer = ResumeUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        pdf_file = serializer.validated_data['pdf_file']
        job_title = serializer.validated_data['job_title']
        
        # The Django User is available via request.user
        django_user = request.user 
        
        # 2. File Saving Logic
        
        # Define the target media subdirectory
        pdf_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs')
        os.makedirs(pdf_dir, exist_ok=True)
        
        # Construct a unique file path (Good practice: use telegram_id/pk + unique name)
        # Using the file's original name here for simplicity, but a UUID is better in production.
        filename = f"{django_user.telegram_id}_{pdf_file.name}"
        file_path = os.path.join(pdf_dir, filename)
        
        # Save the file to the media directory
        try:
            with open(file_path, 'wb+') as destination:
                for chunk in pdf_file.chunks():
                    destination.write(chunk)
            
            # The path stored in the DB should be relative to MEDIA_ROOT
            db_file_path = os.path.join('pdfs', filename)
            
        except Exception as e:
            return Response({"detail": f"File saving failed: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
        # 3. SQLAlchemy Model Creation and Transaction Management
        
        # Use the SQLAlchemy dependency helper
        db_generator = get_db()
        db = next(db_generator) # Get the session object
        
        try:
            # 3a. Find the SQLAlchemy User ID
            # Assuming your Django User's 'telegram_id' maps to the SQLAlchemy User's 'telegram_id'
            try:
                # This finds the SQLAlchemy User corresponding to the authenticated Django User
                sqla_user = db.query(SQLAlchemyUser).filter(
                    SQLAlchemyUser.telegram_id == django_user.telegram_id
                ).one()
                user_id = sqla_user.id
            except NoResultFound:
                # Handle case where Django User exists but SQLa User doesn't (shouldn't happen in a stable system)
                return Response({"detail": "Corresponding SQLAlchemy User not found."}, status=status.HTTP_404_NOT_FOUND)

            # 3b. Create Resume Record
            new_resume = Resume(
                user_id=user_id,
                file_path=db_file_path,
                job_title=job_title
            )
            db.add(new_resume)
            db.flush() # Flush to get the new_resume.id

            # 3c. Create Initial ResumeInfo Record (Optional but good practice)
            new_resume_info = ResumeInfo(
                resume_id=new_resume.id,
                # Other fields will be NULL/default until parsing occurs
            )
            db.add(new_resume_info)

            # 3d. Update/Create UsageTracker
            today = date.today()
            usage = db.query(UsageTracker).filter(
                UsageTracker.user_id == user_id
            ).one_or_none()

            if usage:
                # Update existing usage
                if usage.date == today:
                    usage.count += 1
                else:
                    # Reset count for a new day
                    usage.date = today
                    usage.count = 1
            else:
                # Create new usage tracker record
                usage = UsageTracker(user_id=user_id, count=1)
                db.add(usage)
            
            # Commit all changes to the database
            db.commit()

            return Response({
                "message": "Resume uploaded and records created successfully.",
                "resume_id": new_resume.id,
                "file_path": db_file_path,
                "uploads_today": usage.count
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            # Rollback in case of any database error
            db.rollback()
            # Clean up the saved file on failure
            if os.path.exists(file_path):
                 os.remove(file_path)
            return Response({"detail": f"Database transaction failed: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        finally:
            # 4. Close the SQLAlchemy session
            db_generator.close()
