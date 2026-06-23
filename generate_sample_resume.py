import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_resume_pdf(output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            rightMargin=54, leftMargin=54,
                            topMargin=54, bottomMargin=54)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'ResumeTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'ResumeSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=14,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=15
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'ResumeBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=6
    )
    
    bullet_style = ParagraphStyle(
        'ResumeBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1f2937"),
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    story = []
    
    # Header
    story.append(Paragraph("Alex Dev", title_style))
    story.append(Paragraph("Python Software Engineer | Denver, CO (Remote) | alex.dev@email.com | (555) 019-2834", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Summary
    story.append(Paragraph("Professional Summary", section_heading))
    story.append(Paragraph(
        "Highly motivated and skilled Software Engineer with over 5 years of experience specializing in Python development. "
        "Proven track record of designing, building, and deploying scalable web applications, robust RESTful APIs, and efficient "
        "data engineering pipelines. Strong experience with Django, FastAPI, PostgreSQL, Docker, and AWS cloud environments. "
        "Passionate about writing clean, maintainable code and solving complex technical challenges.",
        body_style
    ))
    
    # Skills
    story.append(Paragraph("Technical Skills", section_heading))
    story.append(Paragraph("<b>Languages:</b> Python, SQL, JavaScript, HTML5, CSS3", body_style))
    story.append(Paragraph("<b>Frameworks & Libraries:</b> Django, Django REST Framework, FastAPI, Flask, Pandas, NumPy", body_style))
    story.append(Paragraph("<b>Databases:</b> PostgreSQL, MySQL, SQLite, Redis", body_style))
    story.append(Paragraph("<b>DevOps & Tools:</b> Docker, AWS (S3, EC2, ECS, Lambda), Git, GitHub Actions, Linux", body_style))
    
    # Experience
    story.append(Paragraph("Professional Experience", section_heading))
    
    story.append(Paragraph("<b>Senior Python Engineer</b> | TechCorp Solutions (Remote) | 2023 - Present", body_style))
    story.append(Paragraph("&bull; Architected and implemented 15+ microservices using Python, FastAPI, and PostgreSQL, improving service reliability by 25%.", bullet_style))
    story.append(Paragraph("&bull; Optimized complex database queries and added Redis caching layer, reducing overall API response latency by 35%.", bullet_style))
    story.append(Paragraph("&bull; Containerized development and production environments using Docker, streamlining deployments to AWS ECS.", bullet_style))
    story.append(Paragraph("&bull; Mentored junior developers and instituted code review standards to ensure code quality and maintainability.", bullet_style))
    
    story.append(Paragraph("<b>Software Engineer</b> | StartupInc (Denver, CO) | 2021 - 2023", body_style))
    story.append(Paragraph("&bull; Developed and maintained key features for a high-traffic Django SaaS web application.", bullet_style))
    story.append(Paragraph("&bull; Designed and integrated secure third-party REST APIs for payment processing and analytics.", bullet_style))
    story.append(Paragraph("&bull; Set up automated CI/CD workflows using GitHub Actions, cutting manual deployment errors by 50%.", bullet_style))
    story.append(Paragraph("&bull; Managed database migrations and schema design for PostgreSQL databases.", bullet_style))
    
    # Education
    story.append(Paragraph("Education", section_heading))
    story.append(Paragraph("<b>Bachelor of Science in Computer Science</b> | University of Colorado | 2017 - 2021", body_style))
    
    # Build Document
    doc.build(story)
    print(f"Successfully generated sample resume PDF at: {output_path}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_pdf = os.path.join(current_dir, "sample_resume.pdf")
    create_resume_pdf(output_pdf)
