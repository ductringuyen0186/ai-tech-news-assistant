# Issue #29: Host LLM Backend Locally Using Ollama

> **Branch**: `feature/ollama-llm-integration-29`  
> **Status**: In Progress  
> **Priority**: High  
> **Labels**: feature

---

## 🎯 Goal

Serve LLaMA or Mistral models locally using Ollama for cost-effective inference with optional fallback to Claude API.

---

## ✅ Already Implemented

The codebase already has significant Ollama support:

### 1. **LLM Provider Architecture** (`backend/llm/providers.py`)
- ✅ Abstract `LLMProvider` base class
- ✅ `OllamaProvider` implementation with:
  - Connection checking (`is_available()`)
  - Model availability verification
  - Summarization with structured prompts
  - Keyword extraction
  - Error handling
- ✅ `ClaudeProvider` for fallback
- ✅ Proper async/await support

### 2. **Configuration** (`backend/src/core/config.py`)
- ✅ `LLMProvider` enum with Ollama support
- ✅ Ollama settings (host, model, timeout)
- ✅ Default provider configuration
- ✅ Environment variable support

### 3. **Service Layer** (`backend/src/services/summarization_service.py`)
- ✅ Provider factory pattern
- ✅ Fallback mechanism between providers

---

## 📝 Tasks to Complete

### Phase 1: Testing & Verification
- [ ] **Task 1.1**: Install Ollama locally
  ```bash
  # Windows (using PowerShell)
  # Download from https://ollama.com/download
  
  # Pull a model
  ollama pull llama3.2:1b  # Fast, lightweight
  ollama pull mistral      # Good quality
  ```

- [ ] **Task 1.2**: Test Ollama server
  ```bash
  # Start Ollama (usually auto-starts)
  ollama serve
  
  # Test with curl
  curl http://localhost:11434/api/tags
  ```

- [ ] **Task 1.3**: Verify OllamaProvider connection
  ```python
  # Create test script: backend/test_ollama.py
  import asyncio
  from llm.providers import OllamaProvider
  
  async def test_ollama():
      provider = OllamaProvider(model="llama3.2:1b")
      is_available = await provider.is_available()
      print(f"Ollama available: {is_available}")
      
      if is_available:
          result = await provider.summarize("Test article about AI...")
          print(f"Summary: {result['summary']}")
  
  asyncio.run(test_ollama())
  ```

### Phase 2: Integration
- [ ] **Task 2.1**: Update `.env.example` with Ollama configuration
  ```env
  # LLM Configuration
  DEFAULT_LLM_PROVIDER=ollama
  OLLAMA_BASE_URL=http://localhost:11434
  OLLAMA_MODEL=llama3.2:1b
  OLLAMA_TIMEOUT=60
  
  # Fallback to Claude (optional)
  ANTHROPIC_API_KEY=your_api_key_here
  ANTHROPIC_MODEL=claude-3-haiku-20240307
  ```

- [ ] **Task 2.2**: Test summarization endpoint with Ollama
  ```bash
  # Start backend
  cd backend
  python main.py
  
  # Test summarization
  curl -X POST http://localhost:8000/summarize \
    -H "Content-Type: application/json" \
    -d '{"text": "AI breakthrough article text..."}'
  ```

- [ ] **Task 2.3**: Implement provider fallback logic
  - Update summarization service to try Ollama first
  - Fall back to Claude if Ollama unavailable
  - Log which provider was used

### Phase 3: Documentation
- [ ] **Task 3.1**: Update README with Ollama setup instructions
  - Add "LLM Setup" section
  - Include Ollama installation steps
  - Document model selection (llama3.2:1b vs mistral)
  - Add troubleshooting guide

- [ ] **Task 3.2**: Create Ollama setup guide
  - Document in `docs/OLLAMA_SETUP.md`
  - Include Windows/Mac/Linux instructions
  - Model comparison table
  - Performance benchmarks

- [ ] **Task 3.3**: Update API documentation
  - Document LLM provider selection
  - Show example requests/responses
  - Explain fallback behavior

### Phase 4: Testing
- [ ] **Task 4.1**: Create integration tests
  ```python
  # tests/integration/test_ollama_integration.py
  @pytest.mark.integration
  async def test_ollama_summarization():
      """Test Ollama summarization with real model."""
      # Implementation
  ```

- [ ] **Task 4.2**: Add mock tests for CI/CD
  ```python
  # tests/unit/test_ollama_provider.py
  async def test_ollama_provider_mock():
      """Test OllamaProvider with mocked responses."""
      # Implementation
  ```

- [ ] **Task 4.3**: Performance testing
  - Benchmark summarization speed
  - Compare Ollama vs Claude performance
  - Test with different model sizes

### Phase 5: Optimization
- [ ] **Task 5.1**: Implement response caching
  - Cache LLM responses for identical inputs
  - Set appropriate TTL (time-to-live)
  - Use Redis or in-memory cache

- [ ] **Task 5.2**: Add model warm-up
  - Pre-load model on startup
  - Reduce first-request latency

- [ ] **Task 5.3**: Monitor resource usage
  - Track GPU/CPU usage
  - Monitor memory consumption
  - Log inference times

---

## 🔍 Current Code Analysis

### OllamaProvider Implementation Status

**Strengths:**
- ✅ Well-structured with proper error handling
- ✅ Async/await throughout
- ✅ Model availability checking
- ✅ Configurable via environment variables
- ✅ Proper logging

**Potential Improvements:**
- Consider adding retry logic for transient failures
- Add response streaming support (for longer summaries)
- Implement token counting and limits
- Add model performance metrics

---

## 🧪 Testing Strategy

### 1. **Manual Testing Checklist**
- [ ] Install Ollama and pull model
- [ ] Start Ollama server
- [ ] Test `/api/tags` endpoint
- [ ] Run `test_ollama.py` script
- [ ] Test summarization via API
- [ ] Test with various article lengths
- [ ] Verify fallback to Claude works

### 2. **Automated Testing**
- [ ] Unit tests for OllamaProvider
- [ ] Integration tests with real Ollama
- [ ] Mock tests for CI/CD
- [ ] Performance benchmarks

### 3. **Edge Cases to Test**
- [ ] Ollama not running
- [ ] Model not downloaded
- [ ] Network timeout
- [ ] Very long articles (token limits)
- [ ] Special characters in text
- [ ] Empty or malformed input

---

## 📊 Success Criteria

### Functional Requirements
- ✅ Ollama successfully serves local LLM
- ✅ Summarization endpoint works with Ollama
- ✅ Fallback to Claude when Ollama unavailable
- ✅ Configuration via environment variables
- ✅ Comprehensive documentation

### Performance Requirements
- Response time < 5 seconds for typical articles
- Support for concurrent requests
- Graceful degradation on failures

### Documentation Requirements
- Setup guide for all platforms
- API documentation updated
- Troubleshooting section
- Model selection guide

---

## 🚀 Deployment Considerations

### Local Development
- Ollama runs on developer machines
- No API costs during development
- Privacy-friendly (data stays local)

### Production Options
1. **Self-hosted Ollama**
   - Deploy on dedicated server with GPU
   - Use load balancer for scaling
   - Monitor resource usage

2. **Hybrid Approach**
   - Ollama for development/staging
   - Claude for production
   - Cost optimization based on usage

---

## 📖 Resources

### Ollama
- [Official Website](https://ollama.com/)
- [GitHub Repository](https://github.com/ollama/ollama)
- [Model Library](https://ollama.com/library)
- [API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)

### Models to Consider
- **llama3.2:1b** - Fast, lightweight (1.3GB)
- **llama3.2:3b** - Balanced (2.0GB)
- **mistral** - High quality (4.1GB)
- **llama3:8b** - Best quality (4.7GB)

### Alternative Providers
- **Anthropic Claude** - High quality, API-based
- **OpenAI GPT** - Industry standard
- **Hugging Face** - Open models via API

---

## 🎯 Next Steps

1. **Immediate**: Install Ollama and test locally
2. **Short-term**: Update documentation and add tests
3. **Long-term**: Optimize performance and add monitoring

---

## 📝 Notes

- Ollama provider code is already production-ready
- Main work is testing, documentation, and integration
- Consider creating a video demo for README
- May want to benchmark different models for performance comparison

---

**Last Updated**: October 6, 2025  
**Estimated Completion**: 1-2 days  
**Complexity**: Medium (mostly integration and testing)
