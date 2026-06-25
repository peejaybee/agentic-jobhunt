---
name: ats-scoring
description: Performs ATS-style evaluation of a candidate resume against a single job description using a local LLM via Ollama and ADK.
metadata:
  author: Google
  license: Apache-2.0
  version: 3.0.0
---

# ATS Scoring Skill

This skill performs an ATS (Applicant Tracking System) style evaluation on a single job description against candidate resume text.

## Instructions
Analyze the candidate's resume against the provided job description and evaluate their match suitability.

1. **Evaluation Scope**: Evaluate strictly based on matching skills, programming languages, years of experience, and general job requirements.
2. **Match Score Scale**: Rate the match from 0 to 100:
   - **80-100**: Excellent fit (matches all core tech stacks and experience level)
   - **50-79**: Moderate fit (matches some tech stack, minor gaps in experience or peripheral tools)
   - **0-49**: Poor fit (lacks core technologies or has major level mismatch)
3. **Explanation**: Provide a brief paragraph (2-3 sentences) summarizing key matches and critical skill gaps.
4. **Attribution Isolation**: Do not assume the candidate possesses experience in a specific region, tool, or industry sector simply because it is listed in the job description. All candidate experience must be verified exclusively from the provided resume text.

## Expected Output Format
You MUST return your final response strictly as a JSON object matching this schema:
```json
{
  "match_score": 85, // Integer from 0 to 100
  "explanation": "Summarizing paragraph here."
}
```
Do NOT wrap the JSON in other markdown formatting outside of the standard JSON block. Ensure only valid JSON is returned.
