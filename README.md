# AI Tech News Assistant

A job-market-aligned AI Tech-News Assistant that aggregates, analyzes, and presents technology news with AI-powered insights to help professionals stay current with industry trends.

## 🚀 Features

- **News Ingestion**: Automated scraping from multiple tech news sources (RSS feeds, web scraping)
- **Local LLM Integration**: Free AI-powered summarization using Ollama (Llama 3.2, Mistral) with optional Claude fallback
- **AI Summarization**: Intelligent article summarization with keyword extraction and sentiment analysis
- **🔍 Semantic Search** ✨ **NEW**: AI-powered search using vector embeddings (Sentence Transformers)
  - Natural language queries with semantic understanding
  - Vector similarity search with cosine distance
  - Smart reranking (50% similarity + 30% title match + 20% recency)
  - Advanced filtering (source, category, date range, min score)
  - Sub-100ms query performance with caching
- **Interactive Dashboard**: React-based frontend for browsing and filtering news
- **Automated Pipeline**: Prefect-orchestrated daily news processing

## 🏗️ Architecture

This project follows a **Python-everywhere-except-frontend** strategy:

- **Backend**: FastAPI + LangChain + Chroma (Python)
- **Orchestration**: Prefect for task scheduling (Python)
- **Frontend**: React + TypeScript SPA
- **Deployment**: Docker containers + Vercel (frontend)

## 📁 Project Structure

```
ai-tech-news-assistant/
├── backend/                  # 🧠 FastAPI, LangChain, Vector DB logic
│   ├── api/                  # REST endpoints
│   ├── llm/                  # LLaMA interface logic
│   ├── rag/                  # Retrieval-Augmented Generation
│   ├── vectorstore/          # Chroma setup + queries
│   ├── utils/                # Configuration and logging
│   ├── main.py               # FastAPI app entrypoint
│   └── requirements.txt
├── frontend/                 # 🌐 React + TypeScript SPA (coming soon)
├── orchestrator/            # ⚙️ Scheduled tasks & pipelines (coming soon)
├── docker/                  # 🐳 Docker configs (coming soon)
└── .github/                 # 🚀 CI/CD workflows
```

## 🛠️ Quick Start

### Prerequisites

- **Python 3.9+** (Download from [python.org](https://python.org))
- **Node.js 18+** (for frontend development)
- **Git** (for version control)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ductringuyen0186/ai-tech-news-assistant.git
   cd ai-tech-news-assistant
   ```

2. **Set up Python environment**
   ```bash
   cd backend
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install and Configure Ollama (Recommended)**
   
   For free local LLM inference:
   
   ```bash
   # Download and install from https://ollama.com/download
   
   # Pull a model
   ollama pull llama3.2:1b  # Fast, lightweight (1.3GB)
   
   # Verify installation
   ollama list
   curl http://localhost:11434/api/tags
   ```
   
   📖 **Detailed Guide**: See [docs/OLLAMA_SETUP.md](docs/OLLAMA_SETUP.md) for:
   - Model comparison and selection
   - GPU acceleration setup
   - Performance optimization
   - Troubleshooting guide
   - API reference

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (Ollama config included)
   ```

6. **Run the FastAPI server**
   ```bash
   python main.py
   ```

6. **Access the API**
   - **Local Development**:
     - API Documentation: http://localhost:8000/docs
     - Health Check: http://localhost:8000/health
     - API Endpoints: http://localhost:8000/api/news
   - **Production Deployment**:
     - Frontend: https://frontend-khmjrrjtq-ductringuyen0186s-projects.vercel.app
     - API Documentation: https://ai-tech-news-assistant-backend.onrender.com/docs
     - Health Check: https://ai-tech-news-assistant-backend.onrender.com/health

## 🔧 Development Status

### ✅ Completed (Issue #3)
- [x] FastAPI project structure
- [x] Health check endpoints (`/ping`, `/health`)
- [x] Configuration management with environment variables
- [x] Structured logging framework
- [x] CORS middleware setup
- [x] Modular architecture (api/, llm/, rag/, vectorstore/, utils/)

### 🚧 In Progress
- [ ] RSS news ingestion pipeline (Issue #4)
- [ ] Content parsing and cleaning (Issue #5)
- [ ] Data storage implementation (Issue #6)
- [ ] LLM summarization integration (Issue #7)

### 📋 Planned
- [ ] Vector embeddings and Chroma DB (Issues #10-14)
- [ ] React frontend dashboard (Issues #16-20)
- [ ] Prefect orchestration (Issues #22-25)
- [ ] Docker deployment (Issues #27-31)

## 📚 API Endpoints

### Health & Monitoring
- `GET /` - API information
- `GET /ping` - Basic health check
- `GET /health` - Detailed health status
- `GET /search/health` - ✨ Search service health and statistics

### News & Articles
- `GET /news` - List news articles with pagination
- `POST /news/ingest` - Trigger RSS feed ingestion
- `GET /news/{source}` - Get articles from specific source

### 🔍 Semantic Search (NEW)
- `POST /search` - **AI-powered semantic article search**
  - Query using natural language
  - Vector similarity search with embeddings
  - Smart reranking (similarity + title match + recency)
  - Filter by source, category, date, score
  - Returns ranked results with relevance scores
  - 📖 **[Full API Documentation](docs/SEARCH_API.md)**

### AI Summarization
- `POST /summarize` - Generate AI summaries using Ollama
- `GET /summarize/health` - Check LLM service status

## 🔧 Configuration

Key environment variables in `.env`:

**Local Development:**
```bash
# Application
APP_NAME=AI Tech News Assistant
ENVIRONMENT=development
DEBUG=true

# Server
HOST=0.0.0.0
PORT=8000

# LLM Services
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Vector Database
CHROMA_PERSIST_DIRECTORY=./data/chroma_db

# News Sources
NEWS_SOURCES=https://feeds.feedburner.com/oreilly/radar,https://techcrunch.com/feed/
```

**Production Deployment:**
```bash
# Application
ENVIRONMENT=production
DEBUG=false

# Database (PostgreSQL on Render)
DATABASE_URL=postgresql://user:password@host:port/database

# CORS (Vercel frontend)
ALLOWED_ORIGINS=["https://frontend-khmjrrjtq-ductringuyen0186s-projects.vercel.app"]

# LLM Services (Groq - free tier, fast)
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
```

## 🤝 Contributing

1. Check the [GitHub Issues](https://github.com/ductringuyen0186/ai-tech-news-assistant/issues) for open tasks
2. Fork the repository
3. Create a feature branch: `git checkout -b feature/issue-number`
4. Make your changes
5. Add tests and ensure they pass
6. Submit a pull request linked to the issue

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- [GitHub Repository](https://github.com/ductringuyen0186/ai-tech-news-assistant)
- [Issues & Roadmap](https://github.com/ductringuyen0186/ai-tech-news-assistant/issues)
- **Production:**
  - [Live Application](https://frontend-khmjrrjtq-ductringuyen0186s-projects.vercel.app)
  - [API Documentation](https://ai-tech-news-assistant-backend.onrender.com/docs)
  - [Backend Health](https://ai-tech-news-assistant-backend.onrender.com/health)
- **Local Development:**
  - [Local API Docs](http://localhost:8000/docs) (when running locally)

A job-market-aligned AI Tech-News Assistant that aggregates, analyzes, and presents technology news with AI-powered insights to help professionals stay current with industry trends.

## 🚀 Features

- **News Ingestion**: Automated scraping from multiple tech news sources
- **AI Summarization**: LLM-powered article summarization using local or cloud models
- **Semantic Search**: RAG-powered search through news archives
- **Interactive Dashboard**: React-based frontend for exploring news and insights
- **Automated Pipeline**: Daily news processing with Prefect orchestration

## 🏗️ Architecture

- **Backend**: FastAPI (Python) with LangChain for LLM operations
- **Frontend**: React + TypeScript SPA deployed to Vercel
- **Vector Database**: Chroma for embedding storage and semantic search
- **Orchestration**: Prefect for automated workflows
- **Deployment**: Docker containers with free-tier cloud hosting

## 📁 Project Structure

```
ai-tech-news-assistant/
├── backend/                  # 🧠 FastAPI, LangChain, Vector DB logic
│   ├── api/                  # REST endpoints
│   ├── llm/                  # LLM interface logic
│   ├── rag/                  # Retrieval-Augmented Generation
│   ├── vectorstore/          # Chroma vector database
│   ├── utils/                # Configuration and utilities
│   ├── main.py               # FastAPI app entrypoint
│   └── requirements.txt      # Python dependencies
├── frontend/                 # 🌐 React + TypeScript SPA (coming soon)
├── orchestrator/            # ⚙️ Scheduled tasks & pipelines (coming soon)
├── docker/                  # 🐳 Docker configs (coming soon)
└── .github/                 # 🚀 CI/CD workflows (coming soon)
```

## 🛠️ Development Setup

### Prerequisites

1. **Python 3.9+**: Download from [python.org](https://www.python.org/downloads/)
2. **Git**: For version control
3. **VS Code**: Recommended IDE with Python extension

### Backend Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ductringuyen0186/ai-tech-news-assistant.git
   cd ai-tech-news-assistant
   ```

2. **Set up Python virtual environment**:
   ```bash
   cd backend
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the FastAPI server**:
   ```bash
   python main.py
   ```

6. **Access the API**:
   - **Local Development:**
     - API Documentation: http://localhost:8000/docs
     - Health Check: http://localhost:8000/health
     - Alternative Docs: http://localhost:8000/redoc
   - **Production:**
     - Frontend App: https://frontend-khmjrrjtq-ductringuyen0186s-projects.vercel.app
     - API Docs: https://ai-tech-news-assistant-backend.onrender.com/docs

## 📊 Current Status

- ✅ **Epic 1**: FastAPI project structure (Issue #3) - **COMPLETED**
- ⏳ **Epic 2**: RSS ingestion pipeline (Issue #4) - In Progress
- ⏳ **Epic 3**: Vector storage & RAG (Issues #8-14) - Pending
- ⏳ **Epic 4**: Frontend dashboard (Issues #15-20) - Pending
- ⏳ **Epic 5**: Orchestration & automation (Issues #21-25) - Pending
- ⏳ **Epic 6**: MLOps & deployment (Issues #26-31) - Pending

## 🧪 API Endpoints

### Health & Status
- `GET /` - API information
- `GET /ping` - Simple health check
- `GET /health` - Detailed health status

### API Routes (v1)
- `GET /api/v1/` - API version information
- `GET /api/v1/news` - Latest news (coming soon)
- `POST /api/v1/summarize` - Summarize articles (coming soon)
- `GET /api/v1/search` - Semantic search (coming soon)

## 🔧 Configuration

Key environment variables in `.env`:

```env
# Application
APP_NAME=AI Tech News Assistant
ENVIRONMENT=development
DEBUG=true

# Server
HOST=0.0.0.0
PORT=8000

# LLM Services (optional)
OPENAI_API_KEY=your_key_here
OLLAMA_HOST=http://localhost:11434

# News Sources
NEWS_SOURCES=https://feeds.feedburner.com/oreilly/radar,https://techcrunch.com/feed/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes following the project conventions
4. Run tests: `pytest`
5. Submit a pull request

## 📝 Development Notes

This project follows clean architecture principles with:
- **Dependency Injection** for services
- **Type Hints** throughout Python code
- **Pydantic Models** for data validation
- **Structured Logging** for observability
- **Environment-based Configuration**

## 🚀 Next Steps

1. Implement RSS news ingestion (Issue #4)
2. Add LLM summarization with Ollama (Issue #7)
3. Set up Chroma vector database (Issue #11)
4. Build React frontend dashboard (Issue #16)
5. Deploy to production with Docker (Issue #27)

---

**Repository**: https://github.com/ductringuyen0186/ai-tech-news-assistant  
**Issues**: Track progress and report bugs in GitHub Issues  
**Documentation**: See `/docs` for detailed API documentation