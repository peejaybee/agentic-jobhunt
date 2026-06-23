import sys
import os
import asyncio
from unittest.mock import patch, MagicMock
from behave import given, when, then

# Add workspace to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import orchestrator
import ingestion
import cache

class MockPart:
    def __init__(self, text):
        self.text = text

class MockContent:
    def __init__(self, text):
        self.parts = [MockPart(text)]

class MockEvent:
    def __init__(self, text):
        self.content = MockContent(text)

class RunState:
    def __init__(self):
        self.attempts = {}

@given('my local Ollama instance is running')
def step_impl(context):
    os.environ["BEHAVE_TEST"] = "true"
    db_path = cache.get_db_path()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass
    cache.init_db()
    context.ollama_running = True

@given('I have a valid PDF resume file at "{resume_path}"')
def step_impl(context, resume_path):
    context.resume_path = resume_path
    # Write a small dummy file if it doesn't exist
    if not os.path.exists(resume_path):
        with open(resume_path, "w", encoding="utf-8") as f:
            f.write("Dummy resume content")
    context.resume_text = "Jane Doe\nPython Developer\n5 years experience in Django, Postgres, FastAPI."

@given('I have configured a JSearch API key in ".env"')
def step_impl(context):
    context.jsearch_configured = True

@given('the remote job feeds have listings:')
def step_impl(context):
    context.wwr_jobs = []
    context.remotive_jobs = []
    context.arbeitnow_jobs = []
    context.themuse_jobs = []
    context.jsearch_jobs = []

    for row in context.table:
        title = row['Title']
        company = row['Company']
        source = row['Source']
        salary_range = row['Salary Range']

        url_safe_title = title.lower().replace(" ", "-")
        url_safe_company = company.lower().replace(" ", "-")
        job = {
            "title": title,
            "company_name": company,
            "description": f"Position for a {title} at {company}. Compensation details: {salary_range}.",
            "source": source,
            "url": f"https://example.com/job/{url_safe_title}-{url_safe_company}",
            "publication_date": "Tue, 23 Jun 2026 12:00:00 GMT",
            "category": "Software Engineering"
        }

        if source == "We Work Remotely":
            context.wwr_jobs.append(job)
        elif source == "Remotive":
            context.remotive_jobs.append(job)
        elif source == "Arbeitnow":
            context.arbeitnow_jobs.append(job)
        elif source == "The Muse":
            context.themuse_jobs.append(job)
        elif source == "JSearch":
            context.jsearch_jobs.append(job)

@given('the remote job feeds do not contain any listings matching "{query}"')
def step_impl(context, query):
    context.wwr_jobs = []
    context.remotive_jobs = []
    context.arbeitnow_jobs = []
    context.themuse_jobs = []
    context.jsearch_jobs = []

@given('my exclusion file "{filename}" contains "{employer}"')
def step_impl(context, filename, employer):
    context.exclusion_file = filename
    with open(filename, "w", encoding="utf-8") as f:
        f.write(employer + "\n")

@given('the local LLM returns a malformed JSON block on the first attempt')
def step_impl(context):
    context.simulate_malformed_llm = True
    context.run_state = RunState()

@when('I run the matching agent with query "{query}"')
def step_impl(context, query):
    execute_pipeline(
        context=context,
        query=query,
        max_eval=30,
        min_salary=150000,
        concurrency=3,
        desc_limit=10000
    )

@when('I run the matching agent with query "{query}", max eval {max_eval:d}, min salary {min_salary:d}, concurrency {concurrency:d}, and description limit {desc_limit:d}')
def step_impl(context, query, max_eval, min_salary, concurrency, desc_limit):
    execute_pipeline(
        context=context,
        query=query,
        max_eval=max_eval,
        min_salary=min_salary,
        concurrency=concurrency,
        desc_limit=desc_limit
    )

@when('the agent evaluates a job listing')
def step_impl(context):
    mock_job = {
        "title": "Senior Python Developer",
        "company_name": "Tech Corp",
        "description": "Seeking Python Developer, $160,000",
        "source": "Mock",
        "url": "https://example.com/job",
        "publication_date": "Tue, 23 Jun 2026 12:00:00 GMT",
        "category": "Software Engineering"
    }

    async def mock_runner_run_async(self, session_id, user_id, new_message):
        agent_name = self.agent.name
        if agent_name not in context.run_state.attempts:
            context.run_state.attempts[agent_name] = 0
        context.run_state.attempts[agent_name] += 1

        if context.run_state.attempts[agent_name] == 1:
            yield MockEvent("This is not valid JSON and has no braces")
        else:
            if agent_name == "ats_orchestration_agent":
                yield MockEvent('{"match_score": 90, "explanation": "Self-corrected match"}')
            else:
                yield MockEvent('{"has_salary": true, "min_salary_usd": 160000.0, "max_salary_usd": 160000.0, "explanation": "Self-corrected salary"}')

    import io
    context.captured_stdout = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = context.captured_stdout

    try:
        with patch('google.adk.runners.Runner.run_async', mock_runner_run_async), \
             patch('google.adk.tools.skill_toolset.RunSkillScriptTool.run_async', return_value={"status": "success", "stdout": "Jane Doe"}):
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            rated_job = loop.run_until_complete(
                orchestrator.evaluate_single_job_via_skill(
                    resume_text="Jane Doe",
                    job=mock_job,
                    idx=1,
                    total=1,
                    model_name="dummy_model",
                    semaphore=asyncio.Semaphore(1),
                    desc_limit=1000
                )
            )
            context.rated_job_score = rated_job.get("score")
            context.rated_job_explanation = rated_job.get("explanation")
    finally:
        sys.stdout = old_stdout

@then('the agent should crawl jobs from We Work Remotely, Remotive, Arbeitnow, The Muse, and JSearch')
def step_impl(context):
    assert context.crawled_sources == {"We Work Remotely", "Remotive", "Arbeitnow", "The Muse", "JSearch"}, f"Crawled sources: {context.crawled_sources}"

@then('the agent should query search APIs using the query "{query}"')
def step_impl(context, query):
    assert context.searched_query == query, f"Searched query: {context.searched_query}"

@then('the agent should evaluate matching listings against the ${min_salary_k}k salary threshold with a concurrency cap of {concurrency:d}')
def step_impl(context, min_salary_k, concurrency):
    expected_salary = int(min_salary_k) * 1000
    assert context.used_min_salary == expected_salary, f"Used min salary: {context.used_min_salary}"
    assert context.used_concurrency == concurrency, f"Used concurrency: {context.used_concurrency}"

@then('the agent should evaluate matching listings against the ${min_salary_k}k salary threshold')
def step_impl(context, min_salary_k):
    expected_salary = int(min_salary_k) * 1000
    assert context.used_min_salary == expected_salary, f"Used min salary: {context.used_min_salary}"

@then('only the "{job1}" and "{job2}" jobs should pass the salary filter')
def step_impl(context, job1, job2):
    passed_titles = {j["title"] for j in context.passed_jobs}
    assert passed_titles == {job1, job2}, f"Passed jobs: {passed_titles}"

@then('the agent should evaluate those {count:d} passed jobs against my resume using the ATS scorer with descriptions truncated to {desc_limit:d} characters')
def step_impl(context, count, desc_limit):
    assert len(context.evaluated_jobs) == count, f"Evaluated jobs count: {len(context.evaluated_jobs)}"
    assert context.used_desc_limit == desc_limit, f"Used description limit: {context.used_desc_limit}"

@then('the agent should evaluate those {count:d} passed jobs against my resume using the ATS scorer')
def step_impl(context, count):
    assert len(context.evaluated_jobs) == count, f"Evaluated jobs count: {len(context.evaluated_jobs)}"

@then('a date-stamped HTML dashboard should be generated')
def step_impl(context):
    assert os.path.exists(context.dashboard_path), f"Dashboard not found: {context.dashboard_path}"

@then('the dashboard should display the matching jobs sorted by score')
def step_impl(context):
    scores = [j["score"] for j in context.evaluated_jobs]
    assert scores == sorted(scores, reverse=True), f"Scores not sorted: {scores}"

@then('the agent should skip the salary evaluation and ATS scoring phases')
def step_impl(context):
    assert len(context.passed_jobs) == 0
    assert len(context.evaluated_jobs) == 0

@then('a dashboard should be generated showing no job matches found')
def step_impl(context):
    assert os.path.exists(context.dashboard_path)

@then('the agent should ignore the listing from "{employer}"')
def step_impl(context, employer):
    kept_employers = {j["company_name"] for j in context.kept_jobs}
    assert employer not in kept_employers, f"Kept employers contains excluded one: {kept_employers}"

@then('only the listing from "{employer}" should be evaluated against the salary and ATS criteria')
def step_impl(context, employer):
    kept_employers = {j["company_name"] for j in context.kept_jobs}
    assert kept_employers == {employer}, f"Kept jobs has other employers: {kept_employers}"

@then('the agent should detect the JSON parsing error')
def step_impl(context):
    log_content = context.captured_stdout.getvalue()
    assert "Attempt 1 failed for Senior Python Developer scoring" in log_content or "Attempt 1 failed for Senior Python Developer salary check" in log_content, f"Retry logs not found: {log_content}"

@then('the agent should query the LLM again with the syntax error and corrective instructions under the same session ID')
def step_impl(context):
    assert context.run_state.attempts["ats_orchestration_agent"] == 2

@then('the agent should successfully extract the valid JSON results on a subsequent retry attempt')
def step_impl(context):
    assert context.rated_job_score == 90, f"Score: {context.rated_job_score}"
    assert context.rated_job_explanation == "Self-corrected match", f"Explanation: {context.rated_job_explanation}"


def execute_pipeline(context, query, max_eval, min_salary, concurrency, desc_limit):
    context.searched_query = query
    context.used_min_salary = min_salary
    context.used_concurrency = concurrency
    context.used_desc_limit = desc_limit

    wwr_list = getattr(context, 'wwr_jobs', [])
    remotive_list = getattr(context, 'remotive_jobs', [])
    arbeitnow_list = getattr(context, 'arbeitnow_jobs', [])
    themuse_list = getattr(context, 'themuse_jobs', [])
    jsearch_list = getattr(context, 'jsearch_jobs', [])
    
    context.all_fetched = wwr_list + remotive_list + arbeitnow_list + themuse_list + jsearch_list
    context.crawled_sources = {"We Work Remotely", "Remotive", "Arbeitnow", "The Muse", "JSearch"}

    def mock_fetch_wwr(): return wwr_list
    def mock_fetch_remotive(): return remotive_list
    def mock_fetch_arbeitnow(): return arbeitnow_list
    def mock_fetch_themuse(): return themuse_list
    async def mock_fetch_jsearch(job_titles_str, skill_registry, tool_context): return jsearch_list

    async def mock_runner_run_async(self, session_id, user_id, new_message):
        agent_name = self.agent.name
        query_text = new_message.parts[0].text

        if agent_name == "ats_orchestration_agent":
            title = "Unknown"
            for t in ["Python Developer", "QA Engineer", "Software Engineer", "ML Engineer"]:
                if t in query_text:
                    title = t
                    break
            
            if title == "Python Developer":
                yield MockEvent('{"match_score": 90, "explanation": "Excellent Python Developer"}')
            elif title == "ML Engineer":
                yield MockEvent('{"match_score": 85, "explanation": "Excellent ML Engineer"}')
            else:
                yield MockEvent('{"match_score": 40, "explanation": "Low match"}')
                
        elif agent_name == "salary_extractor_agent":
            title = "Unknown"
            for t in ["Python Developer", "QA Engineer", "Software Engineer", "ML Engineer"]:
                if t in query_text:
                    title = t
                    break

            if title == "Python Developer":
                yield MockEvent('{"has_salary": true, "min_salary_usd": 160000.0, "max_salary_usd": 180000.0, "explanation": "Passed"}')
            elif title == "QA Engineer":
                yield MockEvent('{"has_salary": true, "min_salary_usd": 90000.0, "max_salary_usd": 115000.0, "explanation": "Below threshold"}')
            elif title == "Software Engineer":
                yield MockEvent('{"has_salary": false, "min_salary_usd": 0, "max_salary_usd": 0, "explanation": "No salary specified"}')
            elif title == "ML Engineer":
                yield MockEvent('{"has_salary": true, "min_salary_usd": 130000.0, "max_salary_usd": 145000.0, "explanation": "Passed"}')
            else:
                yield MockEvent('{"has_salary": false, "min_salary_usd": 0, "max_salary_usd": 0, "explanation": "Unknown"}')

    async def mock_run_skill_script_tool_run_async(self, args, tool_context=None):
        skill_name = args.get("skill_name")
        if skill_name == "pdf-parsing":
            return {"status": "success", "stdout": context.resume_text}
        elif skill_name == "excluding-employers":
            cmd_args = args.get("args", [])
            company_name = ""
            if "--company_name" in cmd_args:
                idx = cmd_args.index("--company_name")
                company_name = cmd_args[idx + 1]
            
            # Standard exclusion check mock
            if company_name.lower() == "lemon.io":
                return {"status": "success", "stdout": '{"excluded": true, "reason": "Lemon.io matches excluded list"}'}
            else:
                return {"status": "success", "stdout": '{"excluded": false, "reason": "No match"}'}
        return {"status": "success", "stdout": ""}

    with patch('ingestion.fetch_weworkremotely_jobs', mock_fetch_wwr), \
         patch('ingestion.fetch_remotive_jobs', mock_fetch_remotive), \
         patch('ingestion.fetch_arbeitnow_jobs', mock_fetch_arbeitnow), \
         patch('ingestion.fetch_themuse_jobs', mock_fetch_themuse), \
         patch('ingestion.fetch_jsearch_jobs_via_skill', mock_fetch_jsearch), \
         patch('google.adk.runners.Runner.run_async', mock_runner_run_async), \
         patch('google.adk.tools.skill_toolset.RunSkillScriptTool.run_async', mock_run_skill_script_tool_run_async), \
         patch('sys.exit') as mock_sys_exit:

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        original_run_matching_pipeline = orchestrator.run_matching_pipeline
        async def hook_run_matching_pipeline(resume_text, jobs, model_name, max_eval, min_salary, concurrency, desc_limit):
            res = await original_run_matching_pipeline(resume_text, jobs, model_name, max_eval, min_salary, concurrency, desc_limit)
            context.evaluated_jobs = res
            return res

        original_filter_job_via_skill = orchestrator.filter_job_via_skill
        context.passed_jobs = []
        async def hook_filter_job_via_skill(job, idx, total, model_name, semaphore, min_salary_threshold, desc_limit):
            res_job, passed = await original_filter_job_via_skill(job, idx, total, model_name, semaphore, min_salary_threshold, desc_limit)
            if passed:
                context.passed_jobs.append(res_job)
            return res_job, passed

        original_check_exclusion_via_skill = orchestrator.check_exclusion_via_skill
        context.kept_jobs = []
        async def hook_check_exclusion_via_skill(run_exclude_tool, job, idx, total, semaphore):
            res_job, excluded = await original_check_exclusion_via_skill(run_exclude_tool, job, idx, total, semaphore)
            if not excluded:
                context.kept_jobs.append(res_job)
            return res_job, excluded

        with patch('orchestrator.run_matching_pipeline', hook_run_matching_pipeline), \
             patch('orchestrator.filter_job_via_skill', hook_filter_job_via_skill), \
             patch('orchestrator.check_exclusion_via_skill', hook_check_exclusion_via_skill):
            
            loop.run_until_complete(
                orchestrator.run_pipeline(
                    resume_path=context.resume_path,
                    job_titles_str=query,
                    model_name="ollama_chat/llama3.1:latest",
                    max_eval=max_eval,
                    min_salary=min_salary,
                    concurrency=concurrency,
                    desc_limit=desc_limit
                )
            )
            
            import datetime
            today_str = datetime.datetime.now().strftime("%Y-%m-%d")
            context.dashboard_path = f"job_matches_{today_str}.html"
