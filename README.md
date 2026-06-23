# ATS Job Matcher & Scoring Agent

An AI-powered, multi-skill remote job crawler and resume evaluation agent. It aggregates remote job postings, filters them based on keywords and high salary requirements ($150,000+/year and listed ranges), ranks them against your PDF resume using a local LLM via Ollama, and generates a beautiful interactive glassmorphic dashboard.

---

## Multi-Skill Architecture

The agent is built using the Google ADK framework with the following custom skills under `.agents/skills/`:
1. **`pdf-parsing`**: Extracts text from local PDF resumes using the `pypdf` library.
2. **`filtering-bad-jobs`**: Employs local LLM analysis to parse job descriptions, identify salary ranges (standardizing hourly/monthly rates to USD/year), and filter out listings that pay less than $150k or omit salary information.
3. **`ats-scoring`**: Scores qualified listings from 0 to 100 against your parsed resume and outputs structural AI Recruiter feedback.
4. **`jsearch-rapidapi`**: Queries high-volume web job postings using JSearch via RapidAPI.

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
Run the python script directly by passing parameters:
```bash
python job_matcher_agent.py --resume resume.pdf --titles "Python Developer, Software Engineer" --max-eval 10
```

* `--resume`: Absolute or relative path to your PDF resume.
* `--titles`: Comma-separated list of keywords/job titles to match.
* `--model`: Optional LiteLLM-compatible Ollama model name (default: `ollama_chat/llama3.1:latest`).
* `--max-eval`: Maximum number of qualified jobs to score using the local LLM.

---

## Scheduling the Agent (Windows 11 Task Scheduler)

To run the agent automatically every weekday at 1:00 AM:

### Step 1: Customize `run_scheduled.bat`
Open `run_scheduled.bat` in a text editor and update the paths and arguments to your liking:
```bat
@echo off
cd /d "%~dp0"
python job_matcher_agent.py --resume C:\path\to\your\resume.pdf --titles "Python Developer, Software Engineer, Data Scientist" --max-eval 10
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
