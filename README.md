# ATS Job Matcher & Scoring Agent

An AI-powered, multi-skill remote job crawler and resume evaluation agent. It aggregates remote job postings across multiple feeds, performs safety and employer exclusion checks, filters them based on compensation requirements, ranks them against your PDF resume using local LLM agents via Ollama, and generates a beautiful interactive glassmorphic dashboard.

---

## Features & Multi-Skill Architecture

The agent is built using the Google ADK framework and orchestrates five modular skills located under `.agents/skills/`:

1. **`pdf-parsing`** (Script-Based): Extracts text from local PDF resumes using the `pypdf` library.
2. **`excluding-employers`** (Script-Based): Filters out listings from companies specified in `excluded_employers.txt` (e.g. Lemon.io) using case-insensitive checks.
3. **`jsearch-rapidapi`** (Script-Based): Queries high-volume web job postings using JSearch via RapidAPI.
4. **`filtering-bad-jobs`** (In-Process Agent): Uses a local LLM agent to parse unstructured job descriptions, normalize salary ranges to USD/year, and exclude listings that pay below your target threshold or omit compensation information.
5. **`ats-scoring`** (In-Process Agent): Evaluates resume compatibility against qualified job descriptions, returning a match suitability score (0-100) and structured AI recruiter feedback.

### Advanced Agentic Behaviors
* **Progressive Disclosure**: Reconfigured to use a dynamic `LocalSkillRegistry`. Instead of hardcoding skill data, the orchestrator loads `SKILL.md` definitions dynamically from disk only when a skill tool is invoked.
* **Self-Correction (Reflexivity)**: In-process LLM agent runners feature built-in syntax correction. If the local LLM generates a malformed response or invalid JSON structure, the runner intercepts the error and re-prompts the model with error feedback under the *same session context* to self-correct.
* **Security Sanitization**: Utilizes a custom `SafeHTMLSanitizer` parser to strip dangerous HTML tags (e.g., `<script>`, `<iframe>`), dangerous attributes (`onclick`, `onload`), and unescaped payloads from job descriptions before rendering them in the HTML dashboard (mitigating XSS).

---

## Prerequisites

* **Python 3.8+**
* **Ollama**: Run Ollama locally with the default model downloaded:
  ```bash
  ollama pull llama3.1:latest
  ```
* **JSearch API Account**: RapidAPI credentials (see below).

---

## Setup & Installation

1. **Clone the Repository** and navigate into the workspace.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Create the Environment File**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
4. **Add JSearch API Credentials**:
   Open `.env` and fill in your RapidAPI key and host values (Note: `.env` is ignored by Git to keep your keys safe).

---

## How to Sign Up for JSearch on RapidAPI

1. Go to the [JSearch API page on RapidAPI](https://rapidapi.com/letscrape-it-letscrape-it-default/api/jsearch).
2. Click **Log In** or **Sign Up** to create a free account.
3. Subscribe to the **Basic** plan (includes 50 free requests per month, ideal for daily cron/scheduled runs).
4. Go to the **Endpoints** tab in the API playground.
5. In the request headers block on the right, find:
   * `x-rapidapi-key`: Copy this and paste it as `X-RapidAPI-Key` in `.env`.
   * `x-rapidapi-host`: Copy this (should be `jsearch.p.rapidapi.com`) and paste it as `X-RapidAPI-Host` in `.env`.

---

## How to Run

### 1. Interactive Mode
Double-click or run `run.bat` on Windows. It will prompt you for the path to your resume, search terms, and the local Ollama model to use.

### 2. Command Line Mode
Run the Python script directly by passing parameters:
```bash
python job_matcher_agent.py --resume resume.pdf --titles "Python Developer, Software Engineer" --max-eval 10 --min-salary 120000 --concurrency 2
```

#### CLI Parameters:
* `--resume`: (Required) Path to your local PDF resume.
* `--titles`: (Required) Comma-separated list of keywords/job titles to match.
* `--model`: LiteLLM-compatible Ollama model name (default: `ollama_chat/llama3.1:latest`).
* `--max-eval`: Maximum number of qualified jobs to score using the local LLM (default: `30`).
* `--min-salary`: Minimum salary threshold in USD to keep a job (default: `150000`).
* `--concurrency`: Maximum concurrent LLM calls allowed (default: `3`). Capping concurrency protects local LLMs from CPU/GPU memory exhaustion.
* `--desc-limit`: Character limit for truncating job descriptions sent to LLMs (default: `10000`). Keeps token windows compact.

---

## Scheduling the Agent (Windows 11 Task Scheduler)

To run the agent automatically every weekday at 1:00 AM:

### Step 1: Customize `run_scheduled.bat`
Open `run_scheduled.bat` in a text editor and update the paths and arguments to your liking:
```bat
@echo off
cd /d "%~dp0"
python job_matcher_agent.py --resume C:\path\to\your\resume.pdf --titles "Python Developer, Software Engineer, Data Scientist" --max-eval 10 --min-salary 150000 --concurrency 3 --desc-limit 10000
```

### Step 2: Set Up Task Scheduler
1. Press the **Windows Key**, type **Task Scheduler**, and press **Enter**.
2. Click **Create Basic Task** in the Actions panel on the right.
3. **Name**: `ATS Job Matcher`
4. **Trigger**: Select **Weekly**, click Next.
   * Start Date: Select today.
   * Start Time: Set to `1:00:00 AM`.
   * Days: Check **Monday, Tuesday, Wednesday, Thursday, and Friday**. Click Next.
5. **Action**: Select **Start a program**, click Next.
6. **Program/script**: Click Browse and select your customized `run_scheduled.bat` (e.g., `E:\Development\agentic-jobhunt\run_scheduled.bat`).
7. **Start in (optional)**: Set to the workspace directory path (e.g., `E:\Development\agentic-jobhunt`).
8. Click **Finish**.

Now, your agent will crawl job boards, score the best listings, and generate a new date-stamped HTML dashboard file in your folder every weekday morning.
