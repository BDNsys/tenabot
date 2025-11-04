# tenabot/analytics/pdf_generation_service.py
import os, time
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.units import inch

def generate_harvard_pdf(resume_data, telegram_id):
    output_dir = os.path.join(settings.MEDIA_ROOT, "generated_resumes")
    os.makedirs(output_dir, exist_ok=True)

    filename_base = f"resume_{telegram_id}_{int(time.time())}.pdf"
    pdf_path = os.path.join(output_dir, filename_base)

    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    title = resume_data.get("position_inferred", "Professional Resume")
    story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph(f"<b>Phone:</b> {resume_data.get('phone', 'N/A')}", styles["Normal"]))
    story.append(Paragraph(f"<b>Email:</b> {resume_data.get('email', 'N/A')}", styles["Normal"]))
    story.append(Paragraph(f"<b>LinkedIn:</b> {resume_data.get('linkedin', 'N/A')}", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>Core Values</b>", styles["Heading2"]))
    values = resume_data.get("core_values", [])
    story.append(ListFlowable([ListItem(Paragraph(v, styles["Normal"])) for v in values]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>Skills</b>", styles["Heading2"]))
    skills = resume_data.get("skills", [])
    story.append(ListFlowable([ListItem(Paragraph(s, styles["Normal"])) for s in skills]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>Work Experience</b>", styles["Heading2"]))
    for job in resume_data.get("work_history", []):
        story.append(Paragraph(f"<b>{job.get('title','')}</b> — {job.get('company','')}", styles["Normal"]))
        story.append(Paragraph(f"{job.get('start_date','')} - {job.get('end_date','')}", styles["Italic"]))
        story.append(Paragraph(job.get("summary",""), styles["Normal"]))
        story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("<b>Education</b>", styles["Heading2"]))
    for edu in resume_data.get("full_education", []):
        story.append(Paragraph(
            f"{edu.get('degree','')} in {edu.get('field_of_study','')} "
            f"from {edu.get('institution','')} ({edu.get('graduation_date','')})",
            styles["Normal"]
        ))

    doc.build(story)
    return pdf_path
