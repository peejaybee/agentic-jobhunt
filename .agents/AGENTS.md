# Workspace-Scoped Agent Rules

These rules apply to any agentic AI assistants working on the `agentic-jobhunt` project. You MUST read, understand, and comply with these rules at all times.

---

## 1. Documentation & Specification Alignment
* **Requirement**: Whenever you modify command-line arguments, environment configurations, pipeline execution steps, or job ingestion rules, you MUST update:
  1. **`README.md`**: To explain new options, setup details, or execution commands.
  2. **`features/job_matcher.feature`**: To update the Gherkin BDD scenario descriptions to match the new behavior.
* **Testing Specs**: After making any changes that impact pipeline orchestration, you MUST run BDD tests locally using the `behave` command to verify that all Gherkin scenarios compile and pass.

---

## 2. Dynamic Skill Loading & Progressive Disclosure
* **Requirement**: Do NOT hardcode skill definitions or static lists of skills inside `orchestrator.py` or agent scripts.
* **Registry Use**: Always query and load skills dynamically via `LocalSkillRegistry` and a `SkillToolset(registry=...)` when executing tools. This keeps the agent context compact and prevents static coupling.

---

## 3. Stateless Execution & Isolation
* **Requirement**: Ensure all job evaluations remain stateless and isolated.
* **Session Scope**: Always instantiate a new `InMemorySessionService` and create a distinct `session` inside evaluation helper functions (`evaluate_single_job_via_skill` and `filter_job_via_skill`). Do NOT reuse session IDs across different job cards.

---

## 4. Input Truncation & GPU Guardrails
* **Requirement**: When passing third-party job descriptions or resume text to local LLMs, always apply proactive character truncation (e.g. `[:desc_limit]`) to protect GPU memory and prevent context window overflow or attention loss.

---

## 5. Automated Testing Permission
* **Pre-Approval**: Running the BDD tests using the command `python -m behave` is always pre-approved by the user. You may execute this command at any time during development or verification without requesting explicit confirmation.

---

## 6. Git Branching & Workflows
* **Requirement**: All development work must be performed on a Git branch named `update`. Do NOT commit directly to the `main` branch.
