import argparse
import os
import sys
import json

def main():
    parser = argparse.ArgumentParser(description="Check if employers are on the exclusion list")
    parser.add_argument("--companies", nargs="+", required=True, help="List of companies/employers to check")
    parser.add_argument("--file_path", default="excluded_employers.txt", help="Path to the excluded employers text file")
    args = parser.parse_args()

    # Determine script and workspace root to load the exclusion list robustly
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.abspath(os.path.join(script_dir, "../../../.."))
    
    if not os.path.isabs(args.file_path):
        file_path = os.path.join(workspace_root, args.file_path)
    else:
        file_path = args.file_path

    # Read exclusion rules once
    rules = []
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
                    rules.append(item)
        except Exception as e:
            sys.stderr.write(f"Error reading exclusion file: {e}\n")

    results = {}
    for company in args.companies:
        excluded = False
        reason = "Company is not in the exclusion list."
        company_lower = company.strip().lower()

        for rule in rules:
            rule_lower = rule.lower()
            # Case-insensitive substring match both ways to catch variations
            if rule_lower in company_lower or company_lower in rule_lower:
                excluded = True
                reason = f"Company '{company}' is excluded by rule matching '{rule}'."
                break
        
        results[company] = {
            "excluded": excluded,
            "reason": reason
        }

    print(json.dumps(results))

if __name__ == "__main__":
    main()
