# Quick Start Guide - AI Tech News Assistant

## 🚀 Getting Started

### Prerequisites
- **Python 3.9+** installed with pip
- **Git** (for version control)

### 1. Install Python
Download from: https://www.python.org/downloads/windows/
⚠️ **Important**: Check "Add Python to PATH" during installation

### 2. Setup Project
```powershell
# Navigate to project
cd C:\Users\Tri\OneDrive\Desktop\Portfolio\ai-tech-news-assistant\backend

# Run setup script (Windows)
setup_python.bat

# OR manually:
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn pydantic httpx pytest beautifulsoup4 feedparser
```

### 3. Run Application
```powershell
# Activate virtual environment
venv\Scripts\activate

# Start the server
python -m uvicorn src.main:app --reload
```

### 4. Access Application
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **API Info**: http://localhost:8000/

### 5. Run Tests
```powershell
# Run all tests
pytest tests/

# Run specific test types
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

## 📁 Project Structure
```
backend/
├── src/                 # Refactored source code
│   ├── api/routes/     # API endpoints
│   ├── services/       # Business logic  
│   ├── repositories/   # Data access
│   ├── models/         # Data models
│   ├── core/          # Core utilities
│   └── main.py        # Application entry
├── tests/             # Test suite
├── scripts/           # Utility scripts
└── setup_python.bat   # Quick setup
```

## 🎯 Key Features
- ✅ **News Ingestion**: RSS feed processing
- ✅ **AI Summarization**: LLM-powered summaries  
- ✅ **Embeddings**: Semantic search capability
- ✅ **RESTful API**: Full FastAPI implementation
- ✅ **Type Safety**: Comprehensive Pydantic models
- ✅ **Test Coverage**: Unit, integration, e2e tests

## 🔧 Development
- **Code Style**: Black, Flake8
- **Testing**: Pytest with async support
- **Documentation**: Auto-generated with FastAPI
- **Architecture**: Clean layered design

Happy coding! 🎉
