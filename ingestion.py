import datetime
import json
import logging
import xml.etree.ElementTree as ET
import requests

import os
import time
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def fetch_weworkremotely_jobs() -> list[dict]:
    """Fetches jobs from We Work Remotely RSS feed."""
    url = "https://weworkremotely.com/remote-jobs.rss"
    logger.info("Fetching jobs from We Work Remotely...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ATSJobMatcher/1.0"}
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        
        root = ET.fromstring(r.content)
        jobs = []
        for item in root.findall(".//item"):
            title_text = item.find("title").text or ""
            company = "Unknown"
            title = title_text
            
            # WWR RSS titles are formatted as "Company Name: Job Title"
            if ":" in title_text:
                parts = title_text.split(":", 1)
                company = parts[0].strip()
                title = parts[1].strip()
                
            description = item.find("description").text or ""
            link = item.find("link").text or ""
            pub_date = item.find("pubDate").text or ""
            category = item.find("category").text or ""
            
            jobs.append({
                "source": "We Work Remotely",
                "title": title,
                "company_name": company,
                "description": description,
                "url": link,
                "publication_date": pub_date,
                "category": category
            })
        
        logger.info("Retrieved %s jobs from We Work Remotely.", len(jobs))
        return jobs
    except Exception as e:
        logger.warning("Failed to fetch We Work Remotely jobs: %s", e)
        return []

def fetch_remotive_jobs() -> list[dict]:
    """Fetches jobs from Remotive API."""
    url = "https://remotive.com/api/remote-jobs"
    logger.info("Fetching jobs from Remotive API...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ATSJobMatcher/1.0"}
    
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        
        data = r.json()
        raw_jobs = data.get("jobs", [])
        jobs = []
        for job in raw_jobs:
            jobs.append({
                "source": "Remotive",
                "title": job.get("title", ""),
                "company_name": job.get("company_name", ""),
                "description": job.get("description", ""),
                "url": job.get("url", ""),
                "publication_date": job.get("publication_date", ""),
                "category": job.get("category", "")
            })
            
        logger.info("Retrieved %s jobs from Remotive API.", len(jobs))
        return jobs
    except Exception as e:
        logger.warning("Failed to fetch Remotive jobs: %s", e)
        return []

def fetch_arbeitnow_jobs() -> list[dict]:
    """Fetches remote jobs from Arbeitnow API."""
    url = "https://www.arbeitnow.com/api/job-board-api"
    logger.info("Fetching jobs from Arbeitnow API...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ATSJobMatcher/1.0"}
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        
        data = r.json()
        raw_jobs = data.get("data", [])
        jobs = []
        for job in raw_jobs:
            if not job.get("remote"):
                continue
            
            pub_date = ""
            created_at = job.get("created_at")
            if created_at:
                try:
                    pub_date = datetime.datetime.fromtimestamp(created_at).strftime("%a, %d %b %Y %H:%M:%S GMT")
                except Exception:
                    pub_date = str(created_at)
            
            jobs.append({
                "source": "Arbeitnow",
                "title": job.get("title", ""),
                "company_name": job.get("company_name", ""),
                "description": job.get("description", ""),
                "url": job.get("url", ""),
                "publication_date": pub_date,
                "category": ", ".join(job.get("tags", [])) if job.get("tags") else "Remote Job"
            })
            
        logger.info("Retrieved %s remote jobs from Arbeitnow API.", len(jobs))
        return jobs
    except Exception as e:
        logger.warning("Failed to fetch Arbeitnow jobs: %s", e)
        return []

def fetch_themuse_jobs() -> list[dict]:
    """Fetches jobs from The Muse API."""
    url = "https://www.themuse.com/api/public/jobs?location=Remote&page=1"
    logger.info("Fetching jobs from The Muse API...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ATSJobMatcher/1.0"}
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        
        data = r.json()
        raw_jobs = data.get("results", [])
        jobs = []
        for job in raw_jobs:
            company = job.get("company", {})
            company_name = company.get("name", "Unknown") if isinstance(company, dict) else "Unknown"
            
            refs = job.get("refs", {})
            url_link = refs.get("landing_page", "") if isinstance(refs, dict) else ""
            
            categories = job.get("categories", [])
            cat_list = []
            if isinstance(categories, list):
                for cat in categories:
                    if isinstance(cat, dict) and cat.get("name"):
                        cat_list.append(cat.get("name"))
            category_str = ", ".join(cat_list) if cat_list else "Remote Job"
            
            jobs.append({
                "source": "The Muse",
                "title": job.get("name", ""),
                "company_name": company_name,
                "description": job.get("contents", ""),
                "url": url_link,
                "publication_date": job.get("publication_date", ""),
                "category": category_str
            })
            
        logger.info("Retrieved %s jobs from The Muse API.", len(jobs))
        return jobs
    except Exception as e:
        logger.warning("Failed to fetch The Muse jobs: %s", e)
        return []

def fetch_jsearch_jobs(job_titles_str: str, exclude_publishers: list[str] = None) -> list[dict]:
    """Fetches jobs from JSearch API natively in Python."""
    logger.info("Fetching jobs from JSearch API...")
    load_dotenv()
    
    api_key = os.getenv("X-RapidAPI-Key") or os.getenv("X_RAPIDAPI_KEY")
    api_host = os.getenv("X-RapidAPI-Host") or os.getenv("X_RAPIDAPI_HOST") or "jsearch.p.rapidapi.com"
    
    if not api_key or "dummy" in api_key.lower():
        logger.warning("No valid X-RapidAPI-Key found in environment or .env file.")
        return []

    # Use the first job title search query as the query for JSearch
    first_title = job_titles_str.split(",")[0].strip() if job_titles_str else "Python Developer"
    query = f"{first_title} in Remote"

    url = f"https://{api_host}/search-v2"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": api_host
    }

    try:
        raw_jobs = []
        current_cursor = None
        
        # Fetch 1 page
        num_pages = 1
        for p in range(num_pages):
            params = {}
            if current_cursor:
                params["cursor"] = current_cursor
            else:
                params["query"] = query
                if exclude_publishers:
                    params["exclude_job_publisher"] = ",".join(exclude_publishers)
                
            MAX_RETRIES = 3
            TIMEOUT = 30
            r = None
            for attempt in range(MAX_RETRIES):
                try:
                    r = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
                    r.raise_for_status()
                    break
                except (requests.exceptions.RequestException, requests.exceptions.Timeout) as req_err:
                    if attempt == MAX_RETRIES - 1:
                        raise req_err
                    logger.warning("JSearch API request attempt %s failed: %s. Retrying in %ss...", attempt + 1, req_err, 2 ** attempt)
                    time.sleep(2 ** attempt)
            
            response_json = r.json()
            if response_json.get("status") == "ERROR":
                error_info = response_json.get("error", {})
                error_msg = error_info.get("message") or "Unknown JSearch API error"
                logger.warning("JSearch API returned error status: %s", error_msg)
                break
                
            data_obj = response_json.get("data")
            if isinstance(data_obj, dict):
                page_jobs = data_obj.get("jobs", [])
                current_cursor = data_obj.get("cursor")
            elif isinstance(data_obj, list):
                page_jobs = data_obj
                current_cursor = None
            else:
                page_jobs = []
                current_cursor = None
                
            if not page_jobs:
                break
                
            raw_jobs.extend(page_jobs)
            if not current_cursor:
                break

        normalized_jobs = []
        for job in raw_jobs:
            publisher = job.get("job_publisher") or ""
            if exclude_publishers:
                if any(expub.strip().lower() in publisher.lower() for expub in exclude_publishers if expub.strip()):
                    continue

            title = job.get("job_title") or "JSearch Job"
            company = job.get("employer_name") or "Unknown"
            desc = job.get("job_description") or ""
            link = job.get("job_apply_link") or job.get("job_google_link") or ""
            
            pub_date = job.get("job_posted_at_datetime_utc") or ""
            if not pub_date and job.get("job_posted_at_timestamp"):
                try:
                    pub_date = datetime.datetime.fromtimestamp(job["job_posted_at_timestamp"]).strftime("%a, %d %b %Y %H:%M:%S GMT")
                except Exception:
                    pub_date = str(job["job_posted_at_timestamp"])
            
            category = job.get("job_employment_type") or "Remote Job"
            
            normalized_jobs.append({
                "source": f"JSearch ({publisher})" if publisher else "JSearch (via RapidAPI)",
                "title": title,
                "company_name": company,
                "description": desc,
                "url": link,
                "publication_date": pub_date,
                "category": category
            })
            
        logger.info("Retrieved %s jobs from JSearch API.", len(normalized_jobs))
        return normalized_jobs
    except Exception as e:
        logger.warning("Failed to fetch JSearch jobs: %s", e)
        return []

def fetch_himalayas_jobs() -> list[dict]:
    """Fetches remote jobs from Himalayas API."""
    url = "https://himalayas.app/jobs/api"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        raw_jobs = data.get("jobs", [])
        jobs = []
        for job in raw_jobs:
            title = job.get("title", "")
            company = job.get("companyName", "")
            desc = job.get("description", "")
            link = job.get("applicationLink", "")
            
            # Parse timestamp to RFC 822 format
            pub_date = ""
            ts = job.get("pubDate")
            if ts:
                try:
                    pub_date = datetime.datetime.fromtimestamp(ts).strftime("%a, %d %b %Y %H:%M:%S GMT")
                except Exception:
                    pub_date = str(ts)
                    
            category = job.get("employmentType") or "Remote Job"
            
            jobs.append({
                "source": "Himalayas",
                "title": title,
                "company_name": company,
                "description": desc,
                "url": link,
                "publication_date": pub_date,
                "category": category
            })
        logger.info("Retrieved %s jobs from Himalayas API.", len(jobs))
        return jobs
    except Exception as e:
        logger.warning("Failed to fetch Himalayas jobs: %s", e)
        return []

def fetch_remoteok_jobs() -> list[dict]:
    """Fetches remote jobs from Remote OK API."""
    url = "https://remoteok.com/api"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        raw_data = response.json()
        
        # Remote OK returns a list where the first item is a metadata dictionary (has "legal" key)
        if not isinstance(raw_data, list) or len(raw_data) <= 1:
            logger.warning("Remote OK API returned empty or invalid data.")
            return []
            
        jobs = []
        # Skip the first element as it is metadata
        for job in raw_data[1:]:
            title = job.get("position", "")
            company = job.get("company", "")
            desc = job.get("description", "")
            link = job.get("apply_url") or job.get("url", "")
            pub_date = job.get("date", "")
            category = ", ".join(job.get("tags", [])) if job.get("tags") else "Remote Job"
            
            jobs.append({
                "source": "Remote OK",
                "title": title,
                "company_name": company,
                "description": desc,
                "url": link,
                "publication_date": pub_date,
                "category": category
            })
            
        logger.info("Retrieved %s jobs from Remote OK API.", len(jobs))
        return jobs
    except Exception as e:
        logger.warning("Failed to fetch Remote OK jobs: %s", e)
        return []
