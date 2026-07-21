import datetime
import html
import os
import re

from .sanitizer import sanitize_html
from dashboard_template import HTML_TEMPLATE, JOB_CARD_TEMPLATE, NO_MATCHES_TEMPLATE

_WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def format_date_badge(pub_date_str: str) -> str:
    if not pub_date_str:
        return ""
    clean_date = pub_date_str
    m = re.search(r'\d+\s+[A-Za-z]+\s+\d{4}', pub_date_str)
    if m:
        clean_date = m.group(0)
    else:
        clean_date = html.escape(clean_date)
    return f'<span class="badge date">{clean_date}</span>'


def generate_dashboard(rated_jobs, resume_path, searched_keywords, total_found, total_evaluated):
    sorted_jobs = sorted(rated_jobs, key=lambda x: x["score"], reverse=True)
    top_10 = sorted_jobs[:10]
    avg_score = 0
    if top_10:
        avg_score = round(sum(j["score"] for j in top_10) / len(top_10))
    if avg_score >= 80:
        avg_score_class = "score-high"
    elif avg_score >= 50:
        avg_score_class = "score-med"
    else:
        avg_score_class = "score-low"
    jobs_html_content = ""
    if not top_10:
        jobs_html_content = NO_MATCHES_TEMPLATE
    else:
        for idx, job in enumerate(top_10):
            score = job["score"]
            if score >= 80:
                score_class = "high"
            elif score >= 50:
                score_class = "med"
            else:
                score_class = "low"
            pub_date_badge = format_date_badge(job["publication_date"])
            jobs_html_content += JOB_CARD_TEMPLATE.format(
                index=idx + 1,
                job_title=html.escape(job["title"]),
                company_name=html.escape(job["company_name"]),
                source=html.escape(job["source"]),
                category=html.escape(job["category"] or "Remote Job"),
                pub_date_badge=pub_date_badge,
                score_class=score_class,
                score=score,
                explanation=html.escape(job["explanation"]),
                job_description=sanitize_html(job["description"]),
                job_url=html.escape(job["url"])
            )
    resume_filename = os.path.basename(resume_path)
    output_html = (
        HTML_TEMPLATE.replace("{resume_filename}", html.escape(resume_filename))
        .replace("{searched_keywords}", html.escape(searched_keywords))
        .replace("{total_found}", str(total_found))
        .replace("{total_evaluated}", str(total_evaluated))
        .replace("{avg_score}", str(avg_score))
        .replace("{avg_score_class}", avg_score_class)
        .replace("{jobs_html_content}", jobs_html_content)
    )
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    output_filename = f"job_matches_{today_str}.html"
    output_filepath = os.path.join(_WORKSPACE_ROOT, output_filename)
    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(output_html)
    return output_filepath
