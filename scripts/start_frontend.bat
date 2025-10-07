@echo off
echo 🎨 Starting Frontend Server on Port 5173
echo =====================================
cd /d "c:\Users\Tri\OneDrive\Desktop\Portfolio\ai-tech-news-assistant\frontend"
echo Current directory: %CD%
echo Installing dependencies...
call npm install
echo Starting development server...
call npm run dev
pause
