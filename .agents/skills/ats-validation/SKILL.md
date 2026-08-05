---
name: ats-validation
description: Performs a validation check on ATS scores and explanations to catch hallucinations and timezone mismatches.
metadata:
  author: Google
  license: Apache-2.0
  version: 1.0.0
---

# ATS Validation Skill

This skill performs a second-pass quality assurance check on an ATS evaluation to ensure it is accurate and does not contain skill hallucinations or timezone mismatches.

## Instructions

Analyze the candidate's resume, the job description, and the primary evaluation (score and explanation) to audit for errors.

1. **Audit for Skill Hallucinations**:
   - Verify that every technical skill or technology claimed as a match in the primary explanation is explicitly listed or clearly supported by the candidate's resume.
   - If the primary explanation claims the candidate has experience or knowledge of key required technologies (e.g. Kotlin, Android, Jetpack, Meta Ads, etc.) that are NOT found in the resume, you must mark this as a hallucination.
   - **Audit for Contextual Conflation**: Verify that matched terms have matching semantic meanings and contexts. If the primary evaluator matched a term that is contextually different in the resume (e.g. treating "remote-control" or "control equipment" as a match for "control systems", "control techniques", or "control theory"), you must mark this as a validation hallucination error, set `is_valid` to `false`, set `corrected_score` to `0`, and explain the semantic mismatch in `validation_notes`.

2. **Audit for Timezone & Location Mismatches**:
   - The candidate is located in the United States and works remotely.
   - Any remote job located in the United States or open to US candidates is **ALWAYS acceptable**.
   - ONLY mark a location constraint violation if the job description **explicitly requires physical residency outside the United States** (e.g. "Must reside in UK/Europe/APAC", "Germany only") or **explicitly excludes US residents**, or **explicitly excludes candidates residing in Illinois**. Do NOT flag a violation for US remote jobs that mention global teams, international headquarters, or general legal/privacy notices referencing other countries (e.g., Australian privacy disclaimers).

3. **Validation Decision**:
   - If any hallucination or timezone constraint violation is found, set `is_valid` to `false`, set `corrected_score` to `0`, and write `validation_notes` detailing the exact corrections made (e.g. "Validation failed: Candidate does not have Kotlin/Android experience as claimed" or "Validation failed: Timezone mismatch with CET").
   - If the evaluation is accurate and supported by the resume, set `is_valid` to `true`, set `corrected_score` to the primary evaluator's score, and set `validation_notes` to a brief statement confirming the evaluation is correct.

## Expected Output Format
You MUST return your final response strictly as a JSON object matching this schema:
```json
{
  "is_valid": true, // Boolean
  "corrected_score": 85, // Integer from 0 to 100
  "validation_notes": "Validation explanation here."
}
```
Do NOT wrap the JSON in other markdown formatting outside of the standard JSON block. Ensure only valid JSON is returned.
