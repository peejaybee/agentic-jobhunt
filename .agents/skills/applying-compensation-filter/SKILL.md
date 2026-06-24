---
name: applying-compensation-filter
description: Excludes jobs that pay less than $150,000/year or do not specify a pay range.
metadata:
  author: Google
  license: Apache-2.0
  version: 2.0.0
---

# Applying Compensation Filter Skill

This skill parses a job description to extract salary/pay ranges, normalize them to USD/year, and determine if they meet the criteria ($150,000/year minimum, and salary must be specified).

## Instructions
Analyze the job description and title for explicit numerical compensation information.

1. **Strict Extraction**: 
   - Identify if any **explicit numerical salary, pay range, or hourly rate** is mentioned. 
   - **CRITICAL**: Do NOT guess, estimate, infer, or use "industry standards" to invent numbers if they are not explicitly written.
   - Phrases like "competitive salary", "market rate", "commensurate with experience", "excellent compensation", or "benefits" without actual numbers do NOT count. For such listings, you MUST set `has_salary` to `false` and both `min_salary_usd` and `max_salary_usd` to `0.0`.
2. **USD Normalization**: Convert the **explicitly listed numbers** to an annual USD amount:
   - If hourly rates are listed, assume 2000 hours per year (e.g., $75/hr = $150,000/yr).
   - If monthly rates are listed, multiply by 12 (e.g., $10,000/month = $120,000/yr).
3. **Threshold Check**: Verify if the maximum normalized salary meets or exceeds **$150,000/year**.
4. **Decision Logic**:
   - `has_salary` is `true` ONLY if explicit numerical salary/hourly figures are present in the text.
   - `passed` is `true` if `has_salary` is `true` AND the maximum salary meets or exceeds $150,000/year.
   - `passed` is `false` if `has_salary` is `false` OR if the maximum salary is below $150,000/year.

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
