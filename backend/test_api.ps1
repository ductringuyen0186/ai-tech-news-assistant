# Test Script for AI Tech News Assistant API
# ============================================
#
# This PowerShell script tests the new LLM summarization endpoints.
# Run this after starting the FastAPI server with: uvicorn main:app --reload
#

Write-Host "Testing AI Tech News Assistant API..." -ForegroundColor Green
Write-Host ""

# Test 1: API Info
Write-Host "1. Testing API info endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/" -Method GET
    $response | ConvertTo-Json -Depth 3
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Health Check
Write-Host "2. Testing health check..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/ping" -Method GET
    $response | ConvertTo-Json
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Summarization Status
Write-Host "3. Testing summarization status..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/summarize/status" -Method GET
    $response | ConvertTo-Json -Depth 4
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 4: News Stats
Write-Host "4. Testing news statistics..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/news/stats" -Method GET
    $response | ConvertTo-Json -Depth 3
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 5: Summarize with text
Write-Host "5. Testing summarization with sample text..." -ForegroundColor Yellow
try {
    $body = @{
        text = "OpenAI has released GPT-4 Turbo, a new language model with enhanced capabilities including a 128,000 token context window. This represents a significant improvement over previous versions, allowing the model to process much longer documents while maintaining coherence. The new model also features updated training data and improved performance at a lower cost."
        provider = "auto"
    }
    
    $response = Invoke-RestMethod -Uri "http://localhost:8000/summarize" -Method POST -Body $body -ContentType "application/x-www-form-urlencoded"
    $response | ConvertTo-Json -Depth 4
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "Testing complete!" -ForegroundColor Green
Write-Host "Note: Some tests may fail if LLM providers (Ollama/Claude) are not configured." -ForegroundColor Cyan
