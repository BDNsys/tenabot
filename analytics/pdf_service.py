# tenabot/analytics/pdf_generation_service.py
import os
import time
import logging
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
    Table,
    TableStyle,
)
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

logger = logging.getLogger(__name__)

def register_custom_fonts():
    """Register custom fonts for better typography"""
    try:
        # Try to register common professional fonts
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/System/Library/Fonts/Helvetica.ttc',  # macOS
            'C:/Windows/Fonts/arial.ttf'  # Windows
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Helvetica', font_path))
                pdfmetrics.registerFont(TTFont('Helvetica-Bold', font_path))
                break
    except:
        # Fall back to default fonts
        pass

def generate_harvard_pdf(resume_data, telegram_id):
    """Generate a visually appealing Harvard-style resume PDF using ReportLab."""
    try:
        output_dir = os.path.join(settings.MEDIA_ROOT, "generated_resumes")
        os.makedirs(output_dir, exist_ok=True)

        filename_base = f"resume_{telegram_id}_{int(time.time())}.pdf"
        pdf_path = os.path.join(output_dir, filename_base)

        logger.info(f"🧾 [PDF] Generating Harvard-style resume for user {telegram_id}")
        logger.info(f"🗂 Saving to {pdf_path}")

        # Register custom fonts
        register_custom_fonts()

        # --- Document setup with better margins ---
        doc = SimpleDocTemplate(
            pdf_path, 
            pagesize=A4, 
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch
        )
        
        styles = getSampleStyleSheet()
        
        # --- Custom Styles for Harvard Design ---
        # Header style
        styles.add(ParagraphStyle(
            name="Header",
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=colors.HexColor("#2C3E50"),  # Dark blue-gray
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Contact info style
        styles.add(ParagraphStyle(
            name="Contact",
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor("#34495E"),
            alignment=TA_CENTER,
            spaceAfter=18
        ))
        
        # Section headers with underline
        styles.add(ParagraphStyle(
            name="SectionHeader",
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=colors.HexColor("#2C3E50"),
            spaceAfter=6,
            spaceBefore=12,
            borderPadding=(0, 0, 0, 0),
            leftIndent=0
        ))
        
        # Job title style
        styles.add(ParagraphStyle(
            name="JobTitle",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.HexColor("#2C3E50"),
            spaceAfter=2
        ))
        
        # Company and date style
        styles.add(ParagraphStyle(
            name="CompanyDate",
            fontName="Helvetica-Oblique",
            fontSize=9,
            textColor=colors.HexColor("#7F8C8D"),
            spaceAfter=6
        ))
        
        # Bullet point style
        styles.add(ParagraphStyle(
            name="Bullet",
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor("#2C3E50"),
            leftIndent=0,
            spaceAfter=3
        ))
        
        # Normal text style
        styles.add(ParagraphStyle(
            name="BodyText",
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor("#2C3E50"),
            leading=11,
            spaceAfter=6
        ))

        story = []

        # --- Header with professional styling ---
        title = resume_data.get("position_inferred", "Professional Resume")
        story.append(Paragraph(f"{title}", styles["Header"]))
        
        # --- Contact Info as centered line ---
        contact_parts = []
        if resume_data.get('phone'):
            contact_parts.append(f"📱 {resume_data['phone']}")
        if resume_data.get('email'):
            contact_parts.append(f"✉️ {resume_data['email']}")
        if resume_data.get('linkedin') and resume_data['linkedin'] != 'None':
            contact_parts.append(f"🔗 {resume_data['linkedin']}")
        
        contact_line = " | ".join(contact_parts)
        story.append(Paragraph(contact_line, styles["Contact"]))
        
        # Add a subtle separator line
        story.append(Spacer(1, 0.1 * inch))
        story.append(Table(
            [[""]], 
            colWidths=[doc.width],
            style=TableStyle([
                ('LINEABOVE', (0, 0), (-1, -1), 1, colors.HexColor("#BDC3C7")),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ])
        ))

        # Two column layout for Core Values and Skills
        core_values = resume_data.get("core_values", [])
        skills = resume_data.get("skills", [])
        
        if core_values or skills:
            # Create two columns table
            col1_content = []
            col2_content = []
            
            if core_values:
                col1_content.append(Paragraph("CORE VALUES", styles["SectionHeader"]))
                for value in core_values:
                    col1_content.append(ListItem(Paragraph(f"• {value}", styles["Bullet"])))
                col1_content.append(Spacer(1, 0.1 * inch))
            
            if skills:
                col2_content.append(Paragraph("TECHNICAL SKILLS", styles["SectionHeader"]))
                for skill in skills:
                    col2_content.append(ListItem(Paragraph(f"• {skill}", styles["Bullet"])))
                col2_content.append(Spacer(1, 0.1 * inch))
            
            # Create table for two columns
            if col1_content and col2_content:
                two_col_table = Table(
                    [[col1_content, col2_content]], 
                    colWidths=[doc.width/2 - 10, doc.width/2 - 10],
                    style=TableStyle([
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                    ])
                )
                story.append(two_col_table)
            elif col1_content:
                story.extend(col1_content)
            elif col2_content:
                story.extend(col2_content)
                
            story.append(Spacer(1, 0.2 * inch))

        # --- Work Experience with improved layout ---
        work_history = resume_data.get("work_history", [])
        if work_history:
            story.append(Paragraph("PROFESSIONAL EXPERIENCE", styles["SectionHeader"]))
            
            for job in work_history:
                # Job title and company
                title_line = f"{job.get('title', 'N/A')}"
                company_line = f"{job.get('company', 'N/A')}"
                
                story.append(Paragraph(title_line, styles["JobTitle"]))
                story.append(Paragraph(company_line, styles["CompanyDate"]))
                
                # Date range
                date_line = f"{job.get('start_date', '')} - {job.get('end_date', '')}"
                story.append(Paragraph(date_line, styles["CompanyDate"]))
                
                # Job description/summary
                if job.get("summary"):
                    # Split summary into bullet points if it's a long text
                    summary_text = job["summary"]
                    if len(summary_text) > 100:  # If it's long, create bullet points
                        sentences = [s.strip() for s in summary_text.split('.') if s.strip()]
                        for sentence in sentences[:4]:  # Limit to 4 key points
                            story.append(ListItem(Paragraph(f"• {sentence}", styles["BodyText"])))
                    else:
                        story.append(Paragraph(summary_text, styles["BodyText"]))
                
                story.append(Spacer(1, 0.15 * inch))

        # --- Education section ---
        education = resume_data.get("full_education", [])
        if education:
            story.append(Paragraph("EDUCATION", styles["SectionHeader"]))
            for edu in education:
                degree = edu.get('degree', '')
                field = edu.get('field_of_study', '')
                institution = edu.get('institution', '')
                grad_date = edu.get('graduation_date', '')
                
                edu_line_parts = []
                if degree:
                    edu_line_parts.append(degree)
                if field:
                    edu_line_parts.append(field)
                
                edu_line = ", ".join(edu_line_parts)
                if institution:
                    edu_line += f" - {institution}"
                if grad_date:
                    edu_line += f" ({grad_date})"
                
                story.append(Paragraph(edu_line, styles["JobTitle"]))
                story.append(Spacer(1, 0.1 * inch))

        # --- Footer with subtle styling ---
        story.append(Spacer(1, 0.3 * inch))
        story.append(Table(
            [[""]], 
            colWidths=[doc.width],
            style=TableStyle([
                ('LINEABOVE', (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ])
        ))
        
        footer_style = ParagraphStyle(
            name="Footer",
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=colors.HexColor("#7F8C8D"),
            alignment=TA_CENTER,
            spaceBefore=6
        )
        
        story.append(Paragraph(
            "Generated by Tenabot AI Resume Assistant using Gemini AI",
            footer_style
        ))

        # Build the document
        doc.build(story)
        
        # Log file size for debugging
        file_size = os.path.getsize(pdf_path)
        logger.info(f"✅ [PDF] Successfully created Harvard PDF for {telegram_id} - Size: {file_size} bytes")
        
        return pdf_path

    except Exception as e:
        logger.error(f"💥 [PDF] Failed to generate Harvard PDF for {telegram_id}: {e}", exc_info=True)
        return None