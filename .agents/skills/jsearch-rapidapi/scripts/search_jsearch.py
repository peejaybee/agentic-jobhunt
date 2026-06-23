import argparse
import os
import sys
import json
import datetime
import requests
from dotenv import load_dotenv

def main():
    parser = argparse.ArgumentParser(description="Search jobs via JSearch RapidAPI wrapper")
    parser.add_argument("--query", default="Python Developer in Remote", help="Search query string")
    parser.add_argument("--page", type=int, default=1, help="Page number")
    parser.add_argument("--num_pages", type=int, default=1, help="Number of pages to fetch")
    args = parser.parse_args()

    # Determine script and workspace root to load the .env file robustly
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.abspath(os.path.join(script_dir, "../../../.."))
    env_path = os.path.join(workspace_root, ".env")

    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()

    api_key = os.getenv("X-RapidAPI-Key") or os.getenv("X_RAPIDAPI_KEY")
    api_host = os.getenv("X-RapidAPI-Host") or os.getenv("X_RAPIDAPI_HOST") or "jsearch.p.rapidapi.com"

    if not api_key or "dummy" in api_key.lower():
        sys.stderr.write("Warning: No valid X-RapidAPI-Key found in environment or .env file.\n")
        # Return empty list to keep script execution safe
        print(json.dumps([]))
        return

    # Call JSearch Search endpoint
    url = f"https://{api_host}/search"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": api_host
    }
    params = {
        "query": args.query,
        "page": str(args.page),
        "num_pages": str(args.num_pages)
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        
        response_json = r.json()
        if response_json.get("status") == "ERROR":
            error_info = response_json.get("error", {})
            error_msg = error_info.get("message") or "Unknown JSearch API error"
            sys.stderr.write(f"JSearch API returned error status: {error_msg}\n")
            print(json.dumps([]))
            return
            
        raw_jobs = response_json.get("data", [])
        normalized_jobs = []
        for job in raw_jobs:
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
                "source": "JSearch (via RapidAPI)",
                "title": title,
                "company_name": company,
                "description": desc,
                "url": link,
                "publication_date": pub_date,
                "category": category
            })
            
        print(json.dumps(normalized_jobs))
    except Exception as e:
        sys.stderr.write(f"Error querying JSearch API: {e}\n")
        print(json.dumps([]))

if __name__ == "__main__":
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
