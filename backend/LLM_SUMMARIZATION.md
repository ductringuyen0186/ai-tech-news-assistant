# LLM Summarization Feature

This document describes the newly implemented LLM summarization feature for the AI Tech News Assistant.

## Overview

The summarization feature provides AI-powered article summarization using multiple LLM providers:

- **Ollama**: Local LLM inference (free, private, requires local setup)
- **Claude**: Anthropic's Claude API (paid, cloud-based, high quality)
- **Auto**: Automatically selects the best available provider

## API Endpoints

### POST `/summarize`

Summarize an article using AI/LLM.

**Parameters:**
- `article_id` (optional): ID of article in database
- `url` (optional): URL to fetch and summarize  
- `text` (optional): Direct text to summarize
- `provider` (default: "auto"): LLM provider to use ("auto", "ollama", "claude")

**Example Requests:**

```bash
# Summarize text directly
curl -X POST "http://localhost:8000/summarize?provider=auto" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "text=Your article text here..."

# Summarize from URL
curl -X POST "http://localhost:8000/summarize?provider=ollama" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "url=https://techcrunch.com/some-article"

# Summarize existing article
curl -X POST "http://localhost:8000/summarize?article_id=123&provider=claude"
```

**Response Example:**
```json
{
  "summary": "OpenAI released GPT-4 Turbo with a 128K context window...",
  "keywords": ["openai", "gpt-4", "turbo", "context", "window"],
  "title": "OpenAI Announces GPT-4 Turbo",
  "provider": "ollama",
  "model": "llama3.2",
  "confidence": 0.8,
  "original_length": 2547,
  "summary_length": 324,
  "compression_ratio": 0.127,
  "source": "url",
  "url": "https://example.com/article"
}
```

### GET `/summarize/status`

Get status of available LLM providers.

**Response Example:**
```json
{
  "message": "Summarization service status",
  "providers": {
    "ollama": {
      "available": true,
      "type": "ollama",
      "model": "llama3.2"
    },
    "claude": {
      "available": false,
      "error": "API key not configured"
    }
  },
  "available_count": 1,
  "default_provider": "auto"
}
```

## Setup Instructions

### Option 1: Ollama (Local LLM)

1. **Install Ollama:**
   - Download from: https://ollama.ai/
   - Follow installation instructions for your OS

2. **Pull a model:**
   ```bash
   ollama pull llama3.2
   # or other models: mistral, codellama, etc.
   ```

3. **Start Ollama service:**
   ```bash
   ollama serve
   ```

4. **Configure in .env:**
   ```env
   OLLAMA_HOST=http://localhost:11434
   OLLAMA_MODEL=llama3.2
   ```

### Option 2: Claude API

1. **Get API key:**
   - Sign up at: https://console.anthropic.com/
   - Generate an API key

2. **Configure in .env:**
   ```env
   ANTHROPIC_API_KEY=your_api_key_here
   ```

### Option 3: Both Providers

Configure both for automatic fallback and provider choice.

## Testing

### Method 1: PowerShell Script
```powershell
.\test_api.ps1
```

### Method 2: Individual Tests
```bash
# Check provider status
curl http://localhost:8000/summarize/status

# Test summarization
curl -X POST "http://localhost:8000/summarize?provider=auto" \
     -d "text=Sample article text for testing..."
```

### Method 3: Python Test Script
```bash
python test_summarization.py
```

## Architecture

### Core Components

1. **ArticleSummarizer**: Main orchestrator class
2. **LLMProvider**: Abstract base class for providers
3. **OllamaProvider**: Local Ollama integration
4. **ClaudeProvider**: Anthropic Claude integration

### Provider Selection Logic

1. **Auto mode**: Prefers Claude (higher quality) → Ollama (local/free)
2. **Specific provider**: Uses requested provider or fails
3. **Fallback**: Auto mode tries other providers if primary fails

### Error Handling

- Provider unavailability
- Network timeouts
- Invalid content
- API rate limits
- Model errors

## Configuration Options

### Environment Variables

```env
# Ollama Settings
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Claude Settings  
ANTHROPIC_API_KEY=your_key_here

# General LLM Settings
LOG_LEVEL=INFO
```

### Supported Models

**Ollama Models:**
- `llama3.2` (recommended)
- `llama2`
- `mistral`
- `codellama`
- `vicuna`

**Claude Models:**
- `claude-3-haiku-20240307` (default, fast)
- `claude-3-sonnet-20240229` (balanced)
- `claude-3-opus-20240229` (highest quality)

## Performance Notes

- **Ollama**: 5-30 seconds depending on model and text length
- **Claude**: 2-10 seconds, rate limited by API
- **Text limits**: 4000 chars for Ollama, 8000 for Claude
- **Context preservation**: Maintains article structure and key details

## Troubleshooting

### Common Issues

1. **"No LLM providers available"**
   - Install and start Ollama, or configure Claude API key
   - Check provider status endpoint

2. **"Ollama request failed"**
   - Ensure Ollama is running: `ollama serve`
   - Check if model is pulled: `ollama list`

3. **"Claude API key not configured"**
   - Set ANTHROPIC_API_KEY environment variable
   - Verify API key is valid

4. **"Text too short to summarize"**
   - Minimum 50 characters required
   - Check article content extraction

### Debug Commands

```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Test Ollama directly
curl -X POST http://localhost:11434/api/generate \
     -d '{"model":"llama3.2","prompt":"Summarize: AI news...","stream":false}'

# Check logs
tail -f logs/app.log
```

## Future Enhancements

- [ ] Response caching
- [ ] Rate limiting
- [ ] Batch summarization
- [ ] Custom prompt templates
- [ ] Quality scoring
- [ ] Multi-language support
- [ ] OpenAI GPT integration
- [ ] Hugging Face model support
