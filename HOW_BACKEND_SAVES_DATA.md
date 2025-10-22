# How Deployed Backend Saves Data

## 🔄 Complete Data Flow: RSS → Database

```
┌─────────────────────────────────────────────────────────────────┐
│                     REQUEST FLOW                                │
└─────────────────────────────────────────────────────────────────┘

1. API REQUEST (HTTP POST)
   └─→ POST /api/ingest
       │
       └─→ IngestRequest {
               sources: optional custom feeds,
               background: true/false
           }

2. ENDPOINT HANDLER (ingestion.py)
   │
   ├─→ trigger_ingestion() endpoint
   │   │
   │   └─→ Create IngestionService(db)
   │       │
   │       ├─→ Determine if background or foreground
   │       │
   │       └─→ If background: add_task to BackgroundTasks
   │           └─→ Returns immediately
   │
   │       If foreground: ingest_all(sources)
   │           └─→ Waits for completion
   │           └─→ Returns result directly

3. INGESTION SERVICE (ingestion_service.py)
   │
   ├─→ ingest_all(sources)
   │   │
   │   ├─→ Set status = RUNNING
   │   ├─→ Record start_time
   │   │
   │   └─→ For each feed in sources (or DEFAULT_FEEDS):
   │       │
   │       └─→ _ingest_feed(feed_config)
   │           │
   │           ├─→ Fetch RSS with httpx.Client
   │           │   └─→ GET https://feeds.feedburner.com/oreilly/radar
   │           │   └─→ GET https://techcrunch.com/feed/
   │           │   └─→ etc.
   │           │
   │           ├─→ Parse with feedparser.parse()
   │           │
   │           ├─→ For each entry in feed:
   │           │   │
   │           │   └─→ _process_entry(entry)
   │           │       │
   │           │       ├─→ Extract: title, url, content, author, date
   │           │       │
   │           │       ├─→ Check duplicate:
   │           │       │   db.query(Article).filter(Article.url == url)
   │           │       │   └─→ If exists: skip (duplicates_skipped++)
   │           │       │
   │           │       ├─→ If new article:
   │           │       │   │
   │           │       │   ├─→ Get/create Category
   │           │       │   │   db.query(Category).filter(name == category)
   │           │       │   │   └─→ If not exists: create new
   │           │       │   │
   │           │       │   ├─→ Get/create Source
   │           │       │   │   db.query(Source).filter(name == source)
   │           │       │   │   └─→ If not exists: create new
   │           │       │   │
   │           │       │   ├─→ Create Article object:
   │           │       │   │   article = Article(
   │           │       │   │       title=title[:500],
   │           │       │   │       url=url[:1000],
   │           │       │   │       content=description,
   │           │       │   │       author=author,
   │           │       │   │       published_at=date,
   │           │       │   │       source_id=source.id,
   │           │       │   │       categories=[category]
   │           │       │   │   )
   │           │       │   │
   │           │       │   ├─→ Add to session:
   │           │       │   │   db.add(article)
   │           │       │   │   └─→ STAGED in memory (NOT saved yet)
   │           │       │   │
   │           │       │   └─→ Increment saved counter
   │           │
   │           └─→ Update source last_scraped timestamp
   │
   ├─→ After all feeds processed:
   │   │
   │   ├─→ COMMIT ALL CHANGES
   │   │   db.commit()  ← THIS IS KEY!
   │   │   │
   │   │   └─→ All staged articles → persisted to database
   │   │       └─→ SQLite file OR PostgreSQL
   │   │
   │   ├─→ Set status = COMPLETED or PARTIAL
   │   ├─→ Record end_time
   │   │
   │   └─→ Return IngestionResult
   │       ├─→ status: "completed"
   │       ├─→ total_articles_saved: 30
   │       ├─→ duplicates_skipped: 0
   │       ├─→ errors: 0
   │       └─→ success_rate: 100%

4. DATABASE PERSISTENCE
   │
   ├─→ SQLAlchemy generates SQL INSERT statements:
   │   │
   │   ├─→ INSERT INTO sources (name, url, ...) VALUES (...)
   │   │
   │   ├─→ INSERT INTO categories (name, slug, ...) VALUES (...)
   │   │
   │   ├─→ INSERT INTO articles (title, url, content, ...) VALUES (...)
   │   │
   │   └─→ INSERT INTO article_categories (article_id, category_id) VALUES (...)
   │
   ├─→ Execute against database:
   │   │
   │   ├─→ For SQLite deployment:
   │   │   └─→ Write to ./data/ai_news.db file
   │   │       └─→ File saved on persistent volume
   │   │
   │   └─→ For PostgreSQL deployment:
   │       └─→ Write to PostgreSQL server
   │           └─→ Data persisted on database server
   │
   └─→ Return results to client

```

---

## 🗄️ Database Save Mechanism (SQLAlchemy Transaction)

### Step 1: **Staging** (In-Memory)
```python
# Inside _process_entry()
article = Article(
    title="New AI Breakthrough",
    url="https://example.com/article",
    content="Article text...",
    source_id=1,
    published_at=datetime.now()
)
db.add(article)  # ← Added to session, NOT saved yet
# Article is in SQLAlchemy session identity map
```

### Step 2: **Flushing** (Transaction Prepared)
```python
# Happens automatically when needed
db.flush()  # ← Generates SQL but doesn't commit
# INSERT INTO articles (...) VALUES (...)
```

### Step 3: **Committing** (Persisted)
```python
# After all entries processed from all feeds
db.commit()  # ← PERSISTS to database file/server
# SQLite: Written to ./data/ai_news.db
# PostgreSQL: Stored in database server
```

### Step 4: **Error Handling** (Rollback if Fails)
```python
try:
    # Process and add articles
    db.commit()
except Exception as e:
    db.rollback()  # ← Undo all changes
    raise
```

---

## 📊 Data Flow Diagram

```
RSS Feeds (5 sources)
    ↓
feedparser.parse() ← Parse XML/Atom
    ↓
30 entries extracted
    ↓
For each entry:
├─→ Check duplicate (query database)
├─→ Get/create category (query database)
├─→ Get/create source (query database)
├─→ Create Article object (in memory)
└─→ db.add(article) ← Stage in session
    ↓
All articles staged in db.session
    ↓
db.commit() ← THE CRITICAL STEP
    ↓
SQLAlchemy generates & executes SQL
    ↓
INSERT statements executed
    ↓
✅ Data written to:
   - SQLite: ./data/ai_news.db
   - PostgreSQL: database server
```

---

## 🚀 Deployment-Specific Save Behavior

### **Docker Compose Deployment**
```yaml
# docker-compose.yml
services:
  backend:
    volumes:
      - backend_data:/app/data  ← Persistent volume
    environment:
      - DATABASE_URL=sqlite:///app/data/news.db

# On container:
# 1. SQLite file: /app/data/news.db
# 2. Mounted to: backend_data volume
# 3. Persisted on host: Docker volume
# 4. Survives container restart: YES ✅
```

**Data persists because:**
- ✅ Database file is in a Docker volume
- ✅ Volume persists even if container stops
- ✅ Multiple containers can share volume
- ✅ Backed up automatically (backup service)

### **Render.com Deployment (Free Tier)**
```yaml
# render.yaml
services:
  ai-tech-news-backend:
    env: python
    # Default: SQLite on ephemeral disk
    # DATABASE_URL=sqlite:///./data/news.db
```

**⚠️ Data does NOT persist because:**
- ❌ Ephemeral disk = temporary file storage
- ❌ Data lost when container restarts
- ❌ New deployment = new disk
- ❌ No volume mounting option

**Solution:**
```yaml
# Use PostgreSQL instead (paid tier required)
services:
  postgres:
    plan: basic_256mb  # $7/month
    
  backend:
    environment:
      DATABASE_URL=postgresql://user:pass@host/db
```

### **Render.com Deployment (Paid Tier with PostgreSQL)**
```yaml
# render.yaml with PostgreSQL
services:
  postgres:
    plan: basic_256mb
    region: oregon
    
  backend:
    environment:
      DATABASE_URL=postgresql://user:pass@render.onrender.com/ai_news
```

**Data persists because:**
- ✅ PostgreSQL managed by Render
- ✅ Data stored on persistent database server
- ✅ Survives all redeployments
- ✅ Automatic backups by Render

---

## 🔍 Actual Save Code Execution

### When API Called: `POST /api/ingest`

```python
# File: src/api/routes/ingestion.py
@router.post("/")
async def trigger_ingestion(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    db=Depends(get_db)  # ← Get database session dependency
):
    ingestion_service = IngestionService(db)  # ← Pass database session
    
    # Either:
    # 1. Background: add_task(_run_ingestion, ...)
    # 2. Foreground: result = ingestion_service.ingest_all(request.sources)
    
    result = ingestion_service.ingest_all(request.sources)
    # ↑ This returns IngestionResult with saved count
```

### Inside `ingest_all()`:

```python
# File: src/services/ingestion_service.py
def ingest_all(self, sources=None) -> IngestionResult:
    # ... process all feeds ...
    
    # THE CRITICAL LINE:
    self.db.commit()  # ← Persist all articles to database
    
    # After this line:
    # ✅ All 30 articles are saved
    # ✅ SQLite file updated (if using SQLite)
    # ✅ PostgreSQL rows inserted (if using PostgreSQL)
    # ✅ Cannot be undone (transaction committed)
    
    return self.result
```

---

## 💾 Where Data Lives After Save

### Development (Local Machine)
```
File: ./backend/data/ai_news.db
├─→ SQLite database file
├─→ Size: ~1-5MB for typical articles
├─→ Persists on disk
└─→ Query with: sqlite3 ./data/ai_news.db
```

### Production (Docker)
```
Docker Volume: backend_data
├─→ Location on host: /var/lib/docker/volumes/backend_data/
├─→ Inside container: /app/data/news.db
├─→ Persists across restarts
└─→ Backed up daily to ./backups/
```

### Production (Render - Paid)
```
PostgreSQL Server (Render Managed)
├─→ Host: ai-tech-news-db.onrender.com
├─→ Database: ai_news
├─→ User: postgres
├─→ Password: (environment variable)
├─→ Persists on Render servers
└─→ Automatic backups every 24 hours
```

---

## ✅ Verification Steps

### After Ingestion Completes

**1. Check API Response:**
```bash
curl -X POST http://localhost:8000/api/ingest
# Response:
# {
#   "message": "Ingestion completed: 30 articles saved",
#   "background": false
# }
```

**2. Query Database Directly:**
```bash
# SQLite
sqlite3 ./data/ai_news.db "SELECT COUNT(*) FROM articles;"
# Output: 30

# PostgreSQL
psql postgresql://user:pass@host/db -c "SELECT COUNT(*) FROM articles;"
# Output: 30
```

**3. Check Database File Size:**
```bash
# SQLite file size increases
ls -lh ./data/ai_news.db
# -rw-r--r--  1 user  staff  2.5M Oct 22 10:15 ./data/ai_news.db
```

**4. Get Status:**
```bash
curl http://localhost:8000/api/ingest/status
# Response:
# {
#   "status": "completed",
#   "result": {
#     "status": "completed",
#     "total_articles_saved": 30,
#     "duplicates_skipped": 0,
#     "errors": 0,
#     "success_rate": 100.0
#   }
# }
```

---

## 🔄 Transactional Safety

### What Happens If Save Fails

```python
try:
    # Process entries
    db.add(article1)
    db.add(article2)
    db.add(article3)
    
    # Attempt to commit
    db.commit()  # ← If THIS fails...
    
except Exception as e:
    # ...all changes are ROLLED BACK
    db.rollback()
    # article1, article2, article3 NOT saved
    # Database remains unchanged
    # State preserved: all-or-nothing
```

### Transaction Isolation

```
Request 1:
├─→ Process feeds
├─→ Add 30 articles to session
└─→ db.commit()
    ↓
    ✅ 30 articles persisted
    
Request 2 (simultaneous):
├─→ Reads database
└─→ Sees Request 1's data ONLY after commit
```

---

## 📈 Performance Considerations

### Batch Processing vs. Individual Saves

**❌ BAD** (Slow - 30 commits):
```python
for article in articles:
    db.add(article)
    db.commit()  # Commit after each article
    # 30 commits = 30 database writes
```

**✅ GOOD** (Fast - 1 commit):
```python
for article in articles:
    db.add(article)
db.commit()  # One commit for all
# 1 commit = 1 batch write
# ~100x faster
```

**Current Implementation**: ✅ Uses batch commit (1 commit for all articles)

---

## 🎯 Summary: How Deployed Backend Saves Data

1. **Request arrives** → POST /api/ingest
2. **API endpoint** creates IngestionService with database session
3. **Service fetches** RSS feeds (5 sources, 30 articles)
4. **For each article:**
   - Check if duplicate (query DB)
   - Extract metadata (title, URL, content, author, date)
   - Create Article object (in-memory)
   - db.add(article) to session
5. **After all articles staged:**
   - db.commit() ← PERSISTS all to database
6. **Data persisted to:**
   - SQLite: ./data/ai_news.db (or Docker volume)
   - PostgreSQL: Render database server (if paid tier)
7. **Return result** with save statistics (30 articles saved, 100% success)

**Key Point**: All articles are added to session first, then committed in **ONE transaction** for efficiency and data safety.

---

**Last Updated**: October 22, 2025
**Status**: ✅ Production-ready, verified working
