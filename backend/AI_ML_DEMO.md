# AI/ML Features Demo 🤖

This demo showcases the core AI/ML capabilities of the AI Tech News Assistant.

## ✨ Features Demonstrated

### 🔄 **News Ingestion Pipeline**
- Automated RSS feed scraping from tech news sources
- Content extraction and cleaning
- Metadata collection and storage

### 🧠 **AI-Powered Summarization**
- LLM-based article summarization using Ollama (local) or Claude (API)
- Technical content processing
- Fallback extractive summarization

### 🔮 **Semantic Embeddings**
- Text-to-vector conversion using Sentence Transformers
- Multiple embedding models support
- Efficient batch processing

### 🔍 **Semantic Search**
- Vector similarity search
- Natural language queries
- Hybrid search combining text and semantic matching

### 🎯 **RAG System**
- Retrieval-Augmented Generation
- Context-aware question answering
- Source attribution and relevance ranking

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Install dependencies
python setup_demo.py

# Optional: Install Ollama for local LLM
# Download from: https://ollama.ai/download
# Then: ollama pull llama2
```

### 2. Run Demo API
```bash
# Start the demo FastAPI server
python demo_app.py

# Open browser to: http://localhost:8000/docs
```

### 3. Run Command-Line Demo
```bash
# Run the full AI/ML pipeline demo
python demo_ai_ml.py
```

## 📋 Demo Endpoints

### **GET /demo/features**
Get information about all available AI/ML features
```bash
curl http://localhost:8000/demo/features
```

### **POST /demo/run-full**
Run the complete AI/ML pipeline demonstration
```bash
curl -X POST http://localhost:8000/demo/run-full
```

### **GET /demo/status**
Check the status of running demos
```bash
curl http://localhost:8000/demo/status
```

### **POST /demo/quick-search**
Test semantic search with a query
```bash
curl -X POST "http://localhost:8000/demo/quick-search" \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence", "limit": 5}'
```

### **POST /demo/test-llm**
Test LLM provider connectivity
```bash
curl -X POST http://localhost:8000/demo/test-llm
```

## 🎬 Demo Flow

1. **🔧 Setup**: Initialize database and configure sources
2. **📰 Ingestion**: Fetch articles from RSS feeds (HackerNews, TechCrunch, The Verge)
3. **🧹 Processing**: Extract and clean article content
4. **🤖 Summarization**: Generate AI summaries using LLM
5. **🔮 Embeddings**: Create semantic vector embeddings
6. **🔍 Search**: Demonstrate semantic search capabilities
7. **🎯 RAG**: Show question-answering with context retrieval

## 🛠️ Tech Stack

- **Backend**: FastAPI + SQLAlchemy
- **AI/ML**: Sentence Transformers + LangChain
- **LLM**: Ollama (local) + Claude API (optional)
- **Vector DB**: Chroma + SQLite embeddings
- **Processing**: AsyncIO + Background Tasks

## 📊 Demo Data

The demo includes:
- **Sample RSS Sources**: 3 major tech news outlets
- **Article Processing**: ~10-15 articles per demo run
- **Embedding Generation**: 384-dimensional vectors
- **Search Queries**: Pre-defined tech-focused queries
- **Mock Data**: Fallback data when external sources are unavailable

## 🔧 Configuration

Create a `.env` file with:
```env
DATABASE_URL=sqlite:///./data/news.db
ANTHROPIC_API_KEY=your_claude_api_key_here
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=all-MiniLM-L6-v2
LOG_LEVEL=INFO
```

## 🎯 Demo Scenarios

### Scenario 1: Full Pipeline Demo
Shows the complete AI/ML workflow from ingestion to search.

### Scenario 2: Semantic Search
Demonstrates vector similarity search with natural language queries.

### Scenario 3: LLM Summarization
Shows AI-powered content summarization with different models.

### Scenario 4: RAG Q&A
Demonstrates question-answering using retrieved context.

## 📈 Performance Metrics

- **Ingestion**: ~5-10 articles/minute
- **Summarization**: ~2-3 articles/minute (local LLM)
- **Embeddings**: ~50-100 texts/minute
- **Search**: Sub-second response times
- **Memory**: ~200-500MB for small model

## 🐛 Troubleshooting

### Common Issues:

1. **Ollama not available**: Install from https://ollama.ai/download
2. **Model download fails**: Check internet connection
3. **API rate limits**: Add delays between requests
4. **Memory issues**: Use smaller embedding models

### Fallback Options:

- **No LLM**: Uses extractive summarization
- **No Ollama**: Falls back to Claude API (if configured)
- **No external data**: Uses mock articles for demo

## 🎯 Production Readiness

This demo shows the core AI/ML capabilities. For production:

1. **Scale**: Use production-grade vector databases (Pinecone, Weaviate)
2. **Performance**: Implement caching and batch processing
3. **Monitoring**: Add logging and metrics collection
4. **Security**: Implement authentication and rate limiting
5. **Reliability**: Add error handling and retry mechanisms

---

**Ready to explore the AI/ML capabilities? Start with `python demo_app.py` and visit http://localhost:8000/docs!** 🚀
