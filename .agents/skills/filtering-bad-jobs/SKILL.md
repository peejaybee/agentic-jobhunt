---
name: filtering-bad-jobs
description: Excludes jobs that pay less than $150,000/year or do not specify a pay range.
metadata:
  author: Google
  license: Apache-2.0
  version: 2.0.0
---

# Filtering Bad Jobs Skill

This skill parses a job description to extract salary/pay ranges, normalize them to USD/year, and determine if they meet the criteria ($150,000/year minimum, and salary must be specified).

## Instructions
Analyze the job description and title for compensation, salary, or pay range information.

1. **Extraction**: Identify if any salary, pay range, hourly rate, or compensation details are mentioned in the job description or title.
2. **USD Normalization**: Convert the extracted numbers to an annual USD amount:
   - If hourly rates are listed, assume 2000 hours per year (e.g., $75/hr = $150,000/yr).
   - If monthly rates are listed, multiply by 12 (e.g., $10,000/month = $120,000/yr).
   - If no salary details are specified, flag it.
3. **Threshold Check**: Verify if the maximum normalized salary meets or exceeds **$150,000/year**.
4. **Decision Logic**:
   - `passed` is `true` if a salary/pay range is specified AND the maximum salary meets or exceeds $150,000/year.
   - `passed` is `false` if no salary is listed OR if the maximum salary is below $150,000/year.

## Expected Output Format
You MUST return your final response strictly as a JSON object matching this schema:
```json
{
  "has_salary": true, // Boolean indicating if any salary info was found
  "min_salary_usd": 120000.0, // Estimated minimum salary normalized to USD per year, 0 if not listed
  "max_salary_usd": 160000.0, // Estimated maximum salary normalized to USD per year, 0 if not listed
  "explanation": "Summarizing sentence explaining the decision."
}
```
Do NOT wrap the JSON in other markdown formatting outside of the standard JSON block. Ensure only valid JSON is returned.
