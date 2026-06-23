import argparse
import asyncio
import os
import sys

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

from dotenv import load_dotenv
load_dotenv()

import orchestrator


async def main():
    parser = argparse.ArgumentParser(description="ATS Remote Job Search and Resume Matcher Agent")
    parser.add_argument("--resume", required=True, help="Path to local PDF resume file")
    parser.add_argument("--titles", required=True, help="Comma-separated list of job titles to search (e.g., 'Python Developer, Software Engineer')")
    parser.add_argument("--model", default="ollama_chat/llama3.1:latest", help="Ollama model to use in LiteLLM format (default: 'ollama_chat/llama3.1:latest')")
    parser.add_argument("--max-eval", type=int, default=30, help="Maximum number of filtered jobs to rate using local LLM (default: 30)")
    parser.add_argument("--min-salary", type=int, default=150000, help="Minimum salary threshold in USD to keep a job (default: 150000)")
    parser.add_argument("--concurrency", type=int, default=3, help="Maximum concurrent LLM calls allowed (default: 3)")
    parser.add_argument("--desc-limit", type=int, default=10000, help="Character limit for truncating job descriptions sent to LLMs (default: 10000)")
    args = parser.parse_args()
    
    print("=" * 60)
    print(" ATS Remote Job Matcher & Scoring System (Multi-Skill Architecture)")
    print("=" * 60)
    
    await orchestrator.run_pipeline(
        resume_path=args.resume,
        job_titles_str=args.titles,
        model_name=args.model,
        max_eval=args.max_eval,
        min_salary=args.min_salary,
        concurrency=args.concurrency,
        desc_limit=args.desc_limit
    )

if __name__ == "__main__":
    # Ensure correct event loop policy on Windows for subprocesses (needed by some async frameworks)
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
