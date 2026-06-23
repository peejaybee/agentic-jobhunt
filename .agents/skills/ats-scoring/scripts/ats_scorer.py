import argparse
import asyncio
import os
import sys
from pydantic import BaseModel, Field

# Import Google ADK modules
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

# Define the Pydantic schema for structured output
class JobMatchRating(BaseModel):
    match_score: int = Field(description="ATS match score from 0 to 100 based on resume skills, experience, and job description fit.")
    explanation: str = Field(description="A brief paragraph (2-3 sentences) summarizing key matches and critical skill gaps.")

async def evaluate_single_job(resume_text: str, job_title: str, job_company: str, job_desc: str, model_name: str) -> str:
    """Invokes the ADK Agent to evaluate a job description against the resume."""
    # 1. Initialize ADK session service
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="ats_job_evaluator",
        user_id="anonymous"
    )
    
    # 2. Setup LiteLlm model pointing to local Ollama
    model = LiteLlm(model=model_name)
    
    # 3. Create the agent with instruction and output Pydantic schema
    agent = Agent(
        model=model,
        name="ats_rating_agent",
        instruction=(
            "You are a professional recruiting coordinator. Your job is to analyze the candidate's resume "
            "against the provided job description and evaluate their match suitability.\n\n"
            "Evaluate strictly based on skills, programming languages, years of experience, and job requirements.\n"
            "Rate from 0 to 100:\n"
            "- 80-100: Excellent fit (matches all core tech stacks and experience level)\n"
            "- 50-79: Moderate fit (matches some tech stack, minor gaps in experience or peripheral tools)\n"
            "- 0-49: Poor fit (lacks core technologies or has major level mismatch)\n\n"
            "Return your final rating in the requested schema format."
        ),
        output_schema=JobMatchRating
    )
    
    # 4. Instantiate the runner
    runner = Runner(
        app_name="ats_job_evaluator",
        agent=agent,
        session_service=session_service
    )
    
    # Clean description HTML text slightly for LLM efficiency (or pass as is)
    cleaned_desc = job_desc[:10000] 
    
    user_query = (
        f"Please rate my resume against this job posting.\n\n"
        f"--- MY RESUME ---\n{resume_text}\n\n"
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
    parser = argparse.ArgumentParser(description="Evaluate job against resume")
    parser.add_argument("--resume_text", required=True, help="Text content of the resume")
    parser.add_argument("--job_title", default="Job Opportunity", help="Job Title")
    parser.add_argument("--job_company", default="Company", help="Company Name")
    parser.add_argument("--job_desc", required=True, help="Job description text")
    parser.add_argument("--model", default="ollama_chat/llama3.1:latest", help="Ollama model to use")
    args = parser.parse_args()
    
    # Run async function
    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        result = asyncio.run(evaluate_single_job(
            resume_text=args.resume_text,
            job_title=args.job_title,
            job_company=args.job_company,
            job_desc=args.job_desc,
            model_name=args.model
        ))
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
