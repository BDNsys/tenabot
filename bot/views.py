from django.shortcuts import render
import os
from datetime import date
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
# --- UPDATED IMPORTS ---
from rest_framework.authentication import SessionAuthentication # Use SessionAuth
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import threading # Added for background processing

# Import Serializer
from .serializers import ResumeUploadSerializer ,ResumeListSerializer,ResumeInfoSerializer

# Import SQLAlchemy components
from tenabot.db import get_db
from .models import Resume, ResumeInfo, UsageTracker, User as SQLAlchemyUser # Alias User to avoid conflict
from sqlalchemy.orm.exc import NoResultFound

# Import the new analytics service
from analytics.services import process_and_save_resume_info 


# Create your views here.


def home(request):
    return render(request, 'bot/bot.html')


# Re-apply csrf_exempt here, as the client (Telegram Web App) cannot reliably provide the token.
@method_decorator(csrf_exempt, name='dispatch')
class ResumeUploadView(APIView):
    """
    Handles PDF file upload, validation, and creation of associated SQLAlchemy models.
    """
    # Use SessionAuthentication because the user is logged in via the Django 'login' function.
    authentication_classes = [SessionAuthentication]
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
        
        new_resume_id = None # Initialize to capture ID
        
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
            new_resume_id = new_resume.id # Capture the ID

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
            
            # 4. Trigger the Resume Analysis in a separate thread
            # This makes the API response fast while processing runs in the background.
            threading.Thread(
                target=process_and_save_resume_info,
                args=(new_resume_id, db_file_path)
            ).start()


            return Response({
                "message": "Resume uploaded and records created successfully. Analysis started in background.",
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
            # 5. Close the SQLAlchemy session
            db_generator.close()
            
            


class ResumeListView(APIView):
    """
    Returns a public, paginated list of all uploaded resumes.
    Uses SQLAlchemy for data access and custom logic for pagination.
    """
    # The user requested that this view is not protected by auth.
    permission_classes = [permissions.AllowAny] 

    def get(self, request, *args, **kwargs):
        db_generator = get_db()
        db = next(db_generator)
        
        try:
            # 1. Pagination Parameters
            # Default to page 1, size 10. Max size is capped at 50 for safety.
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 10))
            page_size = min(page_size, 50) # Safety limit
            offset = (page - 1) * page_size
            
            # 2. Get total count for pagination headers
            # Note: count() executes a separate query optimized for counting.
            total_count = db.query(Resume).count()
            
            # 3. Fetch paginated data using SQLAlchemy's limit and offset
            resumes = db.query(Resume).order_by(
                Resume.created_at.desc()
            ).limit(page_size).offset(offset).all()

            # 4. Serialize data
            serializer = ResumeListSerializer(resumes, many=True)
            
            # 5. Return paginated response
            response_data = {
                "count": total_count,
                "page": page,
                "page_size": page_size,
                "results": serializer.data,
            }
            
            return Response(response_data, status=status.HTTP_200_OK)

        except ValueError:
            # Handles non-integer values for page or page_size
            return Response({"detail": "Invalid page or page_size parameter."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Error fetching resumes: {e}")
            return Response({"detail": "A server error occurred while fetching resumes."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        finally:
            # 4. Close the SQLAlchemy session
            db_generator.close()
            

class ResumeInfoListView(APIView):
    """
    Returns a public, paginated list of all uploaded resumes.
    Uses SQLAlchemy for data access and custom logic for pagination.
    """
    # The user requested that this view is not protected by auth.
    permission_classes = [permissions.AllowAny] 

    def get(self, request, *args, **kwargs):
        db_generator = get_db()
        db = next(db_generator)
        
        try:
            # 1. Pagination Parameters
            # Default to page 1, size 10. Max size is capped at 50 for safety.
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 10))
            page_size = min(page_size, 50) # Safety limit
            offset = (page - 1) * page_size
            
            # 2. Get total count for pagination headers
            # Note: count() executes a separate query optimized for counting.
            total_count = db.query(Resume).count()
            
            # 3. Fetch paginated data using SQLAlchemy's limit and offset
            resumes = db.query(ResumeInfo).order_by(
                ResumeInfo.created_at.desc()
            ).limit(page_size).offset(offset).all()

            # 4. Serialize data
            serializer = ResumeInfoSerializer(resumes, many=True)
            
            # 5. Return paginated response
            response_data = {
                "count": total_count,
                "page": page,
                "page_size": page_size,
                "results": serializer.data,
            }
            
            return Response(response_data, status=status.HTTP_200_OK)

        except ValueError:
            # Handles non-integer values for page or page_size
            return Response({"detail": "Invalid page or page_size parameter."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Error fetching resumes: {e}")
            return Response({"detail": "A server error occurred while fetching resumes."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        finally:
            # 4. Close the SQLAlchemy session
            db_generator.close()

