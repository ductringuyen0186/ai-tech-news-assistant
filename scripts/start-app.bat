@echo off
REM ===================================================================
REM AI Tech News Assistant - Windows Startup Script
REM Intelligently starts backend and frontend with dependency checking
REM ===================================================================

echo.
echo ========================================
echo  AI Tech News Assistant - Local Startup
echo ========================================
echo.

REM Color setup for better output
setlocal enabledelayedexpansion

REM Parse command line arguments
set "WITH_AI=true"
set "SKIP_DEPS=false"

:parse_args
if "%1"=="" goto :done_args
if /i "%1"=="--no-ai" set "WITH_AI=false"
if /i "%1"=="--skip-deps" set "SKIP_DEPS=true"
shift
goto :parse_args
:done_args

REM Display configuration
echo Configuration:
echo - AI Features: %WITH_AI%
echo - Skip Dependency Check: %SKIP_DEPS%
echo.

REM ===================================================================
REM STEP 1: Check System Prerequisites
REM ===================================================================
echo [1/7] Checking system prerequisites...

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
        echo [ERROR] Python is not installed or not in PATH
        echo Please install Python 3.9+ from https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)
echo   - Node.js: OK

REM Check npm
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm is not installed
    echo Please ensure Node.js installation includes npm
    pause
    exit /b 1
)
echo   - npm: OK

REM Check Ollama if AI is enabled
if "%WITH_AI%"=="true" (
    echo.
    echo Checking for Ollama AI engine...
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if %errorlevel% neq 0 (
        echo [WARNING] Ollama is not running or not installed
        echo.
        echo AI features will be disabled. To enable:
        echo 1. Install Ollama from https://ollama.com
        echo 2. Run: ollama pull llama3.2:1b
        echo 3. Restart this script
        echo.
        set "WITH_AI=false"
        timeout /t 5 /nobreak >nul
    ) else (
        echo   - Ollama: OK
    )
)

echo.

REM ===================================================================
REM STEP 2: Setup Backend
REM ===================================================================
echo [2/7] Setting up backend...
cd backend

REM Check if virtual environment exists
if not exist "venv\" (
    echo   Creating Python virtual environment...
    %PYTHON_CMD% -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        cd ..
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo   Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    cd ..
    pause
    exit /b 1
)

REM Check if dependencies need to be installed
if "%SKIP_DEPS%"=="false" (
    echo   Checking Python dependencies...

    REM Check if requirements are already installed
    %PYTHON_CMD% -c "import fastapi" >nul 2>&1
    if %errorlevel% neq 0 (
        echo   Installing Python dependencies (this may take a few minutes)...
        pip install -q -r requirements.txt
        if %errorlevel% neq 0 (
            echo [ERROR] Failed to install Python dependencies
            cd ..
            pause
            exit /b 1
        )
        echo   - Dependencies installed successfully
    ) else (
        echo   - Dependencies already installed (checking for updates...)
        pip install -q -r requirements.txt --upgrade
    )
) else (
    echo   - Skipping dependency check
)

REM Setup environment file if it doesn't exist
if not exist ".env" (
    echo   Creating .env file from template...
    copy .env.example .env >nul

    echo.
    echo [IMPORTANT] Generated .env file with default settings
    echo Please edit backend\.env and set a secure SECRET_KEY
    echo.
    echo Run this to generate a secure key:
    echo %PYTHON_CMD% -c "import secrets; print(secrets.token_hex(32))"
    echo.
    timeout /t 3 /nobreak >nul
)

REM Update AI settings in .env based on flag
if "%WITH_AI%"=="false" (
    echo   Configuring for non-AI mode...
)

echo   Backend setup complete!
cd ..
echo.

REM ===================================================================
REM STEP 3: Setup Frontend
REM ===================================================================
echo [3/7] Setting up frontend...
cd frontend

REM Check if node_modules exists
if "%SKIP_DEPS%"=="false" (
    if not exist "node_modules\" (
        echo   Installing npm dependencies (this may take a few minutes)...
        npm install
        if %errorlevel% neq 0 (
            echo [ERROR] Failed to install npm dependencies
            cd ..
            pause
            exit /b 1
        )
    ) else (
        echo   - Dependencies already installed
    )
) else (
    echo   - Skipping dependency check
)

echo   Frontend setup complete!
cd ..
echo.

REM ===================================================================
REM STEP 4: Initialize Database
REM ===================================================================
echo [4/7] Checking database...
cd backend
call venv\Scripts\activate.bat

if not exist "news_production.db" (
    echo   Database not found, will be created on first run...
) else (
    echo   Database exists
)

cd ..
echo.

REM ===================================================================
REM STEP 5: Display Startup Information
REM ===================================================================
echo [5/7] Starting application services...
echo.
echo ========================================
echo  Services Starting
echo ========================================
echo.
echo Backend API:     http://localhost:8001
echo Frontend:        http://localhost:5173
echo API Docs:        http://localhost:8001/docs
echo Health Check:    http://localhost:8001/health
echo.
if "%WITH_AI%"=="true" (
    echo AI Features:     ENABLED
) else (
    echo AI Features:     DISABLED
)
echo.
echo Press Ctrl+C in each window to stop the services
echo.
timeout /t 3 /nobreak >nul

REM ===================================================================
REM STEP 6: Start Backend in New Window
REM ===================================================================
echo [6/7] Starting backend server...
start "AI News Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && echo Starting backend server... && py production_main.py"

REM Wait a bit for backend to start
timeout /t 3 /nobreak >nul

REM ===================================================================
REM STEP 7: Start Frontend in New Window
REM ===================================================================
echo [7/7] Starting frontend server...
start "AI News Frontend" cmd /k "cd /d %~dp0frontend && echo Starting frontend server... && npm run dev"

echo.
echo ========================================
echo  Startup Complete!
echo ========================================
echo.
echo Both services are starting in separate windows.
echo.
echo Next Steps:
echo 1. Wait 10-15 seconds for services to start
echo 2. Open http://localhost:5173 in your browser
echo 3. Check http://localhost:8001/docs for API documentation
echo.
if "%WITH_AI%"=="false" (
    echo Note: AI features are disabled. Articles will use simple summarization.
    echo To enable AI, install Ollama and run: start-app.bat
    echo.
)
echo To stop: Close the backend and frontend windows
echo.
echo Logs will appear in their respective windows.
echo.
pause
