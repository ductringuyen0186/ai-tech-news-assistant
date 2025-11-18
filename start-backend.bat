@echo off
echo Starting backend server...
cd /d "%~dp0backend"
set DATABASE_URL=postgresql://ai_tech_news_user:eGofnVxiV295g4BptRLLUgQs8G7k5dQi@dpg-d4dqttq4d50c73biqh10-a.oregon-postgres.render.com/ai_tech_news
py -m uvicorn main:app --port 8000
