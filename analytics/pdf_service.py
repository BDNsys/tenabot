# tenabot/analytics/pdf_generation_service.py
import os
import time
import logging
from django.conf import settings

# ReportLab Imports
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
    HRFlowable,
)
from reportlab.lib.units import inch
from reportlab.lib import colors

# Ensure 'name' is defined or use a specific module name
logger = logging.getLogger(__name__)


def generate_harvard_pdf(resume_data: dict, telegram_id: int) -> str | None:
    """Generate a polished Harvard-style resume PDF using ReportLab.

    Args:
        resume_data: Dictionary containing parsed resume content.
        telegram_id: The ID of the user for naming the output file.

    Returns:
        The path to the generated PDF file, or None if generation failed.
    """
    try:
        # --- File Path Setup ---
        output_dir = os.path.join(settings.MEDIA_ROOT, "generated_resumes")
        os.makedirs(output_dir, exist_ok=True)
        
        # Use a timestamp to ensure unique filenames
        filename_base = f"resume_{telegram_id}_{int(time.time())}.pdf"
        pdf_path = os.path.join(output_dir, filename_base)
        
        logger.info(f"🧾 [PDF] Generating Harvard-style resume for user {telegram_id}")
        logger.info(f"🗂 Saving to {pdf_path}")

        # --- Document Setup ---
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        styles = getSampleStyleSheet()
        
        # Define Custom Styles
        styles.add(
            ParagraphStyle(
                name="Header", 
                fontSize=20, 
                leading=24, 
                alignment=1, 
                textColor=colors.HexColor("#1A237E"), 
                fontName="Helvetica-Bold"
            )
        )
        styles.add(
            ParagraphStyle(
                name="SectionTitle", 
                fontSize=13, 
                leading=16, 
                spaceAfter=8, 
                textColor=colors.HexColor("#0D47A1"), 
                fontName="Helvetica-Bold"
            )
        )
        styles.add(
            ParagraphStyle(
                name="JobTitle", 
                fontSize=11, 
                leading=14, 
                spaceAfter=4, 
                textColor=colors.HexColor("#212121"), 
                fontName="Helvetica-Bold"
            )
        )
        styles.add(
            ParagraphStyle(
                name="Body", 
                fontSize=10, 
                leading=13, 
                textColor=colors.HexColor("#424242"), 
                fontName="Helvetica"
            )
        )
        # ✅ Rename here:
        styles.add(
            ParagraphStyle(
                name="ItalicSmall", 
                fontSize=9,
                leading=12,                           
                textColor=colors.HexColor("#555555"), fontName="Helvetica-Oblique"))

        story = []

        # --- Header (Candidate Name / Position Inferred) ---
        title = resume_data.get("position_inferred", "Professional Resume")
        story.append(Paragraph(title, styles["Header"]))
        story.append(Spacer(1, 0.15 * inch))

        # --- Contact Info Box (Table) ---
        contact_data = [
            [f"📞 {resume_data.get('phone', 'N/A')}",
             f"✉️ {resume_data.get('email', 'N/A')}",
             f"🔗 {resume_data.get('linkedin', 'N/A')}"]
        ]
        contact_table = Table(contact_data, colWidths=[2.2 * inch] * 3)
        contact_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1A237E")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(contact_table)
        story.append(Spacer(1, 0.3 * inch))

        # --- Initial Divider ---
        story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
        story.append(Spacer(1, 0.25 * inch))
        # --- Core Values-------
        core_values = resume_data.get("core_values", [])
        if core_values:
            story.append(Paragraph("Core Values", styles["SectionTitle"]))
            story.append(ListFlowable(
                [ListItem(Paragraph(str(v), styles["Body"])) for v in core_values],
                bulletType="bullet",
                start=0.2 * inch
            ))
            story.append(Spacer(1, 0.25 * inch))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
            story.append(Spacer(1, 0.25 * inch))

        # --- Skills ---
        skills = resume_data.get("skills", [])
        if skills:
            story.append(Paragraph("Skills", styles["SectionTitle"]))
            story.append(ListFlowable(
                [ListItem(Paragraph(str(s), styles["Body"])) for s in skills],
                bulletType="bullet",
                start=0.2 * inch
            ))
            story.append(Spacer(1, 0.25 * inch))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
            story.append(Spacer(1, 0.25 * inch))
        # --- Work Experience ---
        work_history = resume_data.get("work_history", [])
        if work_history:
            story.append(Paragraph("Work Experience", styles["SectionTitle"]))
            for job in work_history:
                story.append(Paragraph(f"{job.get('title', 'N/A')} — {job.get('company', 'N/A')}", styles["JobTitle"]))
                story.append(Paragraph(f"{job.get('start_date', '')} - {job.get('end_date', 'Present')}", styles["ItalicSmall"]))
                if job.get("summary"):
                    story.append(Paragraph(job["summary"], styles["Body"]))
                story.append(Spacer(1, 0.15 * inch))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
            story.append(Spacer(1, 0.25 * inch))

        # --- Education ---
        education = resume_data.get("full_education", [])
        if education:
            story.append(Paragraph("Education", styles["SectionTitle"]))
            for edu in education:
                edu_line = (
                    f"**{edu.get('degree', '')}** in {edu.get('field_of_study', '')} "
                    f"from **{edu.get('institution', '')}** ({edu.get('graduation_date', '')})"
                )

                # Convert markdown-like bold (**text**) to <b>text</b> for ReportLab
                import re
                edu_line_html = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", edu_line)

                story.append(Paragraph(edu_line_html, styles["Body"]))
                story.append(Spacer(1, 0.1 * inch))

        # --- Footer ---
        story.append(Spacer(1, 0.3 * inch))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph("Generated by <b>Tenabot AI Resume Assistant</b> using Gemini AI.", styles["ItalicSmall"]))

        # --- Build Document ---
        doc.build(story)
        logger.info(f"✅ [PDF] Successfully created Harvard PDF for {telegram_id}")
        return pdf_path

    except Exception as e:
        logger.error(f"💥 [PDF] Failed to generate Harvard PDF for {telegram_id}: {e}", exc_info=True)
        return None