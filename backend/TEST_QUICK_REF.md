# Test Automation Quick Reference

## 🎯 Common Commands

| Command | Description |
|---------|-------------|
| `python run_tests.py` | Run all tests |
| `python run_tests.py --unit` | Unit tests only (fast) |
| `python run_tests.py --integration` | Integration tests |
| `python run_tests.py --smoke` | Smoke tests (quick check) |
| `python run_tests.py --coverage` | Run with coverage |
| `python run_tests.py --ci` | CI mode (skip external services) |
| `python run_tests.py --all-checks` | Lint + Type + Tests |
| `python run_tests.py --verbose` | Detailed output |
| `python run_tests.py --exitfirst` | Stop on first failure |
| `python run_tests.py --parallel 4` | Run with 4 workers |

## 🏷️ Test Markers

```python
@pytest.mark.unit                # Fast, isolated
@pytest.mark.integration         # With external services
@pytest.mark.e2e                 # Full workflows
@pytest.mark.smoke               # Quick validation
@pytest.mark.slow                # Takes >5 seconds
@pytest.mark.requires_ollama     # Needs Ollama
@pytest.mark.requires_db         # Needs database
@pytest.mark.requires_network    # Needs internet
@pytest.mark.skip_ci             # Skip in CI
```

## 📊 Coverage

```bash
# Generate coverage report
python run_tests.py --coverage

# View HTML report
start htmlcov/index.html  # Windows
open htmlcov/index.html   # Mac/Linux

# Coverage files
- htmlcov/index.html  (interactive)
- coverage.xml        (CI tools)
```

## 🔍 Debugging

```bash
# Run specific test
pytest test_ci.py::test_imports

# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb

# Very verbose
pytest -vv --tb=long --showlocals
```

## ✍️ Writing Tests

```python
# Simple test
@pytest.mark.unit
def test_validation():
    assert validate("test") == True

# Async test
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_func()
    assert result is not None

# With fixture
def test_with_data(sample_article):
    assert sample_article["title"]

# Parametrized test
@pytest.mark.parametrize("input,expected", [
    ("valid", True),
    ("invalid", False),
])
def test_multiple_cases(input, expected):
    assert validate(input) == expected
```

## 🚀 CI/CD

```bash
# Run like CI does
python run_tests.py --ci

# Check what CI will run
pytest -m "not requires_ollama and not requires_network" --collect-only
```

## 🎯 Goals

- **Coverage**: 80%+ overall
- **Unit tests**: < 1s each
- **Integration tests**: < 5s each
- **All tests**: < 2 minutes total

## 📁 Test Structure

```
backend/
├── run_tests.py           # Test automation framework
├── pytest.ini             # Pytest configuration
├── conftest.py            # Shared fixtures
├── test_ci.py             # Unit tests (CI-safe)
├── test_ollama_integration.py  # Integration tests
└── tests/                 # Additional test suites
    ├── unit/
    ├── integration/
    └── e2e/
```

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Tests not found | Check file/function names start with `test_` |
| Import errors | Add backend to PYTHONPATH |
| Async tests fail | Install `pytest-asyncio` |
| Coverage not working | Install `pytest-cov` |
| CI tests fail locally | Run with `--ci` flag |

---

**Pro Tip**: Run `python run_tests.py --help` for all options!
