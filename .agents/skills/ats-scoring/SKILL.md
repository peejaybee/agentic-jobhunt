---
name: ats-scoring
description: Performs ATS-style evaluation of a candidate resume against a single job description using a local LLM via Ollama and ADK.
metadata:
  author: Google
  license: Apache-2.0
  version: 2.0.0
---

# ATS Scoring Skill

This skill performs ATS (Applicant Tracking System) style evaluation on a single job description against resume text.

## Scripts
- **`scripts/ats_scorer.py`**: A CLI script to evaluate a job description.
  - Arguments:
    - `--resume_text`: Plain text content of the resume.
    - `--job_title`: The title of the job.
    - `--job_company`: The company name.
    - `--job_desc`: The text description of the job.
    - `--model`: The local Ollama model to use (default: `ollama_chat/llama3.1:latest`).
  - Output: Prints a JSON string to stdout containing:
    - `match_score`: An integer from 0 to 100.
    - `explanation`: A summary of matching skills and gaps.

## Usage
Run the script using `run_skill_script`:
```json
{
  "skill_name": "ats-scoring",
  "file_path": "scripts/ats_scorer.py",
  "args": {
    "--resume_text": "extracted resume text here",
    "--job_title": "Software Engineer",
    "--job_company": "Tech Corp",
    "--job_desc": "Full job description here",
    "--model": "ollama_chat/llama3.1:latest"
  }
}
```
