import argparse
import os
import sys
import json

def main():
    parser = argparse.ArgumentParser(description="Check if an employer is on the exclusion list")
    parser.add_argument("--company_name", required=True, help="Name of the company/employer to check")
    parser.add_argument("--file_path", default="excluded_employers.txt", help="Path to the excluded employers text file")
    args = parser.parse_args()

    # Determine script and workspace root to load the exclusion list robustly
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.abspath(os.path.join(script_dir, "../../../.."))
    
    if not os.path.isabs(args.file_path):
        file_path = os.path.join(workspace_root, args.file_path)
    else:
        file_path = args.file_path

    excluded = False
    reason = "Company is not in the exclusion list."
    company_name_lower = args.company_name.strip().lower()

    if not os.path.exists(file_path):
        # If the file does not exist, log to stderr and default to not excluded
        sys.stderr.write(f"Warning: Exclusion file not found at: {file_path}. Skipping checks.\n")
    else:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    item = line.strip()
                    if not item or item.startswith("#"):
                        continue
                    item_lower = item.lower()
                    
                    # Case-insensitive substring match both ways to catch variations
                    if item_lower in company_name_lower or company_name_lower in item_lower:
                        excluded = True
                        reason = f"Company '{args.company_name}' is excluded by rule matching '{item}'."
                        break
        except Exception as e:
            sys.stderr.write(f"Error reading exclusion file: {e}\n")

    print(json.dumps({
        "excluded": excluded,
        "reason": reason
    }))

if __name__ == "__main__":
    main()
