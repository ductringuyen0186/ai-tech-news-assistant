# Configuration Guide

This guide explains how to configure the AI Tech News Assistant for different environments.

## Table of Contents

1. [Environment Files Overview](#environment-files-overview)
2. [Frontend Configuration](#frontend-configuration)
3. [Backend Configuration](#backend-configuration)
4. [API Endpoints](#api-endpoints)
5. [Development vs Production](#development-vs-production)
6. [Troubleshooting](#troubleshooting)

---

## Environment Files Overview

The application uses environment files to manage configuration:

### Frontend
- `.env` - Current active configuration (used by default)
- `.env.development` - Development-specific settings
- `.env.production` - Production-specific settings

### Backend
- `.env` - Current active configuration
- `.env.development` - Development-specific settings
- `.env.production` - Production-specific settings
- `.env.example` - Template with all available options

---

## Frontend Configuration

### Location
`frontend/.env`

### Key Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:8001` | Backend API URL |
| `VITE_APP_NAME` | `AI Tech News Assistant` | Application name |
| `VITE_APP_VERSION` | `2.0.0` | Application version |

### Usage in Code

The frontend uses a centralized API client (`frontend/src/lib/api.ts`) that automatically reads `VITE_API_BASE_URL`:

```typescript
import api from '../lib/api';

// All API calls use the configured base URL
const response = await api.get('/articles');
const response = await api.post('/search', { query: 'AI' });
```

### Important Notes

1. **Vite Environment Variables**: All frontend env variables must be prefixed with `VITE_` to be exposed to the client code
2. **Rebuild Required**: Changes to `.env` files require restarting the dev server or rebuilding
3. **Type Safety**: TypeScript types for env variables are defined in `frontend/src/types/global.d.ts`

---

## Backend Configuration

### Location
`backend/.env`

### Key Variables

#### Server Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `127.0.0.1` | Server bind address (use `0.0.0.0` for production) |
| `PORT` | `8001` | Server port |
| `DEBUG` | `false` | Enable debug mode |
| `RELOAD` | `false` | Enable auto-reload on code changes |

#### Database
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./news_production.db` | Database connection string |
| `DATABASE_ECHO` | `false` | Log SQL queries |

#### CORS
| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOWED_ORIGINS` | `http://localhost:5173,...` | Comma-separated list of allowed origins |

#### AI/ML
| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3.2:1b` | LLM model to use |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `ANTHROPIC_API_KEY` | - | Optional: Claude API key for production |

#### Security
| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | - | **REQUIRED**: JWT secret key (change in production!) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token expiration time |

### Usage in Code

Backend configuration is managed by `backend/app/core/config.py`:

```python
from app.core.config import settings

# Access configuration values
print(settings.PORT)
print(settings.OLLAMA_HOST)
```

---

## API Endpoints

All API endpoints are relative to the base URL configured in `VITE_API_BASE_URL`.

### Health & Status
- `GET /` - Root endpoint, returns API info
- `GET /health` - Health check endpoint

### Articles
- `GET /articles` - Get all articles
- `POST /fetch-news` - Fetch fresh news from sources

### Search
- `POST /search` - Search articles
  ```json
  {
    "query": "AI",
    "limit": 10
  }
  ```

### Summarization
- `POST /summarize` - Summarize text
  ```json
  {
    "text": "Article content...",
    "max_length": 150
  }
  ```

### Testing
- `GET /test-llm` - Test LLM connectivity

### Documentation
- `GET /docs` - Swagger/OpenAPI documentation
- `GET /redoc` - ReDoc documentation

---

## Development vs Production

### Development Mode

**Frontend** (`.env.development`):
```env
VITE_API_BASE_URL=http://localhost:8001
```

**Backend** (`.env.development`):
```env
HOST=127.0.0.1
PORT=8001
DEBUG=true
RELOAD=true
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///./news_development.db
```

**Starting Development Servers**:
```bash
# Option 1: Use the automated startup script
./start-app.bat   # Windows
./start-app.sh    # Linux/Mac

# Option 2: Manual start
# Terminal 1 - Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python production_main.py

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

### Production Mode

**Frontend** (`.env.production`):
```env
# Update this to your production backend URL
VITE_API_BASE_URL=https://api.yourdomain.com
```

**Backend** (`.env.production`):
```env
HOST=0.0.0.0
PORT=8001
DEBUG=false
RELOAD=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@localhost:5432/db
SECRET_KEY=<generate-secure-key>
ALLOWED_ORIGINS=https://yourdomain.com
```

**Building for Production**:
```bash
# Frontend
cd frontend
npm run build
# Output in: frontend/dist/

# Backend
cd backend
# Use a production WSGI server like gunicorn or uvicorn with workers
uvicorn production_main:app --host 0.0.0.0 --port 8001 --workers 4
```

---

## Troubleshooting

### Frontend Can't Connect to Backend

**Problem**: "ERR_CONNECTION_REFUSED" or "Failed to fetch"

**Solutions**:
1. Verify backend is running: `curl http://localhost:8001/health`
2. Check `VITE_API_BASE_URL` in `frontend/.env` matches backend PORT
3. Restart frontend dev server after changing `.env`
4. Check CORS settings in backend `.env` include frontend URL

### Port Already in Use

**Problem**: "Address already in use" error

**Solutions**:
1. Change `PORT` in backend `.env`
2. Update `VITE_API_BASE_URL` in frontend `.env` to match
3. Kill existing process:
   - Windows: `netstat -ano | findstr :8001` then `taskkill /PID <pid> /F`
   - Linux/Mac: `lsof -ti:8001 | xargs kill -9`

### CORS Errors

**Problem**: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Solutions**:
1. Add frontend URL to `ALLOWED_ORIGINS` in backend `.env`
2. Use comma-separated values (no spaces): `http://localhost:5173,http://localhost:3000`
3. Restart backend after changing CORS settings

### Configuration Not Applied

**Problem**: Changes to `.env` files not taking effect

**Solutions**:
1. **Frontend**: Restart dev server (`npm run dev`)
2. **Backend**: Restart the Python process
3. Verify the correct `.env` file is being loaded
4. Check for syntax errors in `.env` file (no quotes for most values)

### Hardcoded URLs

**Problem**: Code still using hardcoded URLs like `http://localhost:8001`

**Solutions**:
All frontend API calls should use the centralized API client:

```typescript
// ❌ Wrong
const response = await fetch('http://localhost:8001/articles');

// ✅ Correct
import api from '../lib/api';
const response = await api.get('/articles');
```

Files already updated:
- ✅ `frontend/src/pages/Dashboard.tsx`
- ✅ `frontend/src/pages/Articles.tsx`
- ✅ `frontend/src/pages/Search.tsx`
- ✅ `frontend/src/lib/api.ts`

---

## Security Best Practices

### For Production Deployment

1. **Generate Secure SECRET_KEY**:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Use HTTPS**:
   - Frontend: Deploy behind HTTPS
   - Backend: Use reverse proxy (nginx) with SSL/TLS
   - Update `VITE_API_BASE_URL` to use `https://`

3. **Database**:
   - Use PostgreSQL instead of SQLite
   - Use environment variables for credentials
   - Never commit database files

4. **CORS**:
   - Only allow specific domains
   - Don't use wildcards in production

5. **Environment Files**:
   - Never commit `.env` files with secrets
   - Use `.env.example` as template
   - Use secret management in cloud deployments

---

## Quick Reference

### Current Configuration

**Default Ports**:
- Frontend: `5173` (Vite dev server)
- Backend: `8001` (FastAPI/Uvicorn)
- Ollama: `11434` (LLM service)

**Default URLs**:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs
- Health Check: http://localhost:8001/health

### Environment File Priority

1. `.env.local` (if exists, highest priority)
2. `.env.[mode]` (e.g., `.env.production`)
3. `.env`

### Switching Environments

**Frontend**:
```bash
# Development
npm run dev  # Uses .env.development

# Production build
npm run build  # Uses .env.production
```

**Backend**:
```bash
# Copy the appropriate environment file
cp .env.development .env   # For development
cp .env.production .env    # For production
```
