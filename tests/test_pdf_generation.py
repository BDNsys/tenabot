import os
import logging
from django.test import TestCase
from django.conf import settings
from analytics import pdf_service

logger = logging.getLogger(__name__)

class PDFGenerationTest(TestCase):
    def setUp(self):
        self.resume_data = {
            "position_inferred": "Backend Developer",
            "phone": "+251 954 988 574",
            "email": "nazrawigedion23@gmail.com",
            "linkedin": "linkedin.com/in/nazrawi-gedion",
            "core_values": [
                "Results-driven",
                "Code Quality and Maintainability",
                "Collaboration",
                "Scalable Architecture Design",
            ],
            "skills": [
                "Golang (Go)",
                "Gin",
                "Django",
                "React.js",
                "PostgreSQL",
                "Docker",
                "Git",
            ],
            "work_history": [
                {
                    "title": "Golang Developer",
                    "company": "OneTap Technology",
                    "start_date": "Jun 2025",
                    "end_date": "Present",
                    "summary": "Developed Go microservices and APIs for core banking integration.",
                },
                {
                    "title": "Backend Developer",
                    "company": "BDN",
                    "start_date": "Sep 2024",
                    "end_date": "Present",
                    "summary": "Built scalable apps with Django and Gin; contributed to e-learning platform.",
                },
            ],
            "full_education": [
                {
                    "degree": "BSc",
                    "field_of_study": "Computer Science",
                    "institution": "University of Gondar",
                    "graduation_date": "2021",
                }
            ],
        }

    def test_pdf_generation(self):
        telegram_id = 9999
        output_path = pdf_service.generate_harvard_pdf(self.resume_data, telegram_id)
        self.assertIsNotNone(output_path, "PDF generation returned None — it failed somewhere.")
        self.assertTrue(os.path.exists(output_path), "PDF file not created.")
        size = os.path.getsize(output_path)
        logger.info(f"✅ PDF generated successfully at: {output_path} ({size / 1024:.2f} KB)")
        print(f"✅ PDF generated successfully: {output_path} ({size / 1024:.2f} KB)")
