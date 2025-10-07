# Quick Start Guide - AI Tech News Assistant

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.9+
- Node.js 18+ (for frontend)
- Ollama (optional, for AI features)

---

## Backend Setup

### 1. Install Python Dependencies
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# KEY VARIABLES:
# - SECRET_KEY: Change to a secure random string
# - OLLAMA_HOST: http://localhost:11434 (if using Ollama)
# - DATABASE_URL: sqlite:///./news_production.db
```

### 3. (Optional) Setup Ollama for AI Features
```bash
# Install Ollama
# Visit: https://ollama.com

# Pull the model
ollama pull llama3.2:1b

# Verify it's running
curl http://localhost:11434/api/tags
```

### 4. Run the Backend
```bash
python production_main.py
```

Backend will start at: `http://localhost:8001`

---

## Frontend Setup

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Run Development Server
```bash
npm run dev
```

Frontend will start at: `http://localhost:5173`

---

## First Steps

### 1. Test the API
Open browser: `http://localhost:8001/docs`

### 2. Create a User Account
```bash
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "username": "demo",
    "password": "DemoPass123",
    "full_name": "Demo User"
  }'
```

Response will include your access token.

### 3. Set Your Preferences
```bash
# Save your token
TOKEN="your_access_token_here"

# Set preferred categories
curl -X POST http://localhost:8001/api/v1/preferences/categories \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '["ai_ml", "software_dev", "big_tech", "auto_tech"]'
```

### 4. Fetch Latest News
```bash
# Trigger news fetch (will auto-enrich with AI)
curl -X POST http://localhost:8001/api/v1/fetch-news \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Get Personalized Feed
```bash
curl http://localhost:8001/api/v1/articles \
  -H "Authorization: Bearer $TOKEN"
```

---

## Available Tech Categories

Choose your interests:

- `ai_ml` - AI & Machine Learning
- `software_dev` - Software Development
- `big_tech` - Big Tech Companies
- `military_tech` - Military Technology
- `home_tech` - Smart Home & IoT
- `auto_tech` - Automotive & Self-Driving
- `blockchain` - Blockchain & Crypto
- `cybersecurity` - Cybersecurity
- `cloud` - Cloud Computing
- `iot` - Internet of Things
- `robotics` - Robotics
- `quantum` - Quantum Computing
- `biotech` - Biotechnology
- `fintech` - Financial Technology
- `gaming` - Gaming & Esports
- `ar_vr` - AR/VR & Spatial Computing
- `space_tech` - Space Technology
- `green_tech` - Clean Energy
- `startup` - Startups & VC
- `general` - General Tech News

---

## News Sources

The app fetches from 11 sources:

**Original:**
- Hacker News
- Reddit Programming
- GitHub Trending

**Tech News Sites:**
- TechCrunch
- The Verge
- Ars Technica
- Wired
- VentureBeat
- MIT Technology Review

**AI/ML Specific:**
- OpenAI Blog
- Google AI Blog

---

## Key Features

### ✨ AI-Powered
- Automatic summarization
- Smart categorization
- Keyword extraction
- Sentiment analysis

### 🎯 Personalized
- Set preferred categories
- Choose favorite sources
- Customize reading preferences
- Save bookmarks (coming soon)

### 🔒 Secure
- JWT authentication
- Password hashing
- Protected endpoints

---

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### AI features not working
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start Ollama
ollama serve

# Pull the model
ollama pull llama3.2:1b
```

### Database issues
```bash
# Delete and recreate database
rm news_production.db
python production_main.py  # Will recreate tables
```

### Port conflicts
```bash
# Backend using 8001 instead of 8000
# Frontend using 5173

# Change in .env:
PORT=8001  # or any free port
```

---

## API Endpoints

### Public
- `GET /` - API info
- `GET /ping` - Health check
- `POST /auth/register` - Register
- `POST /auth/login` - Login

### Protected (requires token)
- `GET /auth/me` - Get user info
- `PUT /auth/me` - Update profile
- `GET /preferences/` - Get preferences
- `PUT /preferences/` - Update preferences
- `POST /preferences/categories` - Set categories
- `GET /articles` - Get articles
- `POST /fetch-news` - Trigger news fetch
- `POST /search` - Search articles
- `POST /summarize` - Summarize text

Full docs: `http://localhost:8001/docs`

---

## Next Steps

1. **Set up your preferences** via API or frontend
2. **Fetch news** to populate the database
3. **Explore personalized feed** based on your interests
4. **Try AI features** like summarization and search

---

## Development

### Run with auto-reload
```bash
# Backend
uvicorn production_main:app --reload --host 0.0.0.0 --port 8001

# Frontend
npm run dev
```

### Run tests
```bash
# Backend
pytest

# Frontend
npm test
```

### Check logs
```bash
# Backend logs in console
# Or check: backend/logs/app.log (if configured)
```

---

## Production Deployment

See `PRODUCTION_READY_IMPLEMENTATION.md` for:
- Docker deployment
- PostgreSQL migration
- Redis caching
- CI/CD setup
- Monitoring

---

## Support

- **API Docs:** http://localhost:8001/docs
- **GitHub Issues:** [Your repo]/issues
- **Documentation:** See README.md and PRODUCTION_READY_IMPLEMENTATION.md

**Happy coding! 🎉**
