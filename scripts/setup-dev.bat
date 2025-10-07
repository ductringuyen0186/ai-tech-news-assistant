@echo off
REM ===================================================================
REM Development Environment Setup - First Time Setup Only
REM Run this once before using start-app.bat
REM ===================================================================

echo.
echo ========================================
echo  AI Tech News - First Time Setup
echo ========================================
echo.

REM Check Python (try py first, then python)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    echo   - Python: OK
) else (
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=python
        echo   - Python: OK
    ) else (
        echo [ERROR] Python not found. Install from https://www.python.org/
        pause
        exit /b 1
    )
)

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Install from https://nodejs.org/
    pause
    exit /b 1
)

echo [1/4] Setting up backend...
cd backend

REM Create venv
if not exist "venv\" (
    %PYTHON_CMD% -m venv venv
)
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing Python packages...
pip install -r requirements.txt

REM Setup .env
if not exist ".env" (
    copy .env.example .env
    echo.
    echo [ACTION REQUIRED] Please edit backend\.env and set:
    echo   1. SECRET_KEY to a secure random string
    echo   2. Other configuration as needed
    echo.
)

cd ..

echo.
echo [2/4] Setting up frontend...
cd frontend

REM Install npm packages
echo Installing npm packages...
npm install

cd ..

echo.
echo [3/4] Creating logs directory...
if not exist "logs\" mkdir logs

echo.
echo [4/4] Checking Ollama (optional)...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Ollama not detected. AI features will be disabled.
    echo To enable AI:
    echo   1. Install from https://ollama.com
    echo   2. Run: ollama pull llama3.2:1b
) else (
    echo Ollama detected and running!
)

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Edit backend\.env if needed
echo   2. Run: start-app.bat
echo.
pause
