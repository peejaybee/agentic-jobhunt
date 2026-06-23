---
name: pdf-parsing
description: Extracts text from local PDF files (specifically resumes) using the pypdf library.
metadata:
  author: Google
  license: Apache-2.0
  version: 1.0.0
---

# PDF Parsing Skill

This skill extracts clean, plain text from local PDF documents, such as candidate resumes.

## Scripts
- **`scripts/pdf_parser.py`**: A CLI script to parse a PDF.
  - Arguments:
    - `--pdf`: The absolute or relative path to the local PDF file.
  - Output: Prints the extracted plain text to stdout.

## Usage
Run the script using `run_skill_script`:
```json
{
  "skill_name": "pdf-parsing",
  "file_path": "scripts/pdf_parser.py",
  "args": ["--pdf", "sample_resume.pdf"]
}
```
