from rest_framework import serializers
from django.core.files.uploadedfile import UploadedFile

class ResumeUploadSerializer(serializers.Serializer):
    """
    Serializer for handling PDF file uploads and size validation.
    """
    # Use a FileField to handle the upload
    pdf_file = serializers.FileField(label="Resume PDF File")
    
    # New field to capture the job title
    job_title = serializers.CharField(max_length=150) 
    
    # 7 MB limit in bytes (7 * 1024 * 1024)
    MAX_FILE_SIZE = 7340032 

    def validate_pdf_file(self, value: UploadedFile):
        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError("PDF file size must not exceed 7 MB.")
        
        # Simple check for file extension
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("File must be a PDF.")

        return value