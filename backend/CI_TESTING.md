# CI/CD Testing Strategy

## 🎯 Overview

This document explains how we handle testing in CI/CD environments where external dependencies (like Ollama) are not available.

## 🏗️ Testing Approach

### 1. **Mock External Dependencies**

We use mocked versions of external services in CI:

```python
# Example: Mocking OllamaProvider
with patch('httpx.AsyncClient') as mock_client:
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "Test summary"}
    
    mock_client.return_value.__aenter__.return_value.post = AsyncMock(
        return_value=mock_response
    )
    
    result = await provider.summarize("Test article")
```

### 2. **Environment Variables for CI**

Set these environment variables in CI to enable graceful degradation:

```bash
export OLLAMA_HOST="http://mock-ollama:11434"
export USE_MOCK_DATA="true"
export ANTHROPIC_API_KEY="mock-key-for-ci"
```

### 3. **Test Files**

- **`test_ci.py`** - Unit tests with mocked dependencies (runs in CI)
- **`test_ollama_integration.py`** - Integration tests (requires real Ollama, runs locally only)

## 🧪 Running Tests

### Locally (with Ollama)

```bash
# Run integration tests with real Ollama
cd backend
python test_ollama_integration.py
```

### CI/CD (mocked)

```bash
# Run unit tests with mocked dependencies
cd backend
pytest test_ci.py -v
```

### Both

```bash
# Run all tests
cd backend
pytest -v
```

## 📋 Test Coverage

### Unit Tests (CI-friendly)

- ✅ App imports and initialization
- ✅ Configuration loading
- ✅ LLM provider availability checks (mocked)
- ✅ Summarization logic (mocked)
- ✅ Error handling for empty input
- ✅ API endpoints (basic)
- ✅ Utility functions

### Integration Tests (Local only)

- ✅ Real Ollama connection
- ✅ Actual LLM inference
- ✅ Model availability verification
- ✅ Performance benchmarks
- ✅ Provider fallback mechanisms
- ✅ Edge case handling with real data

## 🚀 CI/CD Workflow

Our GitHub Actions workflow:

1. **Install Dependencies** - Installs Python packages + pytest + pytest-asyncio + pytest-mock
2. **Set Mock Environment** - Configures environment variables for CI
3. **Run Unit Tests** - Executes `test_ci.py` with mocked dependencies
4. **Fallback Test** - If pytest fails, runs basic import test
5. **Code Quality** - Runs ruff (linting), mypy (type checking)

## 🔍 Why This Approach?

### ✅ Advantages

1. **Fast CI Builds** - No need to install Ollama in CI (saves ~5-10 minutes)
2. **Reliable** - Tests don't depend on external services
3. **Cost-Effective** - No API calls in CI
4. **Flexible** - Can test error scenarios easily with mocks
5. **Portable** - Works in any CI/CD environment

### ⚠️ Considerations

1. **Integration tests still needed** - Run locally before pushing
2. **Mock accuracy** - Ensure mocks match real API behavior
3. **Documentation** - Keep this guide updated

## 🐳 Docker Testing (Optional)

To test with Ollama in Docker:

```yaml
# docker-compose.test.yml
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
  
  backend:
    build: ./backend
    environment:
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - ollama

volumes:
  ollama_data:
```

```bash
# Run integration tests in Docker
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📊 Test Matrix

| Test Type | Environment | Dependencies | Speed | When to Run |
|-----------|------------|--------------|-------|-------------|
| Unit Tests | CI/CD | Mocked | Fast (< 30s) | Every push/PR |
| Integration Tests | Local | Real Ollama | Slow (1-2 min) | Before merge |
| E2E Tests | Staging | Full stack | Very slow | Pre-release |

## 🔧 Troubleshooting

### Issue: Tests pass locally but fail in CI

**Solution**: Check environment variables and ensure mocks are used

```bash
# Verify mock environment in CI logs
echo $OLLAMA_HOST  # Should be http://mock-ollama:11434
echo $USE_MOCK_DATA  # Should be true
```

### Issue: Import errors in CI

**Solution**: Ensure all dependencies are in `requirements.txt`

```bash
# Check dependencies
pip freeze | grep -E "pytest|httpx|fastapi"
```

### Issue: Async tests not running

**Solution**: Install pytest-asyncio

```bash
pip install pytest-asyncio
```

Add to `pytest.ini` or `pyproject.toml`:

```ini
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

## 📚 Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [GitHub Actions](https://docs.github.com/en/actions)

---

**Last Updated**: October 6, 2025
