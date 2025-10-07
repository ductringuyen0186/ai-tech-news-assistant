@echo off
echo 🚀 Starting AI Tech News Assistant (Production Version)
echo =====================================================

cd /d "%~dp0backend"

echo 📦 Installing/updating dependencies...
pip install -r requirements.txt

echo 🔧 Starting production server...
echo 📖 API docs will be available at: http://127.0.0.1:8000/docs
echo 🏥 Health check at: http://127.0.0.1:8000/health
echo 📰 Articles API at: http://127.0.0.1:8000/articles
echo.

python production_main.py