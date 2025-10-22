# Render Deployment: Article Persistence Analysis

## ⚠️ TL;DR - Direct Answer

**Current Question**: "If I pull article from source it gonna save in render?"

**Answer**: 
- ✅ **YES** - Articles save temporarily 
- ❌ **NO** - Articles don't persist permanently
- 💾 **Need PostgreSQL** - To make saves permanent

---

## 📊 Visual Comparison

### **CURRENT** (SQLite on Ephemeral Disk)

```
Timeline:
─────────────────────────────────────────────────────────────

t=0:00   POST /api/ingest
         ├─→ Fetch 30 articles from RSS ✅
         └─→ db.commit() to SQLite ✅

t=0:15   Articles visible in API
         └─→ GET /api/ingest/stats → 30 articles ✅

t=15:00  Container auto-restart (Render default)
         ├─→ Ephemeral disk WIPED
         └─→ SQLite file deleted ❌

t=15:01  GET /api/ingest/stats
         └─→ 0 articles (lost!) ❌

t=15:30  GET /health
         └─→ Still working ✅
         └─→ But database empty ❌
```

### **FIXED** (PostgreSQL on Persistent Server)

```
Timeline:
─────────────────────────────────────────────────────────────

t=0:00   POST /api/ingest
         ├─→ Fetch 30 articles from RSS ✅
         └─→ db.commit() to PostgreSQL ✅

t=0:15   Articles visible in API
         └─→ GET /api/ingest/stats → 30 articles ✅

t=15:00  Container auto-restart
         ├─→ Backend restarted
         ├─→ PostgreSQL database UNTOUCHED ✅
         └─→ Reconnects automatically ✅

t=15:01  GET /api/ingest/stats
         └─→ 30 articles STILL THERE ✅✅✅

t=1:00   Day passes...
t=7:00   Week passes...
t=30:00  Month passes...
         └─→ Articles still there! ✅
```

---

## 🔍 Technical Breakdown

### **How Current Setup Works (Broken)**

```python
# backend/main.py startup
from src.database.base import get_database_url

database_url = get_database_url()
# Returns: "sqlite:///./data/ai_news.db"
# ↑ File path on container disk

engine = create_engine(database_url)
# SQLite engine pointing to ephemeral disk
```

**Problem**:
```
Render Container Filesystem
├─→ / (root)
├─→ /app/ (application code)
│   ├─→ /backend/
│   ├─→ /frontend/
│   └─→ /data/  ← EPHEMERAL DISK ⚠️
│       └─→ ai_news.db (lost on restart)
└─→ /tmp/ (temporary storage)
```

**Result**: 
- ❌ Articles saved to ephemeral disk
- ❌ Disk deleted on restart
- ❌ No data persistence

### **How Fixed Setup Works (Persistent)**

```python
# backend/main.py startup (AFTER fix)
database_url = os.getenv("DATABASE_URL")
# Returns: "postgresql://user:pass@host/db"
# ↑ Connection to Render's PostgreSQL server

engine = create_engine(database_url)
# PostgreSQL engine pointing to persistent server
```

**How it works**:
```
Render Backend Container
├─→ Connect to PostgreSQL server
│   └─→ postgresql://ai-tech-news-db.onrender.com:5432/postgres
│
└─→ All db.commit() writes to PostgreSQL
    ├─→ Articles saved on server ✅
    ├─→ Survives container restart ✅
    ├─→ Survives redeployment ✅
    └─→ Persists forever ✅

PostgreSQL Server (Render Managed)
└─→ Persistent storage
    ├─→ Data backed up hourly
    ├─→ Data replicated
    └─→ Data lives permanently ✅
```

---

## 🔄 API Behavior: Current vs. Fixed

### **CURRENT (Broken) - After Ingestion**

```bash
# Time 0: Ingest articles
$ curl -X POST https://ai-backend.onrender.com/api/ingest
{
  "message": "Ingestion completed: 30 articles saved",
  "background": false
}

# Time 0-15 min: API works
$ curl https://ai-backend.onrender.com/api/ingest/stats
{
  "total_articles": 30,
  "total_sources": 5
}

# Time 15 min: Container restarts
$ curl https://ai-backend.onrender.com/api/ingest/stats
{
  "total_articles": 0,  # ← Data lost!
  "total_sources": 0
}
```

### **FIXED (Working) - After Ingestion**

```bash
# Time 0: Ingest articles
$ curl -X POST https://ai-backend.onrender.com/api/ingest
{
  "message": "Ingestion completed: 30 articles saved",
  "background": false
}

# Time 0-15 min: API works
$ curl https://ai-backend.onrender.com/api/ingest/stats
{
  "total_articles": 30,
  "total_sources": 5
}

# Time 15 min: Container restarts (DATA PERSISTS)
$ curl https://ai-backend.onrender.com/api/ingest/stats
{
  "total_articles": 30,  # ← Data still here!
  "total_sources": 5
}

# Time 1 week later: Data still there
$ curl https://ai-backend.onrender.com/api/ingest/stats
{
  "total_articles": 30,
  "total_sources": 5
}
```

---

## 🚀 What Needs to Happen

### **Current State**
```yaml
render.yaml:
├─ DATABASE_TYPE: (not set, defaults to sqlite)
├─ DATABASE_URL: (not set)
└─ Result: SQLite on ephemeral disk ❌
```

### **After Fix**
```yaml
render.yaml:
├─ DATABASE_TYPE: postgresql  ← Add this
├─ DATABASE_URL: (environment variable)
│  └─ Set in Render dashboard to PostgreSQL connection
└─ Result: PostgreSQL persistent storage ✅
```

---

## 📝 Implementation Checklist

### **Step 1: Create PostgreSQL** (2 minutes)
- [ ] Go to Render dashboard
- [ ] Create new PostgreSQL database
- [ ] Copy connection string

### **Step 2: Set Environment Variable** (1 minute)
- [ ] Go to Backend service → Environment
- [ ] Add `DATABASE_URL` = your PostgreSQL connection string
- [ ] Save and auto-redeploy

### **Step 3: Verify Connection** (2 minutes)
- [ ] Check backend logs
- [ ] Look for "Creating database engine"
- [ ] Test health check: `/health` returns 200

### **Step 4: Test Ingestion** (2 minutes)
- [ ] Call `POST /api/ingest`
- [ ] Response: "30 articles saved" ✅
- [ ] Call `GET /api/ingest/stats`
- [ ] Result: shows 30 articles

### **Step 5: Verify Persistence** (2 minutes)
- [ ] Restart backend in Render dashboard
- [ ] Call `GET /api/ingest/stats` again
- [ ] **Result should still show 30 articles** ✅

---

## 💡 Understanding the Difference

### **Ephemeral Disk** (Current)
```
Container starts
├─→ Empty ephemeral disk
├─→ Application initializes
├─→ Writes to disk happen here
└─→ Container stops/restarts
    └─→ Disk completely wiped
        └─→ All writes lost forever
```

**Analogy**: Writing on sand that gets washed away by waves

### **Persistent Database** (After fix)
```
Container starts
├─→ Connects to database server
├─→ Database persists on server
├─→ Writes go to server
└─→ Container stops/restarts
    └─→ Server still has data
        └─→ Reconnects and sees all data
```

**Analogy**: Writing in a book that survives even if you close it

---

## 🎯 Why This Matters

### **Use Case 1: Manual Ingestion**

**Current (Broken)**:
```
Monday:
├─→ POST /api/ingest
├─→ 30 articles saved
└─→ Can query articles ✅

Tuesday (container restarted):
├─→ GET /api/ingest/stats
└─→ 0 articles (lost) ❌
    └─→ Have to re-ingest ❌
```

**Fixed**:
```
Monday:
├─→ POST /api/ingest
├─→ 30 articles saved
└─→ Can query articles ✅

Tuesday (container restarted):
├─→ GET /api/ingest/stats
└─→ Still 30 articles (persisted) ✅
    └─→ Can query immediately ✅
```

### **Use Case 2: Automated Ingestion**

**Current (Broken)**:
```
Hourly job: POST /api/ingest
├─→ Fetch 50 new articles
├─→ Save to SQLite
└─→ Every 15 minutes: articles lost ❌
    └─→ Each restart wipes data ❌
    └─→ Only keeps data for 15 minutes max ❌
```

**Fixed**:
```
Hourly job: POST /api/ingest
├─→ Fetch 50 new articles
├─→ Save to PostgreSQL
└─→ Data persists forever ✅
    └─→ Hourly job accumulates articles ✅
    └─→ After 7 days: 7000 articles in DB ✅
    └─→ Frontend can query all of them ✅
```

---

## ✅ Solution Summary

| Aspect | Current | After PostgreSQL |
|--------|---------|-----------------|
| **API Save Works** | ✅ Yes | ✅ Yes |
| **Data Persists** | ❌ No (15 min max) | ✅ Yes (forever) |
| **Cost** | Free | $7/month |
| **Complexity** | Simple | Medium |
| **Reliability** | 0% | 99.9% |
| **Production Ready** | ❌ No | ✅ Yes |

---

## 🔗 Next Actions

1. **Read**: `RENDER_POSTGRESQL_SETUP.md` for step-by-step guide
2. **Do**: Create PostgreSQL on Render (5 minutes)
3. **Set**: DATABASE_URL environment variable (1 minute)
4. **Test**: Article persistence after restart (5 minutes)

---

**Current Status**: 
- ✅ render.yaml updated to support PostgreSQL
- ⏳ PostgreSQL not yet created on Render (your next step)
- ⏳ Awaiting DATABASE_URL configuration

**Estimated Total Time to Fix**: 15-20 minutes
