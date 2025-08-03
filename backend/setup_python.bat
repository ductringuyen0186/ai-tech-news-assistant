@echo off
echo 🐍 AI Tech News Assistant - Python Setup Script
echo ================================================

echo.
echo Checking Python installation...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Python is not installed or not in PATH
        echo.
        echo Please install Python from:
        echo 🔗 https://www.python.org/downloads/windows/
        echo.
        echo Make sure to check "Add Python to PATH" during installation!
        pause
        exit /b 1
    )
    set PYTHON_CMD=python
) else (
    set PYTHON_CMD=py
)

echo ✅ Python is installed
%PYTHON_CMD% --version

echo.
echo Creating virtual environment...
%PYTHON_CMD% -m venv venv

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install --upgrade pip
pip install fastapi uvicorn pydantic httpx pytest beautifulsoup4 feedparser

echo.
echo ✅ Setup complete!
echo.
echo To run the application:
echo 1. cd C:\Users\Tri\OneDrive\Desktop\Portfolio\ai-tech-news-assistant\backend
echo 2. venv\Scripts\activate
echo 3. %PYTHON_CMD% -m uvicorn src.main:app --reload
echo.
echo Then visit: http://localhost:8000/docs
echo.
pause
