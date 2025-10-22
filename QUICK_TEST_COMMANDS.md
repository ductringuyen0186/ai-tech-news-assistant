# Quick Test Commands for Render

## Replace with your actual Render backend URL:
```
https://your-backend-name.onrender.com
```

---

## ✅ Test 1: Health Check

```bash
curl https://your-backend-name.onrender.com/health
```

**Expected**: Status 200, JSON response with "healthy"

---

## ✅ Test 2: Trigger Ingestion (THE MAIN TEST)

```bash
curl -X POST https://your-backend-name.onrender.com/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"background": false}'
```

**Expected response**:
```json
{
  "message": "Ingestion completed: 30 articles saved",
  "background": false
}
```

**This means:**
- ✅ Fetched 30 articles from RSS
- ✅ Saved to database
- ✅ Ready to query

---

## ✅ Test 3: Check Stats

```bash
curl https://your-backend-name.onrender.com/api/ingest/stats
```

**Expected**: Shows 30 articles saved, success rate 100%

---

## ⚠️ Data Persistence Test

After ingestion completes:

1. **Manual restart in Render dashboard**:
   - Services → ai-tech-news-backend → More → Restart

2. **Then run**:
```bash
curl https://your-backend-name.onrender.com/api/ingest/stats
```

**If 30 articles still there**: ✅ Data persisted (PostgreSQL working)
**If 0 articles**: ❌ Data lost (ephemeral disk issue)

---

## 🐛 Troubleshooting

**Connection refused?**
- Backend still deploying, wait 2-3 minutes

**"Cannot GET /api/ingest"**
- Routes not registered, check backend logs

**"Internal server error"**
- Check Render logs for details

---

## 📊 Your Render Backend URL

Find it here:
1. Go to: https://dashboard.render.com/services
2. Click: ai-tech-news-backend
3. Look for: Service URL
4. Copy and replace in commands above

Example:
```
https://ai-tech-news-backend-xyz123.onrender.com
```

---

**Command to save in terminal**:
```bash
# Set your backend URL
$BACKEND="https://your-backend-name.onrender.com"

# Test health
curl $BACKEND/health

# Test ingestion
curl -X POST $BACKEND/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"background": false}'

# Check stats
curl $BACKEND/api/ingest/stats
```
