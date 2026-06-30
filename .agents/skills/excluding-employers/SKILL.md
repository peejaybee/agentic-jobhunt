---
name: excluding-employers
description: Excludes jobs from specific employers listed in a text file.
metadata:
  author: Antigravity
  license: Apache-2.0
  version: 1.0.0
---

# Excluding Employers Skill

This skill reads a list of excluded employers from a text file and checks if a given list of company/employer names matches any entries in the list.

## Scripts
- **`scripts/exclude_employers.py`**: A CLI script to check if multiple employers are excluded.
  - Arguments:
    - `--companies`: A space-separated list of company/employer names of the job listings.
    - `--file_path`: Path to the text file containing the excluded employers (default: `excluded_employers.txt` at workspace root).
  - Output: Prints a JSON object to stdout containing a mapping of company names to their exclusion results:
    - Each key is the company name.
    - The value is an object containing `excluded` (Boolean) and `reason` (String).

## Usage
Run the script using `run_skill_script`:
```json
{
  "skill_name": "excluding-employers",
  "file_path": "scripts/exclude_employers.py",
  "args": {
    "--companies": ["example.com", "Google"],
    "--file_path": "excluded_employers.txt"
  }
}
```
