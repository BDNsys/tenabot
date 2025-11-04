import unittest
import os
import time
from unittest.mock import patch, MagicMock
import json

# Assuming your service file is named pdf_service.py and the functions are imported
# from .pdf_service import generate_harvard_pdf, clean_list_data
# For this example, we'll assume it's imported globally for simplicity
from analytics.pdf_service import generate_harvard_pdf # Adjust import path as needed

# --- Define a Mock Settings Object ---
class MockSettings:
    MEDIA_ROOT = '/mock/media/'

# --- Sample Resume Data for Testing ---
SAMPLE_RESUME_DATA = {
    "position_inferred": "Senior Software Engineer",
    "phone": "123-456-7890",
    "email": "test@example.com",
    "linkedin": "linkedin.com/in/testuser",
    "core_values": [
        "Innovation",
        "Teamwork",
        "Customer Focus",
        1.0, # Test case: float
        None, # Test case: None
        "" # Test case: empty string
    ],
    "skills": [
        "Python",
        "Django",
        "React",
        "AWS",
        "0.9", # Test case: string number
    ],
    "work_history": [
        {
            "title": "Lead Developer",
            "company": "Tech Corp",
            "start_date": "Jan 2020",
            "end_date": "Present",
            "summary": "Led team of 5 developers on project X. Delivered 2 major features.",
        },
        {
            "title": "Junior Developer",
            "company": "Startup Co.",
            "start_date": "Jan 2018",
            "end_date": "Dec 2019",
            "summary": None, # Test case: None summary
        },
    ],
    "full_education": [
        {
            "degree": "M.S.",
            "field_of_study": "Computer Science",
            "institution": "State University",
            "graduation_date": "2017",
        }
    ]
}


class PdfServiceTest(unittest.TestCase):
    
    # Patch all external dependencies
    @patch('analytics.pdf_service.settings', MockSettings)
    @patch('analytics.pdf_service.os.makedirs')
    @patch('analytics.pdf_service.time.time', return_value=1678886400) # Fixed timestamp for predictable filename
    @patch('analytics.pdf_service.SimpleDocTemplate')
    def test_generate_harvard_pdf_success(self, MockDocTemplate, mock_time, mock_makedirs):
        
        # --- Arrange ---
        telegram_id = 12345
        
        # Mock the SimpleDocTemplate instance and its build method
        mock_doc_instance = MagicMock()
        MockDocTemplate.return_value = mock_doc_instance
        
        # Expected PDF path based on mock settings and time
        expected_filename = f"resume_{telegram_id}_{int(mock_time.return_value)}.pdf"
        expected_path = os.path.join(MockSettings.MEDIA_ROOT, "generated_resumes", expected_filename)
        
        # --- Act ---
        result_path = generate_harvard_pdf(SAMPLE_RESUME_DATA, telegram_id)
        
        # --- Assert ---
        
        # 1. Check if the expected path was returned
        self.assertEqual(result_path, expected_path, "Should return the expected PDF file path.")
        
        # 2. Check if output directory was created
        mock_makedirs.assert_called_once_with(
            os.path.join(MockSettings.MEDIA_ROOT, "generated_resumes"), 
            exist_ok=True
        )
        
        # 3. Check if ReportLab document was initialized with the correct path
        MockDocTemplate.assert_called_once()
        self.assertEqual(MockDocTemplate.call_args[0][0], expected_path)
        
        # 4. Check if the 'build' method was called
        mock_doc_instance.build.assert_called_once()
        
        # 5. Check the contents (story flowables)
        # The 'story' list contains all the elements passed to doc.build()
        story = mock_doc_instance.build.call_args[0][0]
        
        # Check basic count (Spacers, HRFlowables, Paragraphs, Tables, ListFlowables)
        self.assertGreater(len(story), 20, "Story should contain many elements (header, sections, etc.).")
        
        # Check for successful rendering of cleaned list data (Core Values)
        # We expect 3 core values (1.0, None, "" should be cleaned out)
        core_values_flowable = story[story.index(story[-1]) - 14] # Approx index of ListFlowable for Core Values
        
        self.assertIsInstance(core_values_flowable, ListFlowable)
        self.assertEqual(len(core_values_flowable.content), 3, "Core Values list should be cleaned to contain exactly 3 items.")
        
        # Check work history count
        work_history_flowables = [f for f in story if isinstance(f, Paragraph) and f.style.name == 'JobTitle']
        self.assertEqual