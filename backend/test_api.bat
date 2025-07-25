@echo off
REM Test Script for AI Tech News Assistant API
REM ============================================
REM
REM This script tests the new LLM summarization endpoints.
REM Run this after starting the FastAPI server with: uvicorn main:app --reload
REM

echo Testing AI Tech News Assistant API...
echo.

REM Test 1: API Info
echo 1. Testing API info endpoint...
curl -X GET "http://localhost:8000/" -H "accept: application/json"
echo.
echo.

REM Test 2: Health Check
echo 2. Testing health check...
curl -X GET "http://localhost:8000/ping" -H "accept: application/json"
echo.
echo.

REM Test 3: Summarization Status
echo 3. Testing summarization status...
curl -X GET "http://localhost:8000/summarize/status" -H "accept: application/json"
echo.
echo.

REM Test 4: News Stats
echo 4. Testing news statistics...
curl -X GET "http://localhost:8000/news/stats" -H "accept: application/json"
echo.
echo.

REM Test 5: Summarize with text (if providers are available)
echo 5. Testing summarization with sample text...
curl -X POST "http://localhost:8000/summarize?provider=auto" ^
     -H "accept: application/json" ^
     -H "Content-Type: application/x-www-form-urlencoded" ^
     -d "text=OpenAI has released GPT-4 Turbo, a new language model with enhanced capabilities including a 128,000 token context window. This represents a significant improvement over previous versions, allowing the model to process much longer documents while maintaining coherence. The new model also features updated training data and improved performance at a lower cost."
echo.
echo.

REM Test 6: Summarize with URL (example)
echo 6. Testing summarization with URL...
curl -X POST "http://localhost:8000/summarize?provider=auto" ^
     -H "accept: application/json" ^
     -H "Content-Type: application/x-www-form-urlencoded" ^
     -d "url=https://techcrunch.com/2023/11/06/openai-devday-gpt-4-turbo/"
echo.
echo.

echo Testing complete!
pause
