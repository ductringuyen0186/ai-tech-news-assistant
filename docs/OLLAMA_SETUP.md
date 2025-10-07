# Ollama LLM Integration Guide

## 📋 Overview

This project uses **Ollama** to run Large Language Models (LLMs) locally for AI-powered article summarization. Ollama provides cost-effective, privacy-friendly inference without requiring cloud API keys.

### Benefits

- **✅ Free**: No API costs for LLM inference
- **🔒 Privacy**: Data stays on your machine
- **⚡ Fast**: Local inference with GPU acceleration
- **🔄 Offline**: Works without internet connection
- **🎛️ Control**: Choose your preferred models

---

## 🚀 Quick Start

### 1. Install Ollama

**Windows**:
1. Download from [ollama.com/download](https://ollama.com/download)
2. Run the installer
3. Ollama will start automatically

**Mac**:
```bash
# Using Homebrew
brew install ollama

# Or download from ollama.com
```

**Linux**:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Pull a Model

Choose a model based on your needs:

```bash
# Fast and lightweight (1.3GB) - Recommended for development
ollama pull llama3.2:1b

# Balanced quality and speed (2.0GB)
ollama pull llama3.2:3b

# Higher quality (4.1GB)
ollama pull mistral

# Best quality (4.7GB)
ollama pull llama3:8b
```

### 3. Verify Installation

```bash
# Check Ollama version
ollama --version

# List installed models
ollama list

# Test the server
curl http://localhost:11434/api/tags
```

### 4. Configure Environment

Update your `.env` file:

```env
# LLM Configuration
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
OLLAMA_TIMEOUT=60

# Optional: Fallback to Claude if Ollama unavailable
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_MODEL=claude-3-haiku-20240307
```

### 5. Test Integration

Run the integration test suite:

```bash
cd backend
python test_ollama_integration.py
```

Expected output:
```
🚀 OLLAMA INTEGRATION TEST SUITE
======================================================================
✅ AVAILABILITY: PASSED
✅ SUMMARIZATION: PASSED  
✅ FALLBACK: PASSED
✅ EDGE_CASES: PASSED

🎉 All tests passed! Ollama integration is working correctly.
```

---

## 📊 Model Comparison

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| **llama3.2:1b** | 1.3GB | ⚡⚡⚡ | ⭐⭐ | Development, testing |
| **llama3.2:3b** | 2.0GB | ⚡⚡ | ⭐⭐⭐ | Production (balanced) |
| **mistral** | 4.1GB | ⚡ | ⭐⭐⭐⭐ | High-quality summaries |
| **llama3:8b** | 4.7GB | ⚡ | ⭐⭐⭐⭐⭐ | Best quality |

### Benchmark Results

Tested on: Intel i7 / 16GB RAM / No GPU

| Model | Avg. Response Time | Quality Score | Memory Usage |
|-------|-------------------|---------------|--------------|
| llama3.2:1b | ~1.0s | Good | ~2GB |
| llama3.2:3b | ~2.5s | Better | ~3GB |
| mistral | ~4.0s | Excellent | ~5GB |
| llama3:8b | ~6.0s | Outstanding | ~8GB |

---

## 🏗️ Architecture

### Provider Abstraction

The project uses a provider abstraction layer that supports multiple LLM backends:

```python
# backend/llm/providers.py

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def summarize(self, text: str, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        pass

class OllamaProvider(LLMProvider):
    """Local LLM inference via Ollama."""
    # Implementation...

class ClaudeProvider(LLMProvider):
    """Cloud LLM via Anthropic Claude API."""
    # Implementation...
```

### Fallback Mechanism

The system automatically falls back to Claude if Ollama is unavailable:

```python
# 1. Try Ollama first
ollama = OllamaProvider(model="llama3.2:1b")
if await ollama.is_available():
    result = await ollama.summarize(text)
else:
    # 2. Fall back to Claude
    claude = ClaudeProvider(api_key=ANTHROPIC_API_KEY)
    result = await claude.summarize(text)
```

### API Integration

Summarization endpoint automatically uses the configured provider:

```bash
# POST /summarize
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your article content here..."
  }'

# Response
{
  "success": true,
  "summary": "A concise summary of the article...",
  "keywords": ["AI", "machine", "learning", "model", "breakthrough"],
  "model": "llama3.2:1b",
  "provider": "ollama",
  "confidence": 0.8
}
```

---

## 🔧 Advanced Configuration

### GPU Acceleration

Ollama automatically uses GPU if available:

```bash
# Check GPU support
ollama run llama3.2:1b --verbose
```

**NVIDIA GPU (CUDA)**:
- Ollama automatically detects CUDA
- Significantly faster inference
- Supports larger models

**AMD GPU (ROCm)**:
- Supported on Linux
- Configure ROCm drivers

**Apple Silicon (Metal)**:
- Native support on M1/M2/M3 Macs
- Excellent performance

### Custom Model Parameters

Override default parameters:

```python
provider = OllamaProvider(
    base_url="http://localhost:11434",
    model="llama3.2:1b",
    timeout=120  # Longer timeout for large articles
)

result = await provider.summarize(
    text=article_content,
    temperature=0.5,  # More creative (0.0-1.0)
    max_tokens=300,   # Longer summaries
    top_p=0.95        # Nucleus sampling
)
```

### Multiple Ollama Instances

Run Ollama on different ports for load balancing:

```bash
# Terminal 1: Default instance
ollama serve

# Terminal 2: Second instance on port 11435
OLLAMA_HOST=0.0.0.0:11435 ollama serve
```

Then configure multiple providers:

```python
provider1 = OllamaProvider(base_url="http://localhost:11434")
provider2 = OllamaProvider(base_url="http://localhost:11435")
```

---

## 🐛 Troubleshooting

### Issue: "Ollama not found"

**Solution**:
```bash
# Windows: Check if Ollama is in PATH
where ollama

# Mac/Linux: Check installation
which ollama

# Reinstall if needed
# Download from ollama.com/download
```

### Issue: "Model not found"

**Solution**:
```bash
# List installed models
ollama list

# Pull the required model
ollama pull llama3.2:1b

# Verify it's available
ollama list
```

### Issue: "Connection refused"

**Solution**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start manually
ollama serve

# Check if port is in use
# Windows
netstat -ano | findstr :11434

# Mac/Linux
lsof -i :11434
```

### Issue: "Slow inference"

**Solutions**:
1. **Use smaller model**:
   ```bash
   ollama pull llama3.2:1b  # Instead of llama3:8b
   ```

2. **Enable GPU**:
   - Install NVIDIA drivers + CUDA toolkit
   - Ollama will automatically use GPU

3. **Increase memory**:
   ```bash
   # Set environment variable (MB)
   export OLLAMA_MAX_LOADED_MODELS=2048
   ```

4. **Reduce context length**:
   ```python
   # Truncate long articles
   text = article_content[:4000]
   ```

### Issue: "Out of memory"

**Solutions**:
1. Use smaller model (llama3.2:1b)
2. Reduce max_tokens parameter
3. Close other applications
4. Restart Ollama service

### Issue: "Test failures"

**Check**:
1. Ollama service running: `ollama serve`
2. Model downloaded: `ollama list`
3. Correct model name in `.env`
4. API accessible: `curl http://localhost:11434/api/tags`

---

## 📝 API Reference

### OllamaProvider

```python
class OllamaProvider(LLMProvider):
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama2",
        timeout: int = 60
    )
```

**Parameters**:
- `base_url`: Ollama server URL
- `model`: Model name (must be pulled first)
- `timeout`: Request timeout in seconds

**Methods**:

#### `is_available() -> bool`

Check if Ollama server is running and model is available.

```python
provider = OllamaProvider(model="llama3.2:1b")
is_ready = await provider.is_available()
```

#### `summarize(text: str, **kwargs) -> Dict[str, Any]`

Summarize article text.

```python
result = await provider.summarize(
    text="Article content...",
    max_length=200,
    temperature=0.3
)

# Returns:
{
    "success": True,
    "summary": "Concise summary...",
    "keywords": ["keyword1", "keyword2", ...],
    "model": "llama3.2:1b",
    "provider": "ollama",
    "confidence": 0.8
}
```

---

## 🔬 Testing

### Run Integration Tests

```bash
cd backend
python test_ollama_integration.py
```

### Test Coverage

- ✅ Server availability checking
- ✅ Model availability verification
- ✅ Article summarization (3 samples)
- ✅ Provider fallback mechanism
- ✅ Edge cases (empty, short, long, special chars)
- ✅ Error handling
- ✅ Performance benchmarks

### Manual Testing

```bash
# Test Ollama API directly
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "prompt": "Summarize: AI breakthrough in language models...",
    "stream": false
  }'

# Test through FastAPI
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "AI researchers have announced..."
  }'
```

---

## 🚀 Performance Optimization

### 1. Model Caching

Models are cached in memory after first load:
```bash
# Pre-load model
ollama run llama3.2:1b "test"
```

### 2. Batch Processing

Process multiple articles efficiently:

```python
async def summarize_batch(articles: List[str]) -> List[Dict]:
    provider = OllamaProvider()
    tasks = [provider.summarize(text) for text in articles]
    return await asyncio.gather(*tasks)
```

### 3. Response Caching

Cache summaries to avoid reprocessing:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_summary(article_hash: str) -> str:
    # Return cached summary if available
    pass
```

### 4. Load Balancing

Distribute load across multiple Ollama instances:

```python
providers = [
    OllamaProvider("http://localhost:11434"),
    OllamaProvider("http://localhost:11435"),
]

# Round-robin selection
provider = providers[request_count % len(providers)]
```

---

## 📚 Additional Resources

- [Ollama GitHub](https://github.com/ollama/ollama)
- [Ollama Model Library](https://ollama.com/library)
- [Ollama API Docs](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Llama 3.2 Announcement](https://ai.meta.com/blog/llama-3-2/)
- [Mistral AI](https://mistral.ai/)

---

## 🤝 Contributing

Found an issue or want to improve Ollama integration? Please:

1. Check [GitHub Issues](../../issues)
2. Create a new issue with details
3. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License.

---

**Last Updated**: October 6, 2025
