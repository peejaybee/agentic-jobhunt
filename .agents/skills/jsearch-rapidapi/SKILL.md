---
name: jsearch-rapidapi
description: Searches jobs using JSearch via RapidAPI with environment credentials.
metadata:
  author: Antigravity
  license: Apache-2.0
  version: 1.0.0
---

# JSearch Skill (RapidAPI)

This skill queries job postings from the JSearch endpoint on RapidAPI using environment credentials.

## Scripts
- **`scripts/search_jsearch.py`**: A CLI script to fetch and format JSearch jobs.
  - Arguments:
    - `--query`: Search query string (e.g., `"Python Developer in Remote"`).
    - `--page`: Page number to fetch (default: `1`).
    - `--num_pages`: Number of pages to retrieve (default: `1`).
  - Environment Variables:
    - `X-RapidAPI-Key`: Your RapidAPI access key.
    - `X-RapidAPI-Host`: Your RapidAPI host (default: `"jsearch.p.rapidapi.com"`).
  - Output: Prints a JSON array of normalized job listings to stdout.

## Usage
Run the script using `run_skill_script`:
```json
{
  "skill_name": "jsearch-rapidapi",
  "file_path": "scripts/search_jsearch.py",
  "args": {
    "--query": "Software Engineer in Remote"
  }
}
```
