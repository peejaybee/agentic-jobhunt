---
name: excluding-employers
description: Excludes jobs from specific employers listed in a text file.
metadata:
  author: Antigravity
  license: Apache-2.0
  version: 1.0.0
---

# Excluding Employers Skill

This skill reads a list of excluded employers from a text file and checks if a given company/employer name matches any entries in the list.

## Scripts
- **`scripts/exclude_employers.py`**: A CLI script to check if an employer is excluded.
  - Arguments:
    - `--company_name`: The company/employer name of the job listing.
    - `--file_path`: Path to the text file containing the excluded employers (default: `excluded_employers.txt` at workspace root).
  - Output: Prints a JSON object to stdout containing:
    - `excluded`: Boolean (True if the employer is excluded, False otherwise).
    - `reason`: A brief explanation of the decision.

## Usage
Run the script using `run_skill_script`:
```json
{
  "skill_name": "excluding-employers",
  "file_path": "scripts/exclude_employers.py",
  "args": {
    "--company_name": "Lemon.io",
    "--file_path": "excluded_employers.txt"
  }
}
```
