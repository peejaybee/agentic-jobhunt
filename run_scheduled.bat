@echo off
:: Navigate to the directory containing this script
cd /d "%~dp0"

echo Running ATS Job Matcher in Scheduled Mode...
python job_matcher_agent.py --resume resume.pdf --titles "Python Developer, Software Engineer, Machine Learning" --max-eval 10
echo Run completed at %date% %time%
