# tenabot/analytics/pdf_generation_service.py

import os
import time
import logging
from django.conf import settings
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
    Table,  # Added for contact info
    TableStyle, # Added for contact info style
    HRFlowable, # Added for horizontal rules
)
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Paragraph

logger = logging.getLogger(__name__)

from math import ceil


def split_in_two_columns(items):
    """Split list roughly in half for two-column layout."""
    half = ceil(len(items) / 2)
    return items[:half], items[half:]

# --- Helper Function to Clean List Data (Prevents 'float' errors) ---
def clean_list_data(data_list: list) -> list:
    """Ensure list only contains clean strings (no floats or None)."""
    if not isinstance(data_list, list):
        return []

    cleaned_list = []
    for item in data_list:
        try:
            if item is None:
                continue
            if isinstance(item, (float, int)):
                # Ignore numeric-only entries (likely invalid text)
                continue
            item_str = str(item).strip()
            if item_str and item_str.lower() != "none":
                cleaned_list.append(item_str)
        except Exception as e:
            logger.warning(f"[PDF CLEAN] Failed to clean list item {item}: {e}")
    return cleaned_list

# -------------------------------------------------------------------

def generate_harvard_pdf(resume_data: dict, telegram_id: int) -> str | None:
    def format_link(label, url, icon=""):
        if not url:
            return ""
        url = url.strip()
        return Paragraph(
            f"{icon} {label}: <link href='{url}' color='blue'>{url}</link>",
            styles["Body"]
        )
    """Generate a clean and visually appealing Harvard-style resume PDF."""
    try:
        # --- File Path Setup ---
        output_dir = os.path.join(settings.MEDIA_ROOT, "generated_resumes")
        os.makedirs(output_dir, exist_ok=True)
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

        # --- Colors ---
        DARK_BLUE = colors.HexColor("#1E3A8A")
        LIGHT_GREY = colors.HexColor("#F3F4F6")
        TEXT_DARK = colors.HexColor("#1F2937")

        # --- Custom Styles ---
        styles.add(
            ParagraphStyle(
                name="Header",
                fontSize=22,
                leading=26,
                alignment=1,
                textColor=DARK_BLUE,
                fontName="Helvetica-Bold",
            )
        )
        styles.add(
            ParagraphStyle(
                name="SubHeader",
                fontSize=13,
                leading=16,
                alignment=1,
                textColor=TEXT_DARK,
                fontName="Helvetica",
            )
        )
        styles.add(
            ParagraphStyle(
                name="SectionTitle",
                fontSize=13,
                leading=16,
                spaceBefore=6,
                spaceAfter=4,
                textColor=DARK_BLUE,
                fontName="Helvetica-Bold",
            )
        )
        styles.add(
            ParagraphStyle(
                name="JobTitle",
                fontSize=11,
                leading=14,
                spaceAfter=2,
                textColor=TEXT_DARK,
                fontName="Helvetica-Bold",
            )
        )
        styles.add(
            ParagraphStyle(
                name="Body",
                fontSize=10,
                leading=13,
                textColor=TEXT_DARK,
                fontName="Helvetica",
            )
        )
        styles.add(
            ParagraphStyle(
                name="DateItalic",
                fontSize=9,
                leading=12,
                textColor=colors.HexColor("#6B7280"),
                fontName="Helvetica-Oblique",
            )
        )

        # --- Story Start ---
        story = []

        # --- Header (Name + Position) ---
        name = str(resume_data.get("name", "Unnamed Candidate"))
        position = str(resume_data.get("position_inferred", "Professional Resume"))

        story.append(Paragraph(name, styles["Header"]))
        story.append(Paragraph(position, styles["SubHeader"]))
        story.append(Spacer(1, 0.15 * inch))

        # --- Contact Info ---
         # --- Contact Info ---
        phone = resume_data.get("phone")
        email = resume_data.get("email")
        linkedin_url = resume_data.get("linkedin")
        github_url = resume_data.get("github")

        # Build contact info rows dynamically
        contact_cells = []

        basic_info = []
        if phone:
            basic_info.append(Paragraph(f"📞 Phone: {phone}", styles["Body"]))
        if email:
            basic_info.append(Paragraph(f"✉️ Email: {email}", styles["Body"]))

        social_info = []
        if linkedin_url:
            social_info.append(format_link("LinkedIn", linkedin_url, "🔗"))
        if github_url:
            social_info.append(format_link("GitHub", github_url, "🐙"))

        contact_cells = []
        if basic_info:
            contact_cells.append(basic_info)
        if social_info:
            contact_cells.append(social_info)

        # Only build table if there is data
        if contact_cells:
            contact_table = Table(contact_cells, colWidths=[3.2 * inch, 3.2 * inch])
            contact_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
                ("TEXTCOLOR", (0, 0), (-1, -1), DARK_BLUE),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.white),
            ]))
            story.append(contact_table)
            story.append(Spacer(1, 0.3 * inch))

        # --- Core Values ---
        core_values = clean_list_data(resume_data.get("core_values", []))
        if core_values:
            story.append(Paragraph("Core Values", styles["SectionTitle"]))
            col1, col2 = split_in_two_columns(core_values)
            col1_items = [Paragraph(f"• {v}", styles["Body"]) for v in col1]
            col2_items = [Paragraph(f"• {v}", styles["Body"]) for v in col2]
            core_table = Table([[col1_items, col2_items]], colWidths=[3.2 * inch, 3.2 * inch])
            core_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
            story.append(core_table)
            story.append(Spacer(1, 0.25 * inch))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
            story.append(Spacer(1, 0.25 * inch))

        # --- Skills ---
        skills = clean_list_data(resume_data.get("skills", []))
        if skills:
            story.append(Paragraph("Skills", styles["SectionTitle"]))
            col1, col2 = split_in_two_columns(skills)
            col1_items = [Paragraph(f"• {s}", styles["Body"]) for s in col1]
            col2_items = [Paragraph(f"• {s}", styles["Body"]) for s in col2]
            skill_table = Table([[col1_items, col2_items]], colWidths=[3.2 * inch, 3.2 * inch])
            skill_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
            story.append(skill_table)
            story.append(Spacer(1, 0.25 * inch))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
            story.append(Spacer(1, 0.25 * inch))

        # --- Work Experience ---
        work_history = resume_data.get("work_history", [])
        if work_history:
            story.append(Paragraph("Work Experience", styles["SectionTitle"]))
            for job in work_history:
                title_company = f"<b>{str(job.get('title', 'N/A'))}</b> — {str(job.get('company', 'N/A'))}"
                story.append(Paragraph(title_company, styles["JobTitle"]))
                dates = f"{str(job.get('start_date', ''))} - {str(job.get('end_date', 'Present'))}"
                story.append(Paragraph(dates, styles["DateItalic"]))
                if job.get("summary"):
                    story.append(Paragraph(str(job["summary"]), styles["Body"]))
                story.append(Spacer(1, 0.15 * inch))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
            story.append(Spacer(1, 0.25 * inch))

        # --- Education ---
        education = resume_data.get("full_education", [])
        if education:
            story.append(Paragraph("Education", styles["SectionTitle"]))
            for edu in education:
                edu_line = (
                    f"<b>{str(edu.get('degree', ''))}</b> in {str(edu.get('field_of_study', ''))} "
                    f"from <b>{str(edu.get('institution', ''))}</b> "
                    f"({str(edu.get('graduation_date', ''))})"
                )
                story.append(Paragraph(edu_line, styles["Body"]))
                story.append(Spacer(1, 0.1 * inch))

        # --- Footer ---
        story.append(Spacer(1, 0.3 * inch))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(
            "Generated by <b>Tenabot AI Resume Assistant</b> using Gemini AI.",
            styles["DateItalic"]
        ))

        # --- Build Document ---
        doc.build(story)
        logger.info(f"✅ [PDF] Successfully created Harvard PDF for {telegram_id}")
        return pdf_path

    except Exception as e:
        logger.error(f"💥 [PDF] Failed to generate Harvard PDF for {telegram_id}: {e}", exc_info=True)
        return None