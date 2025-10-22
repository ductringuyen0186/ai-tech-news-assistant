# Deploy to Render and Test Ingestion

## 🚀 Deployment Status

✅ **Latest changes pushed to GitHub**
- Commit: `82fdcef`
- Changes: IngestionService working, database models fixed, render.yaml updated

✅ **Render auto-deploy enabled**
- Auto-deploys on git push: YES
- Should be deploying now...

---

## ⏳ Wait for Deployment (3-5 minutes)

### **Option 1: Check Render Dashboard** (Recommended)

1. Go to: https://dashboard.render.com/
2. Click on: **ai-tech-news-backend** service
3. Look for:
   - Green checkmark = Deployed ✅
   - Spinning icon = Deploying ⏳
   - Red X = Failed ❌

4. When green ✅, proceed to testing

### **Option 2: Check Service URL**

```bash
# Try to access the health endpoint
curl https://ai-tech-news-backend.onrender.com/health

# Expected response (after deployment complete):
# {"status": "healthy", "timestamp": "...", "version": "2.0.0"}

# If not deployed yet:
# Error: connection refused or 503 Service Unavailable
```

---

## 🧪 Test Ingestion on Render (After Deployment)

### **Step 1: Trigger Ingestion**

```bash
curl -X POST https://ai-tech-news-backend.onrender.com/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"background": false}'
```

**Expected response:**
```json
{
  "message": "Ingestion completed: 30 articles saved",
  "job_id": null,
  "background": false
}
```

### **Step 2: Verify Articles Saved**

```bash
curl https://ai-tech-news-backend.onrender.com/api/ingest/stats
```

**Expected response:**
```json
{
  "status": "completed",
  "result": {
    "status": "completed",
    "start_time": "2025-10-22T10:00:00",
    "end_time": "2025-10-22T10:00:30",
    "duration_seconds": 30,
    "total_feeds": 5,
    "total_articles_found": 30,
    "total_articles_saved": 30,
    "duplicates_skipped": 0,
    "errors": 0,
    "success_rate": 100.0,
    "sources_processed": {
      "Hacker News": 30
    }
  }
}
```

### **Step 3: Check Persistence (CRITICAL!)**

Wait 15 seconds, then check if data persists:

```bash
curl https://ai-tech-news-backend.onrender.com/api/ingest/stats
```

**Expected**:
- Same 30 articles still there ✅ (if PostgreSQL is configured)
- OR 0 articles (if still using SQLite - means data lost) ❌

---

## ⚠️ Important Notes

### **About Data Persistence**

**Current Issue**: 
- Articles WILL save initially ✅
- BUT they'll be lost on next container restart ❌
- Because: Using ephemeral disk (not PostgreSQL)

**To fix**:
1. Create PostgreSQL on Render ($7/month)
2. Set `DATABASE_URL` environment variable
3. Redeploy
4. Then articles persist forever ✅

See: `RENDER_POSTGRESQL_SETUP.md` for detailed steps

---

## 🔍 Test Checklist

- [ ] Render deployment showing green checkmark (deployed)
- [ ] Health check passes: `curl /health` returns 200
- [ ] POST /api/ingest returns "30 articles saved"
- [ ] GET /api/ingest/stats shows 30 articles
- [ ] Test article query works (if implemented)
- [ ] Frontend can query backend (if testing frontend)

---

## 📊 Expected Timeline

```
Now:
├─ Latest commit pushed ✅
├─ Render receives webhook
└─ Auto-deploy starts ⏳

In 1-2 min:
├─ Backend building
└─ Installing dependencies ⏳

In 3-5 min total:
├─ Backend deployed ✅
├─ Health check passing ✅
└─ Ready to test ✅

Your testing:
├─ POST /api/ingest
├─ 30 seconds to fetch & save
├─ GET /api/ingest/stats
└─ Review results ✅
```

---

## 🚨 If Deployment Fails

### **Issue: "Connection refused" or 503**

**Possible causes:**
1. Still deploying - wait 2 more minutes
2. Build failed - check Render logs
3. Wrong service name

**Fix:**
1. Go to Render dashboard
2. Click service: **ai-tech-news-backend**
3. Check build logs (scroll down)
4. Look for error messages

### **Issue: "Cannot GET /health"**

**Means:** Backend deployed but routes not working

**Fix:**
1. Check backend/main.py has health route
2. Check no syntax errors
3. View Render logs for runtime errors

---

## 📱 How to Monitor Deployment

### **Via Render Dashboard** (Easiest)

1. Go to: https://dashboard.render.com/services
2. Click: **ai-tech-news-backend**
3. Watch "Logs" section in real-time
4. Look for:
   ```
   ✅ Starting deployment...
   ✅ Building...
   ✅ Starting service...
   ✅ Service healthy
   ```

### **Via CLI** (if you have render CLI)

```bash
render logs --tail=50 --service=ai-tech-news-backend
```

---

## 🧬 Test Ingestion Endpoint Details

### **Endpoint**: `POST /api/ingest`

**Parameters**:
```json
{
  "sources": null,           // optional custom sources
  "background": false        // true=async, false=wait for completion
}
```

**Responses**:

**Success (foreground)**:
```json
{
  "message": "Ingestion completed: 30 articles saved",
  "job_id": null,
  "background": false
}
```

**Success (background)**:
```json
{
  "message": "Ingestion started in background",
  "job_id": "bg_ingest_001",
  "background": true
}
```

**Error**:
```json
{
  "detail": "Ingestion failed: ...",
  "status_code": 500
}
```

---

## 📊 Endpoint: `GET /api/ingest/stats`

Returns latest ingestion statistics:

```json
{
  "status": "completed",
  "result": {
    "status": "completed",
    "start_time": "2025-10-22T10:00:00Z",
    "end_time": "2025-10-22T10:00:30Z",
    "duration_seconds": 30.5,
    "total_feeds": 5,
    "total_articles_found": 30,
    "total_articles_saved": 30,
    "duplicates_skipped": 0,
    "errors": 0,
    "error_details": [],
    "sources_processed": {
      "Hacker News": 30,
      "TechCrunch": 0,
      "Ars Technica": 0,
      "The Verge": 0,
      "MIT Technology Review": 0
    },
    "success_rate": 100.0
  }
}
```

---

## 🎯 Next Steps After Testing

**If ingestion works** ✅:
1. ✅ Great! Core functionality verified
2. ⏳ Next: Set up PostgreSQL for persistence
3. ⏳ Then: Test that data persists after restart

**If ingestion fails** ❌:
1. Check error message in response
2. View Render logs for details
3. Common issues:
   - HTTP timeout (feeds taking too long to fetch)
   - Database schema not created
   - Import errors in backend

---

## 📝 Summary

```
Your Action: git push origin main ✅ (Already done)
Render Action: Auto-deploy (should be deploying now)
Your Next: 
  1. Wait 3-5 minutes for deployment
  2. Test: curl /api/ingest (POST request)
  3. Verify: curl /api/ingest/stats (should show 30 articles)
  4. Check persistence: Data still there after restart?
```

---

**Estimated Time**:
- Deployment: 3-5 minutes
- Testing: 2-3 minutes
- **Total: 5-8 minutes**

**Let me know when**:
1. Deployment shows green ✅
2. You run the test
3. What results you get

I can help troubleshoot if anything fails!
