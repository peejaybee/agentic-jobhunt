import argparse
import asyncio
import json
import os
import sys
from pydantic import BaseModel, Field

# Import Google ADK modules
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

class SalaryFilterResult(BaseModel):
    has_salary: bool = Field(description="True if a salary, pay range, hourly rate, or compensation details are mentioned in the job description or title, False otherwise.")
    min_salary_usd: float = Field(description="Estimated minimum salary normalized to USD per year (e.g. hourly rate of $80/hr is ~$160k/yr). Set to 0 if not listed.")
    max_salary_usd: float = Field(description="Estimated maximum salary normalized to USD per year. Set to 0 if not listed.")
    explanation: str = Field(description="A brief sentence explaining what salary was found and if it matches the $150k/year threshold.")

async def filter_job_salary(job_title: str, job_desc: str, model_name: str) -> str:
    """Invokes the ADK Agent to extract salary details and verify requirements."""
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="salary_filter",
        user_id="anonymous"
    )
    
    model = LiteLlm(model=model_name)
    
    agent = Agent(
        model=model,
        name="salary_extractor_agent",
        instruction=(
            "You are a compensation analysis assistant. Your job is to extract salary/pay ranges from the "
            "job description and title, and normalize them to an annual USD amount.\n\n"
            "Guidelines:\n"
            "- If hourly rates are listed, assume 2000 hours per year (e.g., $75/hr = $150,000/yr).\n"
            "- If monthly rates are listed, multiply by 12 (e.g., $10,000/month = $120,000/yr).\n"
            "- If no salary, pay range, or hourly rate is mentioned, set has_salary to False and salaries to 0.\n"
            "- Return your final output in the requested schema format."
        ),
        output_schema=SalaryFilterResult
    )
    
    runner = Runner(
        app_name="salary_filter",
        agent=agent,
        session_service=session_service
    )
    
    cleaned_desc = job_desc[:8000]
    
    user_query = (
        f"Analyze this job listing for salary or compensation info.\n\n"
        f"--- JOB TITLE ---\n{job_title}\n\n"
        f"--- JOB DESCRIPTION ---\n{cleaned_desc}\n"
    )
    
    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_query)]
    )
    
    response_text = ""
    async for event in runner.run_async(
        session_id=session.id,
        user_id=session.user_id,
        new_message=content
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
                    
    return response_text

def main():
    parser = argparse.ArgumentParser(description="Filter job listings based on salary")
    parser.add_argument("--job_title", default="Job Opportunity", help="Job Title")
    parser.add_argument("--job_desc", required=True, help="Job description text")
    parser.add_argument("--model", default="ollama_chat/llama3.1:latest", help="Ollama model to use")
    args = parser.parse_args()
    
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        result_str = asyncio.run(filter_job_salary(
            job_title=args.job_title,
            job_desc=args.job_desc,
            model_name=args.model
        ))
        
        # Parse the JSON from the agent response
        json_start = result_str.find("{")
        json_end = result_str.rfind("}") + 1
        if json_start != -1 and json_end != 0:
            parsed = json.loads(result_str[json_start:json_end])
            has_salary = parsed.get("has_salary", False)
            max_salary = parsed.get("max_salary_usd", 0.0)
            min_salary = parsed.get("min_salary_usd", 0.0)
            explanation = parsed.get("explanation", "")
            
            passed = has_salary and max_salary >= 150000
            
            if not has_salary:
                reason = "No salary range or pay range is listed in the posting."
            elif not passed:
                reason = f"Salary max ({max_salary}) is below the required $150,000 threshold. (Range: {min_salary}-{max_salary})"
            else:
                reason = f"Salary matches threshold: max {max_salary} meets or exceeds $150,000. (Range: {min_salary}-{max_salary})"
                
            out = {
                "passed": passed,
                "reason": reason,
                "min_salary": min_salary,
                "max_salary": max_salary
            }
        else:
            out = {
                "passed": False,
                "reason": f"Agent failed to return structured salary output. Raw: {result_str}",
                "min_salary": 0.0,
                "max_salary": 0.0
            }
            
        print(json.dumps(out))
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "reason": f"Error running filter: {e}",
            "min_salary": 0.0,
            "max_salary": 0.0
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
