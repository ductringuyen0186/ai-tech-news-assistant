# AI Tech News Assistant 🤖📰

> A production-ready, AI-powered tech news aggregation platform with personalized feeds, real-time scraping, and intelligent content analysis.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-blue.svg)](https://reactjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Features

### Core Capabilities
- **🔄 Real-time News Aggregation** - Scrapes from 11+ tech news sources
- **🤖 AI-Powered Analysis** - Automatic summarization, categorization, and sentiment analysis
- **🎯 Personalized Feed** - Customizable preferences across 20 tech categories
- **🔍 Smart Search** - Keyword-based and semantic search capabilities
- **👤 User Management** - Secure authentication with JWT tokens
- **📊 Analytics** - Article engagement tracking and reading history

### Tech Categories
AI/ML • Software Development • Big Tech • Military Tech • Home Tech • Automotive • Blockchain • Cybersecurity • Cloud • IoT • Robotics • Quantum Computing • Biotech • Fintech • Gaming • AR/VR • Space Tech • Green Tech • Startups • General

### News Sources
**Major Tech Sites:** TechCrunch, The Verge, Ars Technica, Wired, VentureBeat, MIT Tech Review
**Community:** Hacker News, Reddit Programming, GitHub Trending
**AI/ML:** OpenAI Blog, Google AI Blog

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  Dashboard • Articles • Search • Settings • Authentication   │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Auth Service │  │  AI Service  │  │   Scrapers   │     │
│  │   (JWT)      │  │   (Ollama)   │  │  (11 src)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Database   │  │   Caching    │  │  Monitoring  │     │
│  │  (SQLite)    │  │   (Redis)    │  │   (Logs)     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

**Stack:**
- **Backend:** FastAPI, SQLAlchemy, Pydantic
- **Frontend:** React, TypeScript, Tailwind CSS
- **AI:** Ollama (local LLM), Transformers
- **Database:** SQLite (dev), PostgreSQL (prod)
- **Caching:** Redis (optional)
- **Deployment:** Docker, Docker Compose

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Ollama** (optional) - [Download](https://ollama.com) for AI features

### 🎯 Easiest Way: Automated Startup Scripts

We provide smart startup scripts that handle everything automatically!

#### Windows
```bash
# First time setup (install dependencies)
setup-dev.bat

# Start the application
start-app.bat

# Start without AI features (faster, no Ollama needed)
start-app.bat --no-ai

# Skip dependency checks (faster startup)
start-app.bat --skip-deps
```

#### macOS/Linux
```bash
# First time setup (install dependencies)
chmod +x setup-dev.sh
./setup-dev.sh

# Start the application
chmod +x start-app.sh
./start-app.sh

# Start without AI features (faster, no Ollama needed)
./start-app.sh --no-ai

# Skip dependency checks (faster startup)
./start-app.sh --skip-deps
```

**What the scripts do:**
- ✅ Check system prerequisites (Python, Node.js)
- ✅ Create virtual environments automatically
- ✅ Install/update dependencies intelligently
- ✅ Detect if Ollama is installed for AI features
- ✅ Start both backend and frontend in separate windows
- ✅ Show you all the URLs and info you need

---

### 📚 Manual Setup (Alternative)

If you prefer manual control:

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/ai-tech-news-assistant.git
cd ai-tech-news-assistant
```

### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set SECRET_KEY to a secure random string:
# Windows PowerShell:
# -join (1..32 | ForEach-Object { '{0:x}' -f (Get-Random -Max 16) })
# macOS/Linux:
# openssl rand -hex 32

# Run the backend
python production_main.py
```

Backend will start at: **http://localhost:8001**

### 3. Frontend Setup

```bash
# In a new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will start at: **http://localhost:5173**

### 4. (Optional) Setup Ollama for AI Features

```bash
# Install Ollama from https://ollama.com

# Pull the model
ollama pull llama3.2:1b

# Verify it's running
curl http://localhost:11434/api/tags
```

### 5. Test the Application

1. **Open frontend:** http://localhost:5173
2. **API docs:** http://localhost:8001/docs
3. **Health check:** http://localhost:8001/health

---

## 📖 Usage Guide

### Creating Your First Account

**Via API:**
```bash
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "techfan",
    "password": "SecurePass123",
    "full_name": "Tech Enthusiast"
  }'
```

**Via Frontend:**
1. Navigate to http://localhost:5173
2. Click "Sign Up"
3. Fill in your details
4. Start customizing your preferences!

### Setting Preferences

```bash
# Login to get token
TOKEN=$(curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123"}' \
  | jq -r '.access_token')

# Set preferred categories
curl -X POST http://localhost:8001/api/v1/preferences/categories \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '["ai_ml", "software_dev", "big_tech"]'
```

### Fetching News

```bash
# Trigger news fetch (will auto-enrich with AI)
curl -X POST http://localhost:8001/api/v1/fetch-news \
  -H "Authorization: Bearer $TOKEN"

# Get your personalized feed
curl http://localhost:8001/api/v1/articles \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔧 Configuration

### Environment Variables

Key configuration in `backend/.env`:

```env
# Security (REQUIRED - change in production!)
SECRET_KEY=your-secret-key-use-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server
HOST=0.0.0.0
PORT=8001
DEBUG=false

# Database
DATABASE_URL=sqlite:///./news_production.db

# AI/LLM (optional)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b

# News Scraping
MAX_ARTICLES_PER_SOURCE=15
CACHE_EXPIRY_HOURS=2

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

See `backend/.env.example` for all available options.

---

## 📚 API Documentation

### Authentication Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Create new user account |
| `/auth/login` | POST | Login and get JWT token |
| `/auth/me` | GET | Get current user info |
| `/auth/me` | PUT | Update user profile |

### Preference Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/preferences/` | GET | Get all preferences |
| `/preferences/` | PUT | Update preferences |
| `/preferences/categories` | POST | Set tech categories |
| `/preferences/categories/available` | GET | List all categories |

### Article Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/articles` | GET | Get articles (paginated) |
| `/search` | POST | Search articles |
| `/summarize` | POST | Summarize text |
| `/fetch-news` | POST | Trigger news fetch |
| `/sources` | GET | Get source statistics |

**Full API Documentation:** http://localhost:8001/docs

---

## 📦 Project Structure

```
ai-tech-news-assistant/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   │   ├── auth.py        # Authentication
│   │   │   ├── endpoints.py   # Main endpoints
│   │   │   └── preferences.py # User preferences
│   │   ├── models/            # Database models
│   │   │   ├── __init__.py    # Article models
│   │   │   └── user.py        # User models
│   │   ├── scrapers/          # News scrapers
│   │   │   ├── base.py
│   │   │   ├── hackernews.py
│   │   │   ├── reddit.py
│   │   │   ├── github.py
│   │   │   └── rss_scraper.py # RSS feeds
│   │   ├── services/          # Business logic
│   │   │   ├── ai_service.py  # AI enrichment
│   │   │   ├── auth_service.py # Authentication
│   │   │   ├── database.py    # Database ops
│   │   │   └── scraping.py    # Scraper manager
│   │   └── core/              # Config & utils
│   │       └── config.py
│   ├── production_main.py     # Application entry
│   ├── requirements.txt       # Python deps
│   └── .env.example          # Config template
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── pages/            # Page components
│   │   ├── components/       # Reusable components
│   │   ├── lib/             # Utilities
│   │   └── types/           # TypeScript types
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml        # Docker config
├── README.md                 # This file
├── QUICK_START.md           # Quick start guide
└── PRODUCTION_READY_IMPLEMENTATION.md  # Full feature docs
```

---

## 🚢 Production Deployment

### What's Missing for Production Deployment

#### ⚠️ **CRITICAL - Must Be Completed**

1. **Security Configuration**
   - [ ] Change `SECRET_KEY` to secure random string (32+ chars)
   - [ ] Set `DEBUG=false` in production
   - [ ] Configure proper CORS origins for production domain
   - [ ] Enable HTTPS/SSL certificates
   - [ ] Remove `.env` from version control (use secrets manager)

2. **Database Migration**
   - [ ] Migrate from SQLite to PostgreSQL
   - [ ] Update `DATABASE_URL` in production
   - [ ] Create database backups strategy
   - [ ] Run Alembic migrations

3. **Infrastructure**
   - [ ] Setup production server (AWS, DigitalOcean, etc.)
   - [ ] Configure reverse proxy (Nginx/Caddy)
   - [ ] Setup domain name and DNS
   - [ ] Configure firewall rules

#### 🔄 **RECOMMENDED - Highly Suggested**

1. **Performance & Scaling**
   - [ ] Setup Redis for caching
   - [ ] Implement API rate limiting
   - [ ] Configure CDN for static assets
   - [ ] Setup load balancer (if needed)

2. **Background Jobs**
   - [ ] Setup Celery + Redis/RabbitMQ
   - [ ] Configure scheduled news fetching
   - [ ] Setup email notifications

3. **Monitoring & Logging**
   - [ ] Integrate error tracking (Sentry)
   - [ ] Setup application monitoring (Prometheus)
   - [ ] Configure log aggregation (ELK stack)
   - [ ] Create health check dashboard

4. **CI/CD Pipeline**
   - [ ] Setup GitHub Actions workflows
   - [ ] Configure automated testing
   - [ ] Setup automated deployments
   - [ ] Implement staging environment

#### 📋 **OPTIONAL - Nice to Have**

1. **Advanced Features**
   - [ ] Vector database for semantic search (ChromaDB/Pinecone)
   - [ ] Email digest system
   - [ ] Push notifications
   - [ ] Social sharing features

2. **Frontend Enhancements**
   - [ ] Complete Settings page UI
   - [ ] Add authentication UI components
   - [ ] Implement bookmarking interface
   - [ ] Add reading history

3. **DevOps**
   - [ ] Kubernetes deployment config
   - [ ] Automated backup scripts
   - [ ] Disaster recovery plan
   - [ ] Performance testing

---

### Quick Production Deployment Guide

#### Option 1: Docker Compose (Recommended for Small-Medium Scale)
```bash
# Update docker-compose.yml for production
# Build and start
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f backend
```

#### Option 2: Cloud Platforms (Easiest)

**Backend Options:**
- **Railway** - Zero config deployment
- **Render** - Auto-deploy from Git
- **Fly.io** - Global edge deployment
- **DigitalOcean App Platform** - Managed service

**Frontend Options:**
- **Vercel** - Zero config React deployment
- **Netlify** - CI/CD built-in
- **Cloudflare Pages** - Free tier

**Database Options:**
- **Neon** - Serverless Postgres
- **Supabase** - Postgres + extras
- **PlanetScale** - Serverless MySQL alternative

#### Option 3: Manual VPS Deployment

```bash
# 1. Setup VPS (Ubuntu 22.04)
ssh user@your-server-ip

# 2. Install dependencies
sudo apt update
sudo apt install python3.9 python3-pip nginx certbot

# 3. Clone and setup
git clone https://github.com/yourusername/ai-tech-news-assistant.git
cd ai-tech-news-assistant/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure systemd service
sudo nano /etc/systemd/system/ai-news.service

# 5. Configure Nginx reverse proxy
sudo nano /etc/nginx/sites-available/ai-news

# 6. Enable SSL
sudo certbot --nginx -d yourdomain.com

# 7. Start service
sudo systemctl start ai-news
sudo systemctl enable ai-news
```

---

### Production Deployment Checklist

**Copy this checklist when deploying:**

```
□ Backend Configuration
  □ SECRET_KEY set to secure random string
  □ DEBUG=false
  □ PostgreSQL configured
  □ DATABASE_URL updated
  □ ALLOWED_ORIGINS set to production domains
  □ Environment variables secured

□ Database
  □ PostgreSQL database created
  □ Migrations executed
  □ Backup strategy implemented
  □ Connection pooling configured

□ Security
  □ HTTPS/SSL enabled
  □ Firewall configured
  □ API rate limiting active
  □ Input validation enabled
  □ CORS properly configured

□ Infrastructure
  □ Domain name configured
  □ DNS records set
  □ Reverse proxy (Nginx) setup
  □ Health checks working
  □ Logs accessible

□ Monitoring (Recommended)
  □ Error tracking (Sentry)
  □ Application monitoring
  □ Uptime monitoring
  □ Alert notifications configured

□ Performance (Recommended)
  □ Redis caching enabled
  □ CDN configured for static assets
  □ Database indexes optimized
  □ Response compression enabled

□ Frontend
  □ Built for production (npm run build)
  □ Environment variables set
  □ Assets optimized
  □ Deployed to CDN/hosting

□ Testing
  □ All tests passing
  □ Manual smoke tests completed
  □ Load testing performed
  □ Security scan completed

□ Documentation
  □ Deployment guide written
  □ API documentation updated
  □ Runbook created
  □ Team trained
```

---

## 🛠️ Development

### Adding a New News Source

1. Create scraper in `backend/app/scrapers/`:
```python
from .base import BaseScraper
from ..models import ArticleCreate

class MyNewsScraper(BaseScraper):
    def __init__(self):
        super().__init__("My News Source")
        self.api_url = "https://api.mynews.com"

    async def _scrape_implementation(self):
        # Implement scraping logic
        pass
```

2. Register in `backend/app/services/scraping.py`:
```python
from ..scrapers.mynews import MyNewsScraper

self.scrapers = {
    # ... existing scrapers
    "mynews": MyNewsScraper(),
}
```

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest
pytest --cov=app tests/

# Frontend tests
cd frontend
npm test
npm run test:coverage
```

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- **FastAPI** - Modern web framework
- **Ollama** - Local LLM inference
- **React** - UI framework
- News sources for providing RSS feeds

---

## 📞 Support & Documentation

- **Quick Start:** See [QUICK_START.md](QUICK_START.md)
- **Full Documentation:** See [PRODUCTION_READY_IMPLEMENTATION.md](PRODUCTION_READY_IMPLEMENTATION.md)
- **API Docs:** http://localhost:8001/docs
- **Issues:** GitHub Issues

---

**Built with ❤️ for the tech community**

*Stay informed, stay ahead.* 🚀
