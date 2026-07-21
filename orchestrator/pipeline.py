import asyncio
import datetime
import logging
import os
import sys
import webbrowser

from pypdf import PdfReader

import ingestion
from .filters import (
    filter_excluded_employers,
    is_job_match,
    load_excluded_keywords,
    load_excluded_publishers,
    parse_pub_date,
)
from .agents import (
    evaluate_and_validate_single_job,
    filter_job_via_skill,
    UnsafeLocalCodeExecutor,
)
from .dashboard import generate_dashboard

logger = logging.getLogger(__name__)

_WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def extract_resume_text(pdf_path: str) -> str:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Resume file not found at: {pdf_path}")
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()


async def run_matching_pipeline(
    resume_text, jobs, model_name, max_eval, min_salary, concurrency, desc_limit
):
    code_executor = UnsafeLocalCodeExecutor()
    semaphore = asyncio.Semaphore(concurrency)

    total_jobs = len(jobs)
    logger.info("Running employer exclusion check on all %s matching jobs natively...", total_jobs)

    file_name = "excluded_employers_test.txt" if os.environ.get("BEHAVE_TEST") == "true" else "excluded_employers.txt"
    employers_file = os.path.abspath(os.path.join(_WORKSPACE_ROOT, file_name))
    kept_jobs = filter_excluded_employers(jobs, employers_file)

    logger.info("Employer filter completed. %s out of %s jobs kept.", len(kept_jobs), total_jobs)

    if not kept_jobs:
        return []

    filter_tasks = []
    total_kept = len(kept_jobs)
    logger.info("Running salary filter on all %s matching jobs (threshold: $%s, concurrency: %s) using ADK 'applying-compensation-filter' skill...", total_kept, f"{min_salary:,}", concurrency)

    for i, job in enumerate(kept_jobs):
        task = asyncio.create_task(
            filter_job_via_skill(job, i + 1, total_kept, model_name, semaphore, min_salary, desc_limit)
        )
        filter_tasks.append(task)

    filter_results = await asyncio.gather(*filter_tasks)
    passed_jobs = [job for job, passed in filter_results if passed]

    logger.info("Salary filter completed. %s out of %s jobs passed the $%s+ salary requirement.", len(passed_jobs), total_kept, f"{min_salary:,}")

    if not passed_jobs:
        return []

    score_tasks = []
    total_eval = min(len(passed_jobs), max_eval)
    logger.info("Starting evaluations for the first %s qualified jobs (max limit is %s) using ADK skills...", total_eval, max_eval)

    for i, job in enumerate(passed_jobs[:total_eval]):
        task = asyncio.create_task(
            evaluate_and_validate_single_job(resume_text, job, i + 1, total_eval, model_name, semaphore, desc_limit)
        )
        score_tasks.append(task)

    rated_jobs = await asyncio.gather(*score_tasks)
    return rated_jobs


async def run_pipeline(
    resume_path,
    job_titles_str,
    model_name,
    max_eval,
    min_salary=150000,
    concurrency=3,
    desc_limit=10000,
    max_age=5
):
    logger.info("Parsing resume natively...")
    try:
        resume_text = extract_resume_text(resume_path)
        if not resume_text:
            raise ValueError("Parsed resume text is empty.")
        logger.info("Resume successfully parsed.")
    except Exception as e:
        logger.error("Critical Error parsing resume: %s", e)
        sys.exit(1)

    logger.info("Starting concurrent data ingestion from job feeds...")

    pub_file_name = "excluded_publishers_test.txt" if os.environ.get("BEHAVE_TEST") == "true" else "excluded_publishers.txt"
    publishers_file = os.path.abspath(os.path.join(_WORKSPACE_ROOT, pub_file_name))
    excluded_publishers = load_excluded_publishers(publishers_file)

    wwr_task = asyncio.create_task(asyncio.to_thread(ingestion.fetch_weworkremotely_jobs))
    remotive_task = asyncio.create_task(asyncio.to_thread(ingestion.fetch_remotive_jobs))
    arbeitnow_task = asyncio.create_task(asyncio.to_thread(ingestion.fetch_arbeitnow_jobs))
    themuse_task = asyncio.create_task(asyncio.to_thread(ingestion.fetch_themuse_jobs))
    jsearch_task = asyncio.create_task(asyncio.to_thread(
        ingestion.fetch_jsearch_jobs,
        job_titles_str,
        excluded_publishers
    ))
    himalayas_task = asyncio.create_task(asyncio.to_thread(ingestion.fetch_himalayas_jobs))
    remoteok_task = asyncio.create_task(asyncio.to_thread(ingestion.fetch_remoteok_jobs))

    wwr_jobs, remotive_jobs, arbeitnow_jobs, themuse_jobs, jsearch_jobs, himalayas_jobs, remoteok_jobs = await asyncio.gather(
        wwr_task, remotive_task, arbeitnow_task, themuse_task, jsearch_task, himalayas_task, remoteok_task
    )
    all_jobs = wwr_jobs + remotive_jobs + arbeitnow_jobs + themuse_jobs + jsearch_jobs + himalayas_jobs + remoteok_jobs

    if max_age > 0:
        current_time = datetime.datetime.utcnow()
        filtered_by_age = []
        skipped_by_age_count = 0
        for job in all_jobs:
            pub_date_str = job.get("publication_date")
            if not pub_date_str:
                filtered_by_age.append(job)
                continue
            pub_dt = parse_pub_date(pub_date_str)
            if pub_dt:
                age = current_time - pub_dt
                if age > datetime.timedelta(days=max_age):
                    skipped_by_age_count += 1
                    continue
            filtered_by_age.append(job)
        all_jobs = filtered_by_age
        if skipped_by_age_count > 0:
            logger.info("Age filter: Filtered out %s jobs older than %s days.", skipped_by_age_count, max_age)

    if not all_jobs:
        logger.error("No jobs fetched from any job boards (or all fetched jobs were older than the age limit). Exiting.")
        sys.exit(1)

    file_name = "excluded_keywords_test.txt" if os.environ.get("BEHAVE_TEST") == "true" else "excluded_keywords.txt"
    keywords_file = os.path.abspath(os.path.join(_WORKSPACE_ROOT, file_name))
    excluded_keywords = load_excluded_keywords(keywords_file)

    query_titles = [t.strip() for t in job_titles_str.split(",") if t.strip()]
    logger.info("Filtering jobs matching titles: %s", query_titles)
    matching_jobs = [job for job in all_jobs if is_job_match(job, query_titles)]

    filtered_jobs = []
    for job in matching_jobs:
        title_lower = job.get("title", "").lower()
        desc_lower = job.get("description", "").lower()
        excluded_by_keyword = False
        matching_keyword = ""
        for kw in excluded_keywords:
            if kw in title_lower or kw in desc_lower:
                excluded_by_keyword = True
                matching_keyword = kw
                break
        if excluded_by_keyword:
            logger.info("Keyword filter: EXCLUDED %s (%s) - matches excluded keyword '%s'", job.get('title', 'Unknown'), job.get('company_name', 'Unknown'), matching_keyword)
        else:
            filtered_jobs.append(job)

    skipped = len(matching_jobs) - len(filtered_jobs)
    logger.info("Found %s matching jobs out of %s total listings (skipped %s via keyword exclusion).", len(filtered_jobs), len(all_jobs), skipped)

    if not filtered_jobs:
        logger.info("No matching jobs found in feeds for the specified titles.")
        output_path = generate_dashboard(
            rated_jobs=[],
            resume_path=resume_path,
            searched_keywords=job_titles_str,
            total_found=0,
            total_evaluated=0
        )
        logger.info("Generated empty dashboard: %s", output_path)
        webbrowser.open(f"file:///{output_path}")
        return

    try:
        rated_jobs = await run_matching_pipeline(
            resume_text=resume_text,
            jobs=filtered_jobs,
            model_name=model_name,
            max_eval=max_eval,
            min_salary=min_salary,
            concurrency=concurrency,
            desc_limit=desc_limit
        )
    except Exception as e:
        logger.error("Critical Error in rating pipeline: %s", e)
        sys.exit(1)

    output_path = generate_dashboard(
        rated_jobs=rated_jobs,
        resume_path=resume_path,
        searched_keywords=job_titles_str,
        total_found=len(filtered_jobs),
        total_evaluated=min(len(filtered_jobs), max_eval)
    )

    logger.info("=" * 60)
    logger.info("Dashboard successfully generated!")
    logger.info("Filename: %s", output_path)
    logger.info("=" * 60)

    webbrowser.open(f"file:///{output_path}")
