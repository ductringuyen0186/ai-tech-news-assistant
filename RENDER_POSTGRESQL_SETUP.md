# Render PostgreSQL Setup Guide

## 🚨 Current Issue

Your Render deployment **does NOT save articles persistently**:

```
Current Setup: SQLite on Render ephemeral disk
├─→ POST /api/ingest fetches articles ✅
├─→ Articles written to SQLite ✅
├─→ API returns "saved" ✅
└─→ Container restarts in 15 min → **ALL DATA LOST** ❌
```

**Result**: Every article pull is lost after restart.

---

## ✅ Solution: Add PostgreSQL to Render

### **Step 1: Create PostgreSQL Database on Render** (5 minutes)

1. Go to [https://dashboard.render.com/](https://dashboard.render.com/)
2. Click **New+** → **PostgreSQL**
3. Fill in details:
   ```
   Name: ai-tech-news-db
   Database: postgres (default)
   User: postgres
   Region: Oregon (same as backend)
   Plan: Basic ($7/month) or Free (if available)
   ```
4. Click **Create Database**
5. Wait 2-3 minutes for provisioning

### **Step 2: Get Connection String**

After database created:
1. Copy the **Internal Database URL**
   ```
   postgresql://postgres:XXXXXXXXXX@ai-tech-news-db.onrender.com:5432/postgres
   ```
2. Keep it safe - you'll need it

### **Step 3: Set Backend Environment Variable**

1. Go to **Render Dashboard** → **ai-tech-news-backend** service
2. Click **Environment**
3. Add new variable:
   ```
   Key: DATABASE_URL
   Value: postgresql://postgres:XXXXXXXXXX@ai-tech-news-db.onrender.com:5432/postgres
   ```
4. Click **Save** → Auto-redeploys backend

### **Step 4: Verify Connection**

After backend redeploys:
1. Check backend logs:
   ```
   render logs --tail=50
   ```
2. Look for:
   ```
   INFO - Creating database engine for: postgresql://...
   INFO - Database initialized successfully
   ```
3. Test with API:
   ```bash
   curl https://your-backend.onrender.com/health
   # Response: {"status": "healthy", ...}
   ```

### **Step 5: Test Article Ingestion**

```bash
# Trigger ingestion
curl -X POST https://your-backend.onrender.com/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"background": false}'

# Response:
# {
#   "message": "Ingestion completed: 30 articles saved",
#   "background": false
# }

# Verify persistence
curl https://your-backend.onrender.com/api/ingest/stats
# Response shows 30 articles saved
```

---

## 🔄 After PostgreSQL Setup

### **What Changes**

**Before (SQLite ephemeral disk):**
```
POST /api/ingest
├─→ Fetch RSS ✅
├─→ Save to SQLite ✅
├─→ Container restarts ⏰
└─→ ALL DATA LOST ❌
```

**After (PostgreSQL persistent):**
```
POST /api/ingest
├─→ Fetch RSS ✅
├─→ Save to PostgreSQL ✅
├─→ Container restarts ⏰
└─→ DATA PERSISTS ✅
├─→ Next API call sees data ✅
└─→ Articles permanently stored ✅
```

### **Data Flow**

```
RSS Sources (5)
    ↓
Backend (Render)
    ↓
PostgreSQL (Render)
    ↓
Articles persist forever
    ↓
Next restart/redeploy
    ↓
✅ Data still there
```

---

## 💾 Verify Data Persistence

### **After First Ingestion**

```bash
# Get stats
curl https://your-backend.onrender.com/api/ingest/stats

# Response:
{
  "total_articles": 30,
  "total_sources": 5,
  "total_categories": 8,
  "last_ingestion": "2025-10-22T10:14:30"
}
```

### **After Container Restart**

1. Manually restart in Render dashboard:
   ```
   Services → ai-tech-news-backend → More → Restart
   ```

2. Check stats again:
   ```bash
   curl https://your-backend.onrender.com/api/ingest/stats
   ```

3. **Expected**: Same 30 articles still there ✅

4. **If NOT fixed**: Only ~0 articles (data was lost) ❌

---

## 💰 Cost Analysis

| Option | Cost | Data Persistence | Best For |
|--------|------|------------------|----------|
| **SQLite (Current)** | Free | ❌ (lost on restart) | Testing only |
| **PostgreSQL Basic** | $7/month | ✅ (permanent) | Production |
| **PostgreSQL Standard** | $15/month | ✅ (high availability) | High traffic |
| **Self-hosted PG** | Free* | ✅ (if running) | Dev/hobby |

*Requires maintaining your own server

---

## 🔒 Security Notes

**After setting DATABASE_URL:**
1. Don't commit password to git ✅ (already set in Render env vars)
2. Use Internal Database URL (not public) ✅
3. Rotate password regularly (monthly recommended)
4. Monitor database usage in Render dashboard

---

## ⚡ Quick Troubleshooting

### **Issue: "Connection refused"**
```
Error: could not connect to server
```
**Solution**: Wait 2-3 minutes for database to provision, then restart backend

### **Issue: "no such table: articles"**
```
Error: relation "articles" does not exist
```
**Solution**: Backend needs to create schema. Check if init_db() is called on startup.
```python
# backend/main.py (should have):
from src.database import init_db
init_db()  # Create tables on startup
```

### **Issue: "Unknown database user"**
```
Error: FATAL: Ident authentication failed
```
**Solution**: Check DATABASE_URL is correct, copy again from Render dashboard

### **Issue: Data still lost after restart**
1. Verify DATABASE_URL is set:
   ```bash
   render env | grep DATABASE_URL
   ```
2. Check backend logs for connection errors:
   ```bash
   render logs --tail=100 | grep -i database
   ```
3. Restart backend:
   ```bash
   render restart
   ```

---

## 📋 Checklist

- [ ] PostgreSQL database created on Render
- [ ] Connection string copied
- [ ] DATABASE_URL environment variable set in backend
- [ ] Backend redeploy completed
- [ ] Health check passes (`/health` returns 200)
- [ ] POST /api/ingest works (returns "30 articles saved")
- [ ] GET /api/ingest/stats shows 30 articles
- [ ] Backend restarted manually
- [ ] Stats endpoint still shows 30 articles (data persisted!) ✅

---

## 🚀 Next Steps

After PostgreSQL is working:

1. **Set up automated ingestion**
   ```python
   # Option 1: Use FastAPI background tasks
   # Ingest hourly via scheduled task
   
   # Option 2: Use external scheduler (AWS EventBridge, etc.)
   # Trigger POST /api/ingest every 6 hours
   ```

2. **Monitor data growth**
   ```bash
   curl https://your-backend.onrender.com/api/ingest/stats
   # Monitor: total_articles increases over time
   ```

3. **Set up alerting**
   - Slack notifications on ingestion failure
   - Email on data loss
   - Uptime monitoring

4. **Backup strategy**
   - Render auto-backups PostgreSQL
   - Download backups monthly
   - Test restore process

---

## 📝 File Updates

Updated `deployment/render.yaml`:
```yaml
envVars:
  - key: DATABASE_TYPE
    value: postgresql
  - key: DATABASE_URL
    sync: false
    # Set in Render dashboard to:
    # postgresql://user:pass@host:5432/db
```

This tells the backend to:
- Use PostgreSQL instead of SQLite
- Read connection string from DATABASE_URL env var
- Connect to Render's managed database

---

**Status**: 
- ✅ render.yaml updated to support PostgreSQL
- ⏳ Next: Create PostgreSQL on Render dashboard
- ⏳ Then: Set DATABASE_URL environment variable
- ⏳ Finally: Redeploy and test

**Estimated Setup Time**: 10 minutes
