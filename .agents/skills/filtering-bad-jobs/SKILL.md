---
name: filtering-bad-jobs
description: Excludes jobs that pay less than $150,000/year or do not specify a pay range.
metadata:
  author: Google
  license: Apache-2.0
  version: 1.0.0
---

# Filtering Bad Jobs Skill

This skill parses a job description to extract salary/pay ranges, normalize them to USD/year, and determine if they meet the criteria ($150,000/year minimum, and salary must be specified).

## Scripts
- **`scripts/filter_jobs.py`**: A CLI script to evaluate if a job meets the criteria.
  - Arguments:
    - `--job_title`: The title of the job.
    - `--job_desc`: The text description of the job.
    - `--model`: The local Ollama model to use (default: `ollama_chat/llama3.1:latest`).
  - Output: Prints a JSON string to stdout containing:
    - `passed`: Boolean (True if the job has a salary listing of at least $150,000/year).
    - `reason`: A brief explanation of the decision (e.g. no salary listed, salary below $150k, etc.).
    - `min_salary`: Estimated minimum salary in USD/year.
    - `max_salary`: Estimated maximum salary in USD/year.

## Usage
Run the script using `run_skill_script`:
```json
{
  "skill_name": "filtering-bad-jobs",
  "file_path": "scripts/filter_jobs.py",
  "args": {
    "--job_title": "Senior Data Scientist",
    "--job_desc": "Compensation: $160,000 - $190,000 per year...",
    "--model": "ollama_chat/llama3.1:latest"
  }
}
```
