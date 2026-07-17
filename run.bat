@echo off
title ATS Job Matcher & Scorer Dashboard
cls
echo ==========================================================
echo               ATS JOB MATCHER AGENT (OLLAMA + ADK)
echo ==========================================================
echo.
echo Make sure Ollama is running on your machine.
echo.

set /p RESUME_PATH="Enter the path to your PDF resume (e.g. C:\Users\YourName\Documents\resume.pdf): "
if not exist "%RESUME_PATH%" (
    echo [ERROR] Resume file does not exist at: "%RESUME_PATH%"
    pause
    exit /b 1
)

set /p JOB_TITLES="Enter comma-separated job titles to search (e.g. Python Developer, Django Engineer): "

echo Select the Ollama model to use:
echo 1) qwen2.5-coder:7b (Default)
echo 2) llama3.1:latest
echo 3) Custom name
set /p MODEL_CHOICE="Enter option (1-3): "

set OLLAMA_MODEL=ollama_chat/qwen2.5-coder:7b
if "%MODEL_CHOICE%"=="2" set OLLAMA_MODEL=ollama_chat/llama3.1:latest
if "%MODEL_CHOICE%"=="3" (
    set /p CUSTOM_MODEL="Enter custom Ollama model name (e.g. deepseek-r1:8b): "
    set OLLAMA_MODEL=ollama_chat/%CUSTOM_MODEL%
)

echo.
echo ==========================================================
echo Starting Remote Job Search and Resume Evaluation...
echo Model:  %OLLAMA_MODEL%
echo Resume: %RESUME_PATH%
echo Titles: %JOB_TITLES%
echo ==========================================================
echo.

python job_matcher_agent.py --resume "%RESUME_PATH%" --titles "%JOB_TITLES%" --model "%OLLAMA_MODEL%"

if %ERRORLEVEL% equ 0 (
    echo.
    echo Job matching completed successfully! The dashboard should open in your browser.
) else (
    echo.
    echo [ERROR] An error occurred during matching pipeline.
)
echo.
pause
