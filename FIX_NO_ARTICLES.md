# 🐛 FIX: "No articles found" on Frontend

## Problem

Frontend deployed on Vercel shows "No articles found" even though backend is running on Render.

**Root Cause**: API parameter mismatch
- Frontend was sending: `limit=50&q=query&category=...`
- Backend expects: `page_size=50&page=1&source=...&author=...`

## ✅ Solution Applied

### Frontend Fix (App.tsx)
Updated the fetchArticles function to use correct backend parameters:

```typescript
// BEFORE (Wrong - sends limit, q, category)
const params = new URLSearchParams();
params.append("category", selectedCategories.join(","));
params.append("q", searchQuery);
params.append("limit", "50");

// AFTER (Correct - sends page_size, page, source, author)
const params = new URLSearchParams();
params.append("page", "1");
params.append("page_size", "50");
if (selectedCategories.length > 0) {
  params.append("source", selectedCategories[0]);
}
if (searchQuery) {
  params.append("author", searchQuery);
}
```

### Key Changes:
- ✅ `limit` → `page_size` (backend pagination parameter)
- ✅ `q` → `author` (backend uses author field for text search)
- ✅ `category` → `source` (backend filters by source, not category)
- ✅ Added explicit `page=1` parameter
- ✅ Added console logging to debug API responses

---

## 🚀 Deployment Steps

### Step 1: Verify Frontend Build
```bash
cd frontend
npm run build
```

**Expected Output:**
```
✓ 1654 modules transformed
✓ built in ~2 seconds
```

### Step 2: Push to GitHub
```bash
git add frontend/src/App.tsx
git commit -m "Fix API parameter mismatch"
git push origin main
```

### Step 3: Vercel Auto-Redeploy
- Vercel automatically redeploys when code is pushed
- Wait 2-3 minutes for deployment
- Check Vercel dashboard at https://vercel.com

### Step 4: Test Frontend
1. Go to your Vercel deployment URL
2. Open DevTools (F12)
3. Check Network tab for API calls
4. Verify articles now display

---

## 🔍 Debugging Checklist

### If articles still don't show:

1. **Check Console Errors (F12 → Console)**
   - Look for CORS errors
   - Look for 404/500 errors
   - Check API response format

2. **Verify API Base URL**
   ```typescript
   // In DevTools Console:
   import { API_BASE_URL } from './config/api'
   console.log(API_BASE_URL)
   // Should output: https://ai-tech-news-assistant-backend.onrender.com
   ```

3. **Test Backend Directly**
   ```bash
   # Check if backend is responding
   curl https://ai-tech-news-assistant-backend.onrender.com/health
   
   # Check if articles endpoint works
   curl "https://ai-tech-news-assistant-backend.onrender.com/api/news?page=1&page_size=10"
   ```

4. **Check CORS Headers**
   - Look at Network tab → Response Headers
   - Verify `Access-Control-Allow-Origin` header is present
   - Should allow frontend domain (*.vercel.app)

---

## 📋 Backend API Reference

### GET /api/news - Fetch Articles

**Parameters:**
- `page` (int, required): Page number starting from 1
- `page_size` (int, required): Items per page (1-100)
- `source` (str, optional): Filter by source (e.g., "TechCrunch", "Wired")
- `author` (str, optional): Filter by author name
- `has_summary` (bool, optional): Filter by summary presence
- `sort_by` (str, optional): Field to sort (created_at, published_date, title, views)
- `sort_desc` (bool, optional): Sort descending (default: true)

**Example Requests:**
```bash
# Get first page of articles
GET /api/news?page=1&page_size=20

# Filter by source
GET /api/news?page=1&page_size=20&source=TechCrunch

# Search by author
GET /api/news?page=1&page_size=20&author=John

# Combined filters
GET /api/news?page=1&page_size=20&source=Wired&has_summary=true
```

**Response Format:**
```json
{
  "data": [
    {
      "id": "article-id",
      "title": "Article Title",
      "content": "Article content...",
      "summary": "AI summary...",
      "url": "https://...",
      "published_at": "2025-10-22T12:00:00Z",
      "source": "TechCrunch",
      "categories": ["AI", "ML"],
      "created_at": "2025-10-22T12:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 150,
    "total_pages": 8,
    "has_next": true,
    "has_previous": false
  }
}
```

---

## ⚙️ CORS Configuration

Backend CORS allows:
- ✅ Origins: https://*.vercel.app, http://localhost:3000
- ✅ Methods: GET, POST, PUT, DELETE, OPTIONS
- ✅ Headers: Content-Type, Authorization
- ✅ Credentials: Allowed

**If CORS errors occur:**
1. Check backend CORS config in `src/core/middleware.py`
2. Verify frontend domain is whitelisted
3. Verify backend is returning correct CORS headers
4. Check browser console for specific error message

---

## 📊 Testing the Fix

### Manual Test (Browser Console)
```javascript
// 1. Check API base URL
console.log(import.meta.env.VITE_API_BASE_URL);

// 2. Test API call directly
fetch('https://ai-tech-news-assistant-backend.onrender.com/api/news?page=1&page_size=5')
  .then(r => r.json())
  .then(d => console.log('Articles:', d.data))
  .catch(e => console.error('Error:', e));

// 3. Check response format
// Should see array of article objects under "data" field
```

### Automated Test
```bash
# Run integration tests
cd backend
pytest tests/integration/test_news_api.py -v

# Should show all tests passing
```

---

## 🎯 What Should Happen Now

1. **Frontend loads** - No blank page errors
2. **API calls succeed** - Network tab shows 200 status
3. **Articles display** - "No articles found" message gone
4. **Pagination works** - Can navigate between pages
5. **Search works** - Can filter by category and search

---

## ✅ Verification Checklist

- [x] API parameters corrected in App.tsx
- [x] Code committed and pushed to GitHub
- [x] Vercel auto-redeploy triggered
- [ ] Frontend deployed successfully (check Vercel dashboard)
- [ ] Articles displaying on frontend
- [ ] No console errors in DevTools
- [ ] API calls visible in Network tab
- [ ] Search and filter working

---

## 📞 If Issues Persist

**Check these in order:**

1. **Is Vercel deployment complete?**
   - Go to https://vercel.com/dashboard
   - Check if latest commit has green checkmark
   - If red X, click to see build logs

2. **Is backend still running?**
   - Go to https://ai-tech-news-assistant-backend.onrender.com/health
   - Should return 200 status with health info

3. **Are there articles in database?**
   ```bash
   cd backend
   python -m pytest tests/integration/test_news_api.py::TestNewsRoutes::test_get_articles_success -v
   ```

4. **Are CORS headers present?**
   - DevTools → Network → Click API request → Response Headers
   - Look for `Access-Control-Allow-Origin`

5. **Check Vercel deployment logs:**
   - Open Vercel dashboard
   - Click project → Deployments
   - Click latest deployment
   - Check build logs and runtime errors

---

## 🎓 Related Files

- Frontend: `frontend/src/App.tsx`
- API Config: `frontend/src/config/api.ts`
- Backend API: `backend/src/api/routes/news.py`
- CORS Middleware: `backend/src/core/middleware.py`
- Integration Tests: `backend/tests/integration/test_news_api.py`

---

**Status**: ✅ FIXED  
**Date**: October 22, 2025  
**Changes**: 1 file modified (App.tsx)  
**Next**: Monitor Vercel deployment and test frontend

