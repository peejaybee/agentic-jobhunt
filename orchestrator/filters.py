import datetime
import logging
import os
import re

logger = logging.getLogger(__name__)


def load_excluded_keywords(file_path: str) -> list[str]:
    keywords = []
    if not os.path.exists(file_path):
        return keywords
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                item = line.strip()
                if not item or item.startswith("#"):
                    continue
                keywords.append(item.lower())
    except Exception as e:
        logger.warning("Error reading excluded keywords: %s", e)
    return keywords


def load_excluded_publishers(file_path: str) -> list[str]:
    publishers = []
    if not os.path.exists(file_path):
        return publishers
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                item = line.strip()
                if not item or item.startswith("#"):
                    continue
                publishers.append(item)
    except Exception as e:
        logger.warning("Error reading excluded publishers: %s", e)
    return publishers


def check_employer_exclusion(company: str, exclusion_rules: list[str]) -> tuple[bool, str]:
    company_lower = company.strip().lower()
    for rule in exclusion_rules:
        rule_lower = rule.lower()
        if rule_lower in company_lower or company_lower in rule_lower:
            return True, f"Company '{company}' is excluded by rule matching '{rule}'."
    return False, "Company is not in the exclusion list."


def filter_excluded_employers(jobs: list[dict], file_path: str) -> list[dict]:
    if not jobs:
        return []
    rules = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    item = line.strip()
                    if not item or item.startswith("#"):
                        continue
                    rules.append(item)
        except Exception as e:
            logger.warning("Error reading exclusion file: %s", e)
    else:
        logger.warning("Exclusion file not found at: %s. Skipping checks.", file_path)
        return jobs
    kept_jobs = []
    for job in jobs:
        company = job.get("company_name", "").strip()
        if not company:
            kept_jobs.append(job)
            continue
        excluded, reason = check_employer_exclusion(company, rules)
        if excluded:
            logger.info("Employer filter: EXCLUDED %s - %s", company, reason)
        else:
            kept_jobs.append(job)
    return kept_jobs


def is_job_match(job: dict, query_titles: list[str]) -> bool:
    job_title_lower = job["title"].lower()
    for title in query_titles:
        title_lower = title.strip().lower()
        if not title_lower:
            continue
        if title_lower in job_title_lower:
            return True
        query_words = [w for w in title_lower.split() if len(w) > 2]
        if query_words and all(word in job_title_lower for word in query_words):
            return True
    return False


def parse_pub_date(pub_date_str: str) -> datetime.datetime | None:
    if not pub_date_str:
        return None
    import email.utils
    date_str = pub_date_str.strip()
    try:
        dt = email.utils.parsedate_to_datetime(date_str)
        if dt.tzinfo is not None:
            dt = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        pass
    iso_str = date_str
    if iso_str.endswith("Z"):
        iso_str = iso_str[:-1] + "+00:00"
    if " " in iso_str and "," not in iso_str:
        iso_str = iso_str.replace(" ", "T")
    try:
        dt = datetime.datetime.fromisoformat(iso_str)
        if dt.tzinfo is not None:
            dt = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        pass
    try:
        m = re.match(r'^(\d{4})-(\d{2})-(\d{2})', date_str)
        if m:
            return datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except Exception:
        pass
    return None
