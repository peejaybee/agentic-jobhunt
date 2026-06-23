import argparse
import os
import sys
from pypdf import PdfReader

def extract_resume_text(pdf_path: str) -> str:
    """Extracts text from a local PDF resume."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Resume file not found at: {pdf_path}")
    
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()

def main():
    parser = argparse.ArgumentParser(description="Extract text from PDF resume")
    parser.add_argument("--pdf", required=True, help="Path to local PDF resume")
    args = parser.parse_args()
    
    try:
        text = extract_resume_text(args.pdf)
        print(text)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
