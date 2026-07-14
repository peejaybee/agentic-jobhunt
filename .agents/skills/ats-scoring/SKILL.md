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

1. **Evaluation Scope & Constraints**:
   - Evaluate strictly based on matching skills, programming languages, years of experience, and general job requirements.
   - **Timezone & Location Constraints**: The candidate is located in the United States and is compatible with working in **Eastern (EST/EDT)**, **Central (CST/CDT)**, **Mountain (MST/MDT)**, or **Pacific (PST/PDT)** timezones.
   - If the job description explicitly requires residency or working hours in a different region or timezone (e.g. CET, CEST, GMT, UTC+1, EMEA, Europe, UK, APAC, or countries outside the US), you **MUST** fail the evaluation: cap the `match_score` at **0** and state the timezone or geographic mismatch as the primary reason in the `explanation`.
2. **Match Score Scale**: Rate the match from 0 to 100:
   - **80-100**: Excellent fit (matches all core tech stacks and experience level)
   - **50-79**: Moderate fit (matches some tech stack, minor gaps in experience or peripheral tools)
   - **0-49**: Poor fit (lacks core technologies or has major level mismatch)
3. **Explanation**: Provide a brief paragraph (2-3 sentences) summarizing key matches and critical skill gaps.
4. **Attribution Isolation & Anti-Hallucination**:
   - Do not assume, extrapolate, or invent any candidate experience or skills.
   - If a technology, tool, or skill (e.g. Meta Ads, Google Ads) is listed in the job description but is NOT explicitly mentioned in the candidate's resume, you must assume the candidate has ZERO experience in it and list it as a gap.
   - Every matched skill claimed in the explanation MUST be directly backed by the resume. Do not hallucinate matches.

## Expected Output Format
You MUST return your final response strictly as a JSON object matching this schema:
```json
{
  "match_score": 85, // Integer from 0 to 100
  "explanation": "Summarizing paragraph here."
}
```
Do NOT wrap the JSON in other markdown formatting outside of the standard JSON block. Ensure only valid JSON is returned.
