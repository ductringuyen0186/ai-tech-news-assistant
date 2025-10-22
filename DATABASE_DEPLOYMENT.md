# Database Deployment Strategy

## 🏗️ Current Architecture

### Development
- **Database**: SQLite (file-based)
- **Location**: `./data/articles.db`
- **Initialization**: Auto-created by `init_db()` on first run
- **No setup needed** - Just run the app

### Production Deployment

#### Option 1: Docker Compose (Local/Self-Hosted)
```bash
# Start all services (backend, frontend, redis, backup)
docker-compose up -d

# Services:
# - Backend API: http://localhost:8000
# - Frontend: http://localhost:3000
# - Redis: localhost:6379
# - SQLite Database: /app/data/news.db (in container volume)
# - Auto Backups: Daily backups to ./backups/
```

**Configuration** (`docker-compose.yml`):
```yaml
environment:
  - ENVIRONMENT=production
  - DEBUG=false
  - DATABASE_URL=sqlite:///app/data/news.db
volumes:
  - backend_data:/app/data          # Persistent data
  - backend_logs:/app/logs          # Application logs
  - redis_data:/data                # Redis persistence
```

**Features**:
- ✅ Health checks every 30 seconds
- ✅ Auto-restart on failure
- ✅ Daily SQLite backups (7-day retention)
- ✅ Redis caching service
- ✅ Networked services (internal communication)

#### Option 2: Render.com (Cloud Platform)
```yaml
# render.yaml configuration
services:
  ai-tech-news-backend:
    type: web
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
    healthCheckPath: /health
    
  ai-tech-news-frontend:
    type: web (static)
    buildCommand: npm install && npm run build
    staticPublishPath: dist
```

**Deployment**:
```bash
# Push to GitHub → Render auto-deploys
git push origin main

# Or deploy manually:
render deploy
```

**Features**:
- ✅ Auto-deploys on git push
- ✅ CI/CD pipeline included
- ✅ HTTPS/SSL automatic
- ✅ PostgreSQL optional (paid tier)
- ✅ Environment variables managed securely

---

## 🗄️ Database Options by Deployment

| Environment | Database | Configuration | Persistence |
|-------------|----------|---------------|-------------|
| **Development** | SQLite | `./data/articles.db` | Local file |
| **Docker (Local)** | SQLite | Volume mount | `backend_data` volume |
| **Render (Free)** | SQLite | Ephemeral disk | ⚠️ Lost on restart |
| **Render (Paid)** | PostgreSQL | `DATABASE_URL` env var | Managed by Render |

---

## 🔄 Database Initialization Flow

### On Application Startup

1. **Configuration Loaded** (`src/core/config.py`)
   - Check `DATABASE_TYPE` (sqlite/postgresql)
   - Load `DATABASE_URL` from env or use default
   - Verify credentials and connection

2. **Engine Created** (`src/database/base.py`)
   ```python
   engine = create_engine(
       database_url,
       pool_size=5,
       max_overflow=10,
       timeout=30
   )
   ```

3. **Tables Created** (`init_db()` function)
   ```python
   from src.database import Base, engine
   Base.metadata.create_all(engine)
   ```
   - Creates all SQLAlchemy models
   - Creates indices
   - Creates foreign keys

4. **Ready for Operations**
   - API endpoints can accept requests
   - Ingestion service can save articles
   - Queries can run

---

## 📋 Database Schema

**Tables Created**:
1. `users` - User accounts (reserved for future auth)
2. `sources` - RSS feed sources (HackerNews, Reddit, etc.)
3. `articles` - News articles (title, content, URL, metadata)
4. `categories` - Tech categories (AI, ML, DevOps, etc.)
5. `article_categories` - Many-to-many join table
6. `embeddings` - Vector embeddings for semantic search

**Indices**:
- `articles.url` (unique)
- `articles.published_at` (for sorting)
- `articles.source_id` (for filtering)
- `sources.name` (for lookups)

---

## 🚀 Deployment Commands

### Docker Compose
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Backup database
docker-compose exec backup ls -lh /backups/

# Access SQLite directly
docker-compose exec backend sqlite3 /app/data/news.db "SELECT COUNT(*) FROM articles;"
```

### Render.com
```bash
# Deploy via git push (auto-deploys)
git push origin main

# Check deployment status
render deploy status

# View logs
render logs --tail=100

# Redeploy specific service
render redeploy --service=ai-tech-news-backend
```

### Local Development
```bash
# Init database (automatic on startup)
python -c "from src.database import init_db; init_db()"

# Run migrations (if using Alembic)
alembic upgrade head

# Check database
sqlite3 ./data/articles.db "SELECT COUNT(*) FROM articles;"
```

---

## 🔒 Database Migration Strategy

**For SQLite** (no migration needed):
- SQLAlchemy auto-creates schema on startup
- Use Alembic only if you need version control

**For PostgreSQL** (production):
```bash
# Generate migration
alembic revision --autogenerate -m "add user preferences table"

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

**Migration File**: `alembic/versions/001_create_initial_schema.py`

---

## 📊 Database Backup Strategy

### Docker Compose Auto-Backup
- ✅ Daily backups at midnight
- ✅ Stored in `./backups/` directory
- ✅ 7-day retention (older files auto-deleted)
- ✅ Command: `sqlite3 backup` native tool

### Manual Backup
```bash
# SQLite
sqlite3 ./data/articles.db ".backup ./backups/backup_$(date +%Y%m%d_%H%M%S).db"

# PostgreSQL
pg_dump postgresql://user:pass@host/db > backup.sql
```

### Restore from Backup
```bash
# SQLite
sqlite3 ./data/articles.db ".restore ./backups/backup_20251022_120000.db"

# PostgreSQL
psql postgresql://user:pass@host/db < backup.sql
```

---

## 🛠️ Configuration Reference

### Environment Variables

```bash
# Database Type
DATABASE_TYPE=sqlite              # or 'postgresql'

# SQLite (Development)
DATABASE_URL=sqlite:///./data/articles.db
SQLITE_DATABASE_PATH=./data/articles.db

# PostgreSQL (Production)
DATABASE_URL=postgresql://user:password@localhost:5432/ai_news

# Connection Pool
DATABASE_POOL_SIZE=5              # Connections in pool
DATABASE_MAX_OVERFLOW=10          # Extra connections when needed
DATABASE_TIMEOUT=30               # Query timeout (seconds)
```

### Application Environment
```bash
ENVIRONMENT=production            # or 'development', 'staging'
DEBUG=false                        # Disable debug mode
CORS_ORIGINS=https://your-domain.com,http://localhost:3000
```

---

## ✅ Deployment Checklist

- [ ] Database type selected (SQLite for dev/docker, PostgreSQL for production)
- [ ] `DATABASE_URL` configured and tested
- [ ] `init_db()` called or migrations applied
- [ ] Database tables verified
- [ ] Backup strategy in place
- [ ] Health checks configured
- [ ] Connection pooling tuned for load
- [ ] Logging enabled for database queries
- [ ] Environment variables secured (no secrets in code)

---

## 📈 Scaling Considerations

**SQLite** → **PostgreSQL** Migration:
1. Set up PostgreSQL instance
2. Change `DATABASE_TYPE=postgresql`
3. Set `DATABASE_URL=postgresql://...`
4. Run `alembic upgrade head` to create schema
5. Migrate existing data (if any)
6. Test thoroughly
7. Deploy

**Performance Optimization**:
- Increase `DATABASE_POOL_SIZE` for high concurrency
- Add indices on frequently queried columns
- Use Redis caching for hot data
- Implement read replicas for PostgreSQL
- Monitor slow queries with logging

---

**Last Updated**: October 22, 2025
**Current State**: ✅ Production-ready with SQLite (dev) and PostgreSQL support
