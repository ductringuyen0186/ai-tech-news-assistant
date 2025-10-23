# 🧪 Smoke Testing Guide

## Overview

After deploying to Render (backend) and Vercel (frontend), run these tests to verify everything is working correctly.

## Prerequisites

- ✅ Backend deployed on Render
- ✅ Frontend deployed on Vercel
- ✅ Database configured on Render
- ✅ Environment variables set

## 1. Backend Health Checks

### Test 1.1: Backend Accessibility

```bash
# Replace with your Render URL
curl https://ai-tech-news-backend.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-06T12:00:00Z",
  "version": "2.0.0"
}
```

### Test 1.2: Database Connection

```bash
curl https://ai-tech-news-backend.onrender.com/health/detailed
```

Expected: `components.database` should be `"connected"`

### Test 1.3: API Endpoints Available

```bash
curl https://ai-tech-news-backend.onrender.com/docs
```

Should return OpenAPI/Swagger documentation.

## 2. Frontend Health Checks

### Test 2.1: Frontend Loads

1. Navigate to your Vercel URL in browser
2. Verify page loads without blank screen
3. Check browser console (F12) - should be no critical errors

### Test 2.2: Verify Environment Variables

Open browser console and run:
```javascript
console.log(import.meta.env.VITE_API_BASE_URL)
```

Should show your backend URL.

## 3. API Integration Tests

### Test 3.1: Fetch News Articles

```bash
curl "https://ai-tech-news-backend.onrender.com/api/news?limit=5"
```

Expected: Array of articles with titles, content, URLs

### Test 3.2: Search Articles

```bash
curl -X POST "https://ai-tech-news-backend.onrender.com/api/search/hybrid" \
  -H "Content-Type: application/json" \
  -d '{"query":"artificial intelligence","limit":5}'
```

Expected: Search results matching query

### Test 3.3: Get Article Details

First, get an article ID from Test 3.1, then:

```bash
curl "https://ai-tech-news-backend.onrender.com/api/news/{article_id}"
```

Expected: Full article details

## 4. Frontend Integration Tests

### Test 4.1: Load Articles in UI

1. Navigate to frontend URL
2. Wait for articles to load
3. Verify article cards appear with:
   - Title
   - Source
   - Date
   - Summary/Content preview

### Test 4.2: Search Functionality

1. Use search bar to search for "AI"
2. Verify results appear (should call backend API)
3. Check Network tab → should see API calls to backend

### Test 4.3: Click Article

1. Click "Read Article" button
2. Should open article in new tab (external link)
3. No console errors

## 5. CORS and Network Tests

### Test 5.1: Check CORS Headers

```bash
curl -i https://ai-tech-news-backend.onrender.com/api/news?limit=1
```

Look for header: `access-control-allow-origin: *` or your Vercel domain

### Test 5.2: Monitor Network Traffic

1. Open frontend on Vercel
2. Open DevTools → Network tab
3. Perform an action (search, load articles)
4. Verify API requests to backend succeed (status 200, not CORS errors)

## 6. Database Tests

### Test 6.1: Data Persistence

1. Add/modify data via API
2. Refresh frontend
3. Verify data persists

### Test 6.2: Connection Pooling

1. Make rapid requests:
```bash
for i in {1..50}; do curl -s https://api-url/api/news?limit=1 > /dev/null; done
```

Should complete without connection errors.

## 7. Performance Tests

### Test 7.1: Load Time

- Frontend should load in < 2 seconds
- API should respond in < 500ms

### Test 7.2: Large Result Set

```bash
curl "https://ai-tech-news-backend.onrender.com/api/news?limit=100"
```

Should handle large queries gracefully.

## 8. Error Handling Tests

### Test 8.1: Invalid Parameters

```bash
curl "https://ai-tech-news-backend.onrender.com/api/news?limit=99999"
```

Should return 400/422 error, not 500.

### Test 8.2: Missing Required Fields

```bash
curl -X POST "https://ai-tech-news-backend.onrender.com/api/search/hybrid" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Should return 422 validation error with helpful message.

### Test 8.3: Invalid JSON

```bash
curl -X POST "https://api-url/api/search/hybrid" \
  -H "Content-Type: application/json" \
  -d '{invalid json}'
```

Should return 400 bad request.

## 9. Logging and Monitoring

### Test 9.1: Backend Logs

1. Go to Render dashboard → Logs
2. Perform API calls
3. Verify requests appear in logs
4. Check for any ERROR or WARNING messages

### Test 9.2: Frontend Errors

1. Open browser console
2. Perform frontend actions
3. Should see no red errors
4. Warnings are acceptable (deprecations, etc.)

## 10. Post-Deployment Verification Checklist

- [ ] Backend health endpoint returns 200
- [ ] Frontend loads without blank page
- [ ] Can fetch articles from API
- [ ] Can search articles
- [ ] No CORS errors in console
- [ ] No database connection errors in logs
- [ ] Articles display in frontend UI
- [ ] Search results appear when searching
- [ ] External links work correctly
- [ ] Load times are acceptable (< 2 sec)

## Troubleshooting

### Frontend shows blank page
1. Check browser console for errors
2. Verify `VITE_API_BASE_URL` is set
3. Check Vercel build logs

### CORS errors in console
1. Verify backend `VITE_API_BASE_URL` is correct
2. Check backend CORS configuration
3. Ensure backend is responding

### API calls fail with 500
1. Check Render backend logs
2. Verify database is connected
3. Check environment variables

### Articles don't load
1. Verify API endpoint exists
2. Check database has data
3. Verify pagination parameters

## Success Criteria

✅ All 10 tests passing = **Production Ready**

Proceed to monitoring and maintenance phase.

---

**Time to Complete**: 15-20 minutes  
**Difficulty**: Easy  
**Success Rate Target**: 100%
