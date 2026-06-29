import datetime
import json
import xml.etree.ElementTree as ET
import requests

from google.adk.tools.skill_toolset import SkillToolset, RunSkillScriptTool
from google.adk.code_executors.unsafe_local_code_executor import UnsafeLocalCodeExecutor

def fetch_weworkremotely_jobs() -> list[dict]:
    """Fetches jobs from We Work Remotely RSS feed."""
    url = "https://weworkremotely.com/remote-jobs.rss"
    print("Fetching jobs from We Work Remotely...")
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
        
        print(f"Retrieved {len(jobs)} jobs from We Work Remotely.")
        return jobs
    except Exception as e:
        print(f"Warning: Failed to fetch We Work Remotely jobs: {e}")
        return []

def fetch_remotive_jobs() -> list[dict]:
    """Fetches jobs from Remotive API."""
    url = "https://remotive.com/api/remote-jobs"
    print("Fetching jobs from Remotive API...")
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
            
        print(f"Retrieved {len(jobs)} jobs from Remotive API.")
        return jobs
    except Exception as e:
        print(f"Warning: Failed to fetch Remotive jobs: {e}")
        return []

def fetch_arbeitnow_jobs() -> list[dict]:
    """Fetches remote jobs from Arbeitnow API."""
    url = "https://www.arbeitnow.com/api/job-board-api"
    print("Fetching jobs from Arbeitnow API...")
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
            
        print(f"Retrieved {len(jobs)} remote jobs from Arbeitnow API.")
        return jobs
    except Exception as e:
        print(f"Warning: Failed to fetch Arbeitnow jobs: {e}")
        return []

def fetch_themuse_jobs() -> list[dict]:
    """Fetches jobs from The Muse API."""
    url = "https://www.themuse.com/api/public/jobs?location=Remote&page=1"
    print("Fetching jobs from The Muse API...")
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
            
        print(f"Retrieved {len(jobs)} jobs from The Muse API.")
        return jobs
    except Exception as e:
        print(f"Warning: Failed to fetch The Muse jobs: {e}")
        return []

async def fetch_jsearch_jobs_via_skill(job_titles_str: str, skill_registry, tool_context, exclude_publishers: list[str] = None) -> list[dict]:
    """Fetches jobs from JSearch API using the jsearch-rapidapi custom ADK skill."""
    print("Fetching jobs from JSearch API via ADK skill...")
    try:
        code_executor = UnsafeLocalCodeExecutor()
        toolset = SkillToolset(registry=skill_registry, code_executor=code_executor)
        run_skill_script_tool = RunSkillScriptTool(toolset)
        
        # Use the first job title search query as the query for JSearch
        first_title = job_titles_str.split(",")[0].strip() if job_titles_str else "Python Developer"
        query = f"{first_title} in Remote"
        
        args_list = ["--query", query]
        if exclude_publishers:
            args_list.extend(["--exclude_publishers"] + exclude_publishers)
            
        res = await run_skill_script_tool.run_async(
            args={
                "skill_name": "jsearch-rapidapi",
                "file_path": "scripts/search_jsearch.py",
                "args": args_list
            },
            tool_context=tool_context
        )
        
        if res.get("status") != "success" or res.get("error"):
            error_msg = res.get("error") or res.get("stderr") or "Unknown error"
            print(f"Warning: JSearch skill execution failed: {error_msg}")
            return []
            
        stderr = res.get("stderr", "").strip()
        if stderr:
            print(f"[JSearch Skill Output] {stderr}")
            
        stdout = res.get("stdout", "").strip()
        if not stdout:
            return []
            
        try:
            jobs = json.loads(stdout)
            print(f"Retrieved {len(jobs)} jobs from JSearch API.")
            return jobs
        except Exception as e:
            print(f"Warning: Failed to parse JSearch output JSON: {e}")
            return []
    except Exception as e:
        print(f"Warning: Failed to run JSearch skill: {e}")
        return []
