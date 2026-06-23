@echo off
:: Navigate to the directory containing this script
cd /d "%~dp0"

echo Running ATS Job Matcher in Scheduled Mode...
python job_matcher_agent.py --resume resume.pdf --titles "Machine Learning, AI, Data Scientist" --max-eval 10 --min-salary 150000 --concurrency 3 --desc-limit 10000
echo Run completed at %date% %time%
