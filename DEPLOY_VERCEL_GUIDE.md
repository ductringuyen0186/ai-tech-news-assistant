# 🚀 Vercel Deployment Guide - Frontend

## Prerequisites
- ✅ Backend deployed on Render (have the URL ready)
- ✅ Vercel account connected to GitHub
- ✅ Code committed to GitHub (main branch)

## Step-by-Step Deployment

### 1. Deploy to Vercel

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository:
   - **Repository**: `ductringuyen0186/ai-tech-news-assistant`
   - Authorize GitHub if needed

3. Configure Project:
   - **Project Name**: `ai-tech-news-frontend` (or your choice)
   - **Root Directory**: `frontend/`
   - **Framework Preset**: `Vite`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm ci`

### 2. Set Environment Variables

In the Vercel dashboard:

```
VITE_API_BASE_URL=https://ai-tech-news-backend.onrender.com
```

This tells the frontend where to send API requests.

### 3. Deploy

Click **Deploy** - Vercel will:
1. Install dependencies
2. Build the React app
3. Deploy to Vercel's CDN
4. Provide a live URL

### 4. Verify Deployment

1. Wait for build to complete (2-3 minutes)
2. Check deployment logs for errors
3. Visit your Vercel URL (e.g., `https://ai-tech-news-frontend.vercel.app`)
4. Verify the app loads without errors

### 5. Test Frontend-Backend Connection

1. Open browser console (F12)
2. Look for any CORS errors or API errors
3. Try searching for articles (should fetch from backend)
4. Check Network tab to verify API calls to `VITE_API_BASE_URL`

## Environment Variable Format

```
VITE_API_BASE_URL=https://ai-tech-news-backend.onrender.com
```

**DO NOT** include trailing slash:
- ✅ Correct: `https://ai-tech-news-backend.onrender.com`
- ❌ Wrong: `https://ai-tech-news-backend.onrender.com/`

## Troubleshooting

### Build Failures
1. Check Node.js version: Should be 18+
2. Verify `npm run build` works locally
3. Check logs for missing dependencies

### CORS Errors
- Ensure backend has CORS middleware configured
- Verify `VITE_API_BASE_URL` is correct
- Check browser console for specific error messages

### API Connection Errors
- Verify `VITE_API_BASE_URL` environment variable is set
- Check backend is running on Render
- Test backend health: `curl https://api-url/health`

### Blank Page
- Check browser console for JavaScript errors
- Verify build completed successfully
- Clear cache and hard refresh

## Auto-Deploy Configuration

Vercel automatically deploys when:
1. You push to the main branch
2. Pull request is created (preview deployment)
3. Manual redeploy from dashboard

## Frontend URL Format

```
https://ai-tech-news-frontend.vercel.app
```

Or use a custom domain if configured.

## Advanced: Custom Domain (Optional)

1. In Vercel dashboard → Settings → Domains
2. Add your domain and follow DNS configuration
3. Automatic SSL/TLS certificate

## Next Steps

1. ✅ Frontend deployed to Vercel
2. ✅ Backend deployed to Render
3. Run smoke tests (see SMOKE_TESTS.md)
4. Monitor dashboards and logs

---

**Estimated Time**: 10-15 minutes  
**Cost**: Free tier available  
**Domains**: `*.vercel.app` (free) or custom domain

## Post-Deployment Checklist

- [ ] Frontend loads without errors
- [ ] API base URL configured correctly
- [ ] Can fetch news articles
- [ ] Search functionality works
- [ ] No CORS errors in console
- [ ] Backend health check passing
- [ ] Database connected on backend
