import asyncio
import datetime
import html
from html.parser import HTMLParser
import json
import os
import re
import sys
import webbrowser
import xml.etree.ElementTree as ET
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class SafeHTMLSanitizer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.allowed_tags = {
            'p', 'br', 'strong', 'em', 'u', 'b', 'i', 'span', 'div',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li',
            'blockquote', 'code', 'pre', 'hr', 'a', 'table', 'thead',
            'tbody', 'tr', 'th', 'td'
        }
        self.allowed_attrs = {
            'a': {'href', 'target', 'title', 'rel'},
            'span': {'class', 'style'},
            'div': {'class', 'style'},
            'p': {'class', 'style'}
        }
        self.skip_content_tags = {'script', 'style', 'iframe', 'object', 'embed', 'form'}
        self.skip_level = 0
        self.result = []
        self.tag_stack = []

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower in self.skip_content_tags:
            self.skip_level += 1
            return
            
        if self.skip_level > 0:
            return

        if tag_lower in self.allowed_tags:
            cleaned_attrs = []
            allowed_attr_names = self.allowed_attrs.get(tag_lower, set())
            for name, value in attrs:
                name_lower = name.lower()
                if name_lower in allowed_attr_names:
                    if name_lower == 'href':
                        val_lower = value.strip().lower()
                        if val_lower.startswith(('javascript:', 'data:', 'vbscript:')):
                            continue
                    cleaned_attrs.append(f'{name}="{html.escape(value)}"')
            
            attr_str = f" {' '.join(cleaned_attrs)}" if cleaned_attrs else ""
            self.result.append(f"<{tag_lower}{attr_str}>")
            self.tag_stack.append(tag_lower)

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in self.skip_content_tags:
            if self.skip_level > 0:
                self.skip_level -= 1
            return

        if self.skip_level > 0:
            return

        if tag_lower in self.allowed_tags:
            if self.tag_stack and self.tag_stack[-1] == tag_lower:
                self.tag_stack.pop()
                self.result.append(f"</{tag_lower}>")
            elif tag_lower in self.tag_stack:
                while self.tag_stack:
                    closed_tag = self.tag_stack.pop()
                    self.result.append(f"</{closed_tag}>")
                    if closed_tag == tag_lower:
                        break

    def handle_data(self, data):
        if self.skip_level > 0:
            return
        self.result.append(html.escape(data))

    def handle_entityref(self, name):
        if self.skip_level > 0:
            return
        self.result.append(f"&{name};")

    def handle_charref(self, name):
        if self.skip_level > 0:
            return
        self.result.append(f"&#{name};")

    def get_sanitized_html(self) -> str:
        while self.tag_stack:
            self.result.append(f"</{self.tag_stack.pop()}>")
        return "".join(self.result)

def sanitize_html(html_content: str) -> str:
    if not html_content:
        return ""
    parser = SafeHTMLSanitizer()
    try:
        parser.feed(html_content)
        return parser.get_sanitized_html()
    except Exception:
        return html.escape(html_content)


# Reconfigure stdout and stderr to UTF-8 to prevent Unicode encoding errors on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


# Import ADK modules needed for orchestration
from google.adk.skills import load_skill_from_dir, list_skills_in_dir
from google.adk.skills.skill_registry import SkillRegistry
from google.adk.tools.skill_toolset import SkillToolset, RunSkillScriptTool
from google.adk.code_executors.unsafe_local_code_executor import UnsafeLocalCodeExecutor
from dashboard_template import HTML_TEMPLATE, JOB_CARD_TEMPLATE, NO_MATCHES_TEMPLATE

# Resolve paths to the custom skills
workspace_root = os.path.dirname(os.path.abspath(__file__))

class LocalSkillRegistry(SkillRegistry):
    """Registry to load skills dynamically from the local filesystem on-demand (progressive disclosure)."""
    def __init__(self, skills_dir: str):
        self.skills_dir = os.path.abspath(skills_dir)
        self._skills_metadata = {}
        try:
            self._skills_metadata = list_skills_in_dir(self.skills_dir)
        except Exception:
            pass

    async def get_skill(self, *, name: str):
        skill_path = os.path.join(self.skills_dir, name)
        if not os.path.isdir(skill_path):
            raise FileNotFoundError(f"Skill '{name}' not found at '{skill_path}'")
        return load_skill_from_dir(skill_path)

    async def search_skills(self, *, query: str):
        results = []
        query_lower = query.lower()
        for name, fm in self._skills_metadata.items():
            if query_lower in name.lower() or query_lower in fm.description.lower():
                results.append(fm)
        return results

# Initialize the local registry for progressive disclosure
skills_directory = os.path.join(workspace_root, ".agents", "skills")
skill_registry = LocalSkillRegistry(skills_directory)

# Set up dummy tool context for running ADK tools programmatically
class DummyInvocationContext:
    def __init__(self):
        self.agent = None
        self.session_id = "orchestrator_session"
        self.user_id = "orchestrator_user"
        self.invocation_id = "orchestrator_invocation"

class DummyToolContext:
    @property
    def invocation_id(self):
        return "orchestrator_invocation"
    @property
    def agent_name(self):
        return "orchestrator"
    @property
    def state(self):
        return {}
    @property
    def _invocation_context(self):
        return DummyInvocationContext()

tool_context = DummyToolContext()


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

async def fetch_jsearch_jobs_via_skill(job_titles_str: str) -> list[dict]:
    """Fetches jobs from JSearch API using the jsearch-rapidapi custom ADK skill."""
    print("Fetching jobs from JSearch API via ADK skill...")
    try:
        code_executor = UnsafeLocalCodeExecutor()
        toolset = SkillToolset(registry=skill_registry, code_executor=code_executor)
        run_skill_script_tool = RunSkillScriptTool(toolset)
        
        # Use the first job title search query as the query for JSearch
        first_title = job_titles_str.split(",")[0].strip() if job_titles_str else "Python Developer"
        query = f"{first_title} in Remote"
        
        res = await run_skill_script_tool.run_async(
            args={
                "skill_name": "jsearch-rapidapi",
                "file_path": "scripts/search_jsearch.py",
                "args": ["--query", query]
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

async def check_exclusion_via_skill(
    run_exclude_tool: RunSkillScriptTool,
    job: dict,
    idx: int,
    total: int,
    semaphore: asyncio.Semaphore
) -> tuple[dict, bool]:
    """Checks if a job's employer is excluded using the excluding-employers skill."""
    async with semaphore:
        company_name = job.get("company_name", "")
        try:
            res = await run_exclude_tool.run_async(
                args={
                    "skill_name": "excluding-employers",
                    "file_path": "scripts/exclude_employers.py",
                    "args": [
                        "--company_name", company_name,
                        "--file_path", os.path.abspath(os.path.join(workspace_root, "excluded_employers.txt"))
                    ]
                },
                tool_context=tool_context
            )
            
            if res.get("status") != "success" or res.get("error"):
                error_msg = res.get("error") or res.get("stderr") or "Unknown error"
                print(f"Warning: Exclusion skill failed for {company_name}: {error_msg}")
                return job, False
                
            stdout = res.get("stdout", "").strip()
            
            json_start = stdout.find("{")
            json_end = stdout.rfind("}") + 1
            if json_start != -1 and json_end != 0:
                parsed = json.loads(stdout[json_start:json_end])
                excluded = parsed.get("excluded", False)
                reason = parsed.get("reason", "")
                if excluded:
                    print(f"[{idx}/{total}] Employer filter: EXCLUDED {company_name} - {reason}")
                return job, excluded
            else:
                return job, False
        except Exception as e:
            print(f"[{idx}/{total}] Error running exclusion filter for {company_name}: {e}")
            return job, False



def format_date_badge(pub_date_str: str) -> str:
    """Format publication dates nicely if possible."""
    if not pub_date_str:
        return ""
    clean_date = pub_date_str
    m = re.search(r'\d+\s+[A-Za-z]+\s+\d{4}', pub_date_str)
    if m:
        clean_date = m.group(0)
    else:
        clean_date = html.escape(clean_date)
    return f'<span class="badge date">{clean_date}</span>'

def generate_dashboard(rated_jobs: list[dict], resume_path: str, searched_keywords: str, total_found: int, total_evaluated: int) -> str:
    """Generates the HTML dashboard from the rated jobs list."""
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
    output_filepath = os.path.join(workspace_root, output_filename)
    
    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(output_html)
        
    return output_filepath

async def evaluate_single_job_via_skill(
    run_skill_script_tool: RunSkillScriptTool,
    resume_text: str,
    job: dict,
    idx: int,
    total: int,
    model_name: str,
    semaphore: asyncio.Semaphore
) -> dict:
    """Evaluates a single job using the RunSkillScriptTool of ADK's SkillToolset."""
    async with semaphore:
        print(f"[{idx}/{total}] Evaluating job: {job['title']} at {job['company_name']}...")
        
        try:
            res = await run_skill_script_tool.run_async(
                args={
                    "skill_name": "ats-scoring",
                    "file_path": "scripts/ats_scorer.py",
                    "args": [
                        "--resume_text", resume_text,
                        "--job_title", job["title"],
                        "--job_company", job["company_name"],
                        "--job_desc", job["description"],
                        "--model", model_name
                    ]
                },
                tool_context=tool_context
            )
            
            if res.get("status") != "success" or res.get("error"):
                error_msg = res.get("error") or res.get("stderr") or "Unknown error"
                raise RuntimeError(error_msg)
                
            stdout = res.get("stdout", "")
            
            # Extract JSON block
            json_start = stdout.find("{")
            json_end = stdout.rfind("}") + 1
            if json_start != -1 and json_end != 0:
                parsed = json.loads(stdout[json_start:json_end])
                score = int(parsed.get("match_score", 0))
                explanation = parsed.get("explanation", "No explanation provided.")
            else:
                score = 0
                explanation = f"Failed to find JSON in output: {stdout[:200]}"
                
        except Exception as e:
            print(f"[{idx}/{total}] Error evaluating job {job['title']}: {e}")
            score = 0
            explanation = f"Error during ADK evaluation: {e}"
            
        rated_job = job.copy()
        rated_job["score"] = score
        rated_job["explanation"] = explanation
        return rated_job

async def filter_job_via_skill(
    run_skill_script_tool: RunSkillScriptTool,
    job: dict,
    idx: int,
    total: int,
    model_name: str,
    semaphore: asyncio.Semaphore
) -> tuple[dict, bool]:
    """Filters a job listing using the filtering-bad-jobs skill."""
    async with semaphore:
        print(f"[{idx}/{total}] Checking salary requirements for: {job['title']} at {job['company_name']}...")
        try:
            res = await run_skill_script_tool.run_async(
                args={
                    "skill_name": "filtering-bad-jobs",
                    "file_path": "scripts/filter_jobs.py",
                    "args": [
                        "--job_title", job["title"],
                        "--job_desc", job["description"],
                        "--model", model_name
                    ]
                },
                tool_context=tool_context
            )
            
            if res.get("status") != "success" or res.get("error"):
                error_msg = res.get("error") or res.get("stderr") or "Unknown error"
                raise RuntimeError(error_msg)
                
            stdout = res.get("stdout", "")
            
            # Extract JSON block
            json_start = stdout.find("{")
            json_end = stdout.rfind("}") + 1
            if json_start != -1 and json_end != 0:
                parsed = json.loads(stdout[json_start:json_end])
                passed = parsed.get("passed", False)
                reason = parsed.get("reason", "No reason provided.")
                print(f"[{idx}/{total}] Salary filter result for {job['title']}: {'PASSED' if passed else 'FAILED'} - {reason}")
                return job, passed
            else:
                print(f"[{idx}/{total}] Error parsing filter output for {job['title']}: raw output: {stdout}")
                return job, False
        except Exception as e:
            print(f"[{idx}/{total}] Error filtering job {job['title']}: {e}")
            return job, False

async def run_matching_pipeline(resume_text: str, jobs: list[dict], model_name: str, max_eval: int):
    """Filters matching jobs by salary, then evaluates the passed ones using the ats-scoring skill."""
    code_executor = UnsafeLocalCodeExecutor()
    
    # 0. Employer Exclusion Phase
    exclude_toolset = SkillToolset(registry=skill_registry, code_executor=code_executor)
    run_exclude_tool = RunSkillScriptTool(exclude_toolset)
    
    semaphore = asyncio.Semaphore(3)
    exclude_tasks = []
    total_jobs = len(jobs)
    print(f"Running employer exclusion check on all {total_jobs} matching jobs using ADK 'excluding-employers' skill...")
    
    for i, job in enumerate(jobs):
        task = asyncio.create_task(
            check_exclusion_via_skill(
                run_exclude_tool, job, i + 1, total_jobs, semaphore
            )
        )
        exclude_tasks.append(task)
        
    exclude_results = await asyncio.gather(*exclude_tasks)
    kept_jobs = [job for job, excluded in exclude_results if not excluded]
    
    print(f"Employer filter completed. {len(kept_jobs)} out of {total_jobs} jobs kept.")
    
    if not kept_jobs:
        return []
        
    # 1. Salary Filtering Phase
    filter_toolset = SkillToolset(registry=skill_registry, code_executor=code_executor)
    run_filter_tool = RunSkillScriptTool(filter_toolset)
    
    filter_tasks = []
    total_kept = len(kept_jobs)
    print(f"Running salary filter on all {total_kept} matching jobs using ADK 'filtering-bad-jobs' skill...")
    
    for i, job in enumerate(kept_jobs):
        task = asyncio.create_task(
            filter_job_via_skill(
                run_filter_tool, job, i + 1, total_kept, model_name, semaphore
            )
        )
        filter_tasks.append(task)
        
    filter_results = await asyncio.gather(*filter_tasks)
    passed_jobs = [job for job, passed in filter_results if passed]
    
    print(f"Salary filter completed. {len(passed_jobs)} out of {total_kept} jobs passed the $150k+ salary requirement.")
    
    if not passed_jobs:
        return []
        
    # 2. ATS Scoring Phase
    score_toolset = SkillToolset(registry=skill_registry, code_executor=code_executor)
    run_score_tool = RunSkillScriptTool(score_toolset)
    
    score_tasks = []
    total_eval = min(len(passed_jobs), max_eval)
    print(f"Starting evaluations for the first {total_eval} qualified jobs (max limit is {max_eval}) using ADK skills...")
    
    for i, job in enumerate(passed_jobs[:total_eval]):
        task = asyncio.create_task(
            evaluate_single_job_via_skill(
                run_score_tool, resume_text, job, i + 1, total_eval, model_name, semaphore
            )
        )
        score_tasks.append(task)
        
    rated_jobs = await asyncio.gather(*score_tasks)
    return rated_jobs

async def run_pipeline(resume_path: str, job_titles_str: str, model_name: str, max_eval: int):
    """Orchestrates the entire PDF parsing, Job Crawling, Scoring, and Reporting workflow."""
    # 1. Parse Resume using the pdf-parsing skill via ADK RunSkillScriptTool
    print(f"Parsing resume via ADK 'pdf-parsing' skill...")
    try:
        code_executor = UnsafeLocalCodeExecutor()
        toolset = SkillToolset(registry=skill_registry, code_executor=code_executor)
        run_skill_script_tool = RunSkillScriptTool(toolset)
        
        res = await run_skill_script_tool.run_async(
            args={
                "skill_name": "pdf-parsing",
                "file_path": "scripts/pdf_parser.py",
                "args": ["--pdf", os.path.abspath(resume_path)]
            },
            tool_context=tool_context
        )
        
        if res.get("status") != "success" or res.get("error"):
            error_msg = res.get("error") or res.get("stderr") or "Unknown error"
            raise RuntimeError(error_msg)
            
        resume_text = res.get("stdout", "").strip()
        if not resume_text:
            raise ValueError("Parsed resume text is empty.")
            
        print("Resume successfully parsed using ADK skill.")
    except Exception as e:
        print(f"Critical Error parsing resume: {e}")
        sys.exit(1)
        
    # 2. Fetch Job Boards
    wwr_jobs = fetch_weworkremotely_jobs()
    remotive_jobs = fetch_remotive_jobs()
    arbeitnow_jobs = fetch_arbeitnow_jobs()
    themuse_jobs = fetch_themuse_jobs()
    jsearch_jobs = await fetch_jsearch_jobs_via_skill(job_titles_str)
    all_jobs = wwr_jobs + remotive_jobs + arbeitnow_jobs + themuse_jobs + jsearch_jobs
    
    if not all_jobs:
        print("No jobs fetched from any job boards. Exiting.")
        sys.exit(1)
        
    # 3. Filter Jobs (Skipping local title filtering to evaluate all fetched jobs)
    print(f"Proceeding with all {len(all_jobs)} fetched jobs from feeds.")
    filtered_jobs = all_jobs
        
    # 4. Evaluate matching jobs using the ats_scoring skill
    try:
        rated_jobs = await run_matching_pipeline(
            resume_text=resume_text,
            jobs=filtered_jobs,
            model_name=model_name,
            max_eval=max_eval
        )
    except Exception as e:
        print(f"Critical Error in rating pipeline: {e}")
        sys.exit(1)
        
    # 5. Generate Dashboard & Open Browser
    output_path = generate_dashboard(
        rated_jobs=rated_jobs,
        resume_path=resume_path,
        searched_keywords=job_titles_str,
        total_found=len(filtered_jobs),
        total_evaluated=min(len(filtered_jobs), max_eval)
    )
    
    print("=" * 60)
    print(f"Dashboard successfully generated!")
    print(f"Filename: {output_path}")
    print("=" * 60)
    
    webbrowser.open(f"file:///{output_path}")
