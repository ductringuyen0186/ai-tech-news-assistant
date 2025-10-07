# Test Automation Framework Guide

## 📚 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Test Categories](#test-categories)
- [Running Tests](#running-tests)
- [Test Markers](#test-markers)
- [Coverage Reports](#coverage-reports)
- [CI/CD Integration](#cicd-integration)
- [Writing Tests](#writing-tests)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This test automation framework provides a comprehensive testing solution with:

✅ **Automated test discovery** - No more manual test selection  
✅ **Multiple test categories** - Unit, Integration, E2E, Smoke tests  
✅ **Coverage reporting** - See what's tested and what's not  
✅ **CI/CD ready** - Works seamlessly in GitHub Actions  
✅ **Performance tracking** - Identify slow tests  
✅ **Clear reporting** - Know exactly what failed and why  

---

## 🚀 Quick Start

### Run All Tests
```bash
cd backend
python run_tests.py
```

### Run with Coverage
```bash
python run_tests.py --coverage
```

### Run Specific Categories
```bash
# Unit tests only (fast)
python run_tests.py --unit

# Integration tests (requires external services)
python run_tests.py --integration

# Smoke tests (quick validation)
python run_tests.py --smoke
```

### Run with Quality Checks
```bash
# Run linting + type checking + tests
python run_tests.py --all-checks
```

---

## 📋 Test Categories

### Unit Tests (`@pytest.mark.unit`)
- **Fast** (< 1 second per test)
- **Isolated** (no external dependencies)
- **Mock everything** (databases, APIs, LLMs)
- **High coverage** (80%+ goal)

**Example:**
```python
@pytest.mark.unit
def test_article_validation():
    article = {"title": "Test", "content": "Content"}
    assert validate_article(article) == True
```

### Integration Tests (`@pytest.mark.integration`)
- **Medium speed** (1-5 seconds per test)
- **Real dependencies** (Ollama, databases)
- **End-to-end flows** (API → Service → LLM)

**Example:**
```python
@pytest.mark.integration
@pytest.mark.requires_ollama
async def test_ollama_summarization():
    provider = OllamaProvider()
    result = await provider.summarize("Long article text...")
    assert result["success"] == True
```

### E2E Tests (`@pytest.mark.e2e`)
- **Slow** (5+ seconds per test)
- **Full workflows** (user journeys)
- **Real services** (everything wired up)

**Example:**
```python
@pytest.mark.e2e
async def test_article_scraping_to_display():
    # Scrape → Process → Embed → Display
    article = await scrape_article(url)
    summary = await summarize(article)
    embedding = await generate_embedding(article)
    assert all([article, summary, embedding])
```

### Smoke Tests (`@pytest.mark.smoke`)
- **Very fast** (< 0.5 seconds per test)
- **Critical paths** (app starts, imports work)
- **Run first** (catch major issues quickly)

**Example:**
```python
@pytest.mark.smoke
def test_app_imports():
    import production_main
    assert production_main is not None
```

---

## 🏃 Running Tests

### Basic Commands

```bash
# Run all tests
python run_tests.py

# Run specific test file
python run_tests.py test_ci.py

# Run multiple files
python run_tests.py test_ci.py test_ollama_integration.py

# Run tests matching pattern
pytest -k "test_ollama"
```

### Advanced Options

```bash
# Verbose output
python run_tests.py --verbose

# Stop on first failure
python run_tests.py --exitfirst

# Run in parallel (4 workers)
python run_tests.py --parallel 4

# Skip slow tests
python run_tests.py --skip-slow

# Show slowest 20 tests
python run_tests.py --durations 20
```

### CI Mode

```bash
# Skip tests requiring external services
python run_tests.py --ci

# Equivalent to:
pytest -m "not requires_ollama and not requires_network"
```

---

## 🏷️ Test Markers

Markers help categorize and filter tests:

| Marker | Description | Example |
|--------|-------------|---------|
| `@pytest.mark.unit` | Fast, isolated unit tests | `test_validation()` |
| `@pytest.mark.integration` | Integration with services | `test_ollama_api()` |
| `@pytest.mark.e2e` | End-to-end workflows | `test_complete_flow()` |
| `@pytest.mark.smoke` | Quick smoke tests | `test_imports()` |
| `@pytest.mark.slow` | Tests taking >5s | `test_large_dataset()` |
| `@pytest.mark.requires_ollama` | Needs Ollama running | `test_llm_summary()` |
| `@pytest.mark.requires_db` | Needs database | `test_article_repo()` |
| `@pytest.mark.requires_network` | Needs internet | `test_api_scraping()` |
| `@pytest.mark.skip_ci` | Skip in CI | `test_local_only()` |

### Using Markers

```python
import pytest

@pytest.mark.unit
@pytest.mark.smoke
def test_fast_validation():
    """Quick validation test."""
    assert True

@pytest.mark.integration
@pytest.mark.requires_ollama
@pytest.mark.slow
async def test_llm_processing():
    """Integration test with Ollama."""
    # Test code here
    pass
```

---

## 📊 Coverage Reports

### Generate Coverage

```bash
# Terminal output
python run_tests.py --coverage

# HTML report (opens in browser)
python run_tests.py --coverage
start htmlcov/index.html  # Windows
open htmlcov/index.html   # Mac/Linux
```

### Coverage Files

- **Terminal**: Inline coverage percentage
- **HTML**: `htmlcov/index.html` - Interactive browsing
- **XML**: `coverage.xml` - For CI tools (SonarQube, Codecov)

### Coverage Goals

- **Overall**: 80%+ coverage
- **Critical paths**: 95%+ coverage
- **New code**: 100% coverage

### Example Coverage Output

```
Name                        Stmts   Miss  Cover   Missing
---------------------------------------------------------
production_main.py             45      2    96%   23-24
llm/providers.py              120      8    93%   145-152
test_ci.py                     85      0   100%
---------------------------------------------------------
TOTAL                         250     10    96%
```

---

## 🔧 CI/CD Integration

### GitHub Actions

Your `.github/workflows/ci.yml` is already configured:

```yaml
- name: Run tests
  run: |
    cd backend
    python run_tests.py --ci --coverage --html-report
```

### CI-Specific Behavior

- **Skips Ollama tests** (not available in CI)
- **Skips network tests** (unreliable in CI)
- **Uses mock data** (fast, deterministic)
- **Short tracebacks** (easier to read logs)

### Running CI Tests Locally

```bash
# Simulate CI environment
python run_tests.py --ci

# Or with pytest directly
pytest -m "not requires_ollama and not requires_network" --tb=short
```

---

## ✍️ Writing Tests

### Test Structure

```python
"""
Test Module: [Module Name]
==========================

Description of what this module tests.
"""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.unit
class TestArticleValidation:
    """Test article validation logic."""
    
    def test_valid_article(self):
        """Test that valid article passes validation."""
        article = {"title": "Test", "content": "Content"}
        assert validate_article(article) == True
    
    def test_invalid_article_missing_title(self):
        """Test that article without title fails validation."""
        article = {"content": "Content"}
        assert validate_article(article) == False
    
    @pytest.mark.parametrize("title,expected", [
        ("Valid Title", True),
        ("", False),
        (None, False),
        ("A" * 1000, False),  # Too long
    ])
    def test_title_validation(self, title, expected):
        """Test various title validations."""
        article = {"title": title, "content": "Content"}
        assert validate_article(article) == expected


@pytest.mark.integration
@pytest.mark.requires_ollama
class TestOllamaIntegration:
    """Test Ollama LLM integration."""
    
    async def test_summarization(self):
        """Test article summarization with Ollama."""
        provider = OllamaProvider()
        
        article = "Long article content..."
        result = await provider.summarize(article)
        
        assert result["success"] == True
        assert "summary" in result
        assert len(result["summary"]) < len(article)
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_operation():
    """Test async function."""
    result = await async_function()
    assert result is not None
```

### Using Fixtures

```python
def test_with_sample_data(sample_article):
    """Test using fixture."""
    assert sample_article["title"] == "Test Article"

def test_with_mock_ollama(mock_ollama_client):
    """Test using mock."""
    # mock_ollama_client is automatically configured
    result = ollama_client.summarize("text")
    assert result is not None
```

### Mocking External Services

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.unit
async def test_with_mock():
    """Test with mocked external service."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance
        
        # Configure mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_instance.get.return_value = mock_response
        
        # Test code here
        result = await fetch_data()
        assert result["data"] == "test"
```

---

## 🔍 Troubleshooting

### Common Issues

#### Tests Not Found

```bash
# Check test discovery
pytest --collect-only

# Ensure test files start with test_
# Ensure test functions start with test_
```

#### Import Errors

```bash
# Check PYTHONPATH
python -c "import sys; print('\n'.join(sys.path))"

# Add backend to path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"  # Linux/Mac
$env:PYTHONPATH += ";$(pwd)\backend"              # Windows PowerShell
```

#### Async Tests Failing

```python
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Add marker
@pytest.mark.asyncio
async def test_async():
    await some_function()
```

#### Coverage Not Working

```bash
# Install coverage packages
pip install pytest-cov coverage

# Check configuration
cat pytest.ini

# Run with verbose
python run_tests.py --coverage --verbose
```

#### CI Tests Failing Locally Passing

```bash
# Run in CI mode locally
python run_tests.py --ci

# Check environment variables
echo $ENVIRONMENT
echo $USE_MOCK_DATA

# Use same Python version as CI
python --version  # Should match CI (3.11.13)
```

### Debug Mode

```bash
# Run with debugging
pytest --pdb  # Drop into debugger on failure

# Show print statements
pytest -s

# Very verbose
pytest -vv --tb=long --showlocals
```

---

## 📈 Best Practices

### ✅ DO

- Write tests before fixing bugs
- Use descriptive test names
- Test one thing per test
- Use fixtures for common setup
- Mock external dependencies
- Keep tests fast
- Add markers appropriately
- Document complex tests

### ❌ DON'T

- Test implementation details
- Write flaky tests
- Share state between tests
- Make tests depend on order
- Test third-party code
- Ignore failing tests
- Skip coverage on new code

---

## 📚 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

## 🎯 Summary

```bash
# Quick reference
python run_tests.py                    # Run all tests
python run_tests.py --unit             # Unit tests only
python run_tests.py --coverage         # With coverage
python run_tests.py --ci               # CI mode
python run_tests.py --all-checks       # Lint + Type + Test
python run_tests.py --help             # Show all options
```

**Happy Testing! 🚀**
