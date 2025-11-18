# 🚀 DEPLOYMENT GUIDE - PRODUCTION READY

**Status**: ✅ All code ready for deployment  
**Date**: November 17, 2025

---

## 📋 Pre-Deployment Checklist

- ✅ All 301 backend tests passing
- ✅ Frontend builds successfully (332 KB)
- ✅ Git repository clean and pushed
- ✅ Vercel CLI logged in
- ✅ render.yaml fixed to use correct startup command

---

## 🎯 DEPLOYMENT STEPS

### **PHASE 1: Backend on Render (20 min)**

#### 1️⃣ Create PostgreSQL Database

1. Go to: https://dashboard.render.com/
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   ```
   Name: ai-tech-news-db
   Database: ai_tech_news
   Region: Oregon (US West) or closest to you
   Plan: Free (Starter $7/mo for production)
   ```
4. Click **"Create Database"**
5. ⏳ Wait 2-3 minutes
6. **📋 COPY "Internal Database URL"** from database dashboard

#### 2️⃣ Deploy Backend Web Service

1. Click **"New +"** → **"Web Service"**
2. Select **"Build and deploy from a Git repository"**
3. Connect to GitHub: **`ductringuyen0186/ai-tech-news-assistant`**
4. Configure:
   ```
   Name: ai-tech-news-backend
   Region: Same as database (Oregon)
   Branch: main
   Root Directory: backend
   Runtime: Python 3
   Build Command: pip install --upgrade pip && pip install -r requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
   Instance Type: Free
   ```

5. **Environment Variables** (click "Advanced"):
   ```
   DATABASE_URL = <paste Internal Database URL from step 1>
   ENVIRONMENT = production
   DEBUG = false
   CORS_ORIGINS = https://*.vercel.app,http://localhost:5173
   ```
   
   Optional (if you have these):
   ```
   GROQ_API_KEY = <your-groq-api-key>
   OPENAI_API_KEY = <your-openai-key>
   ```

6. Click **"Create Web Service"**
7. ⏳ Wait 5-7 minutes for deployment
8. **📋 COPY backend URL**: `https://ai-tech-news-backend-XXXX.onrender.com`

#### 3️⃣ Verify Backend

Test the health endpoint:
```bash
curl https://your-backend-url.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-17T...",
  "version": "2.0.0"
}
```

Test news endpoint:
```bash
curl https://your-backend-url.onrender.com/api/news?page=1&page_size=10
```

---

### **PHASE 2: Frontend on Vercel (10 min)**

#### 4️⃣ Update Environment Variable

**IMPORTANT**: Replace the backend URL in frontend/.env.production

Edit `frontend/.env.production`:
```
VITE_API_BASE_URL=<your-actual-backend-url-from-step-2>
```

Example:
```
VITE_API_BASE_URL=https://ai-tech-news-backend-abc123.onrender.com
```

#### 5️⃣ Deploy to Vercel

**Option A: Using CLI (Current Terminal)**
```bash
cd frontend
vercel --prod
```

Follow prompts:
- **Set up and deploy?** → Yes
- **Which scope?** → Your account
- **Link to existing project?** → No
- **Project name?** → ai-tech-news-assistant (or custom)
- **Directory?** → ./ (current directory)
- **Override settings?** → No

⏳ Wait 3-5 minutes for deployment

**Option B: Using GitHub Integration**
1. Go to: https://vercel.com/new
2. Import repository: `ductringuyen0186/ai-tech-news-assistant`
3. Configure:
   ```
   Framework Preset: Vite
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: build
   ```
4. Environment Variables:
   ```
   VITE_API_BASE_URL = <your-backend-url>
   ```
5. Click "Deploy"

#### 6️⃣ Verify Frontend

1. Vercel will provide deployment URL: `https://ai-tech-news-assistant-XXXX.vercel.app`
2. Open in browser
3. Check console for any errors
4. Test functionality:
   - ✅ Home page loads
   - ✅ News feed displays (may be empty - need to seed data)
   - ✅ Search works
   - ✅ No CORS errors

---

### **PHASE 3: Seed Database (5 min)**

#### 7️⃣ Seed Sample Articles

**Option A: Using Render Shell**
1. Go to backend service in Render dashboard
2. Click "Shell" tab
3. Run:
   ```bash
   cd backend
   python scripts/seed_articles.py
   ```

**Option B: Using Local Script with Production DB**
1. Copy production DATABASE_URL
2. Set local environment variable:
   ```bash
   $env:DATABASE_URL="<production-database-url>"
   python backend/scripts/seed_articles.py
   ```

#### 8️⃣ Verify Data

Test API again:
```bash
curl https://your-backend-url.onrender.com/api/news?page=1&page_size=10
```

Should return 8 sample articles now.

Refresh frontend - articles should appear!

---

## ✅ POST-DEPLOYMENT CHECKLIST

- [ ] Backend health endpoint returns 200
- [ ] Backend /api/news returns articles
- [ ] Frontend loads without errors
- [ ] Frontend displays articles
- [ ] Search functionality works
- [ ] No CORS errors in browser console
- [ ] Backend logs show no errors (check Render dashboard)

---

## 🔧 UPDATE BACKEND CORS ORIGINS

Once frontend is deployed, update backend environment variables:

1. Go to Render dashboard → Backend service
2. Environment tab
3. Update `CORS_ORIGINS`:
   ```
   https://your-actual-frontend-url.vercel.app
   ```
4. Save and redeploy

---

## 🎉 YOUR DEPLOYMENT URLS

**Backend**: `https://______________________.onrender.com`  
**Frontend**: `https://______________________.vercel.app`  
**Database**: PostgreSQL on Render (internal)

---

## 🐛 TROUBLESHOOTING

### Backend Issues

**"Application failed to start"**
- Check logs in Render dashboard
- Verify DATABASE_URL is correct
- Check Python version compatibility

**"Database connection failed"**
- Verify DATABASE_URL format: `postgresql://user:pass@host:5432/db`
- Check database is running
- Check network connectivity

**"Import errors"**
- Check requirements.txt has all dependencies
- Verify Python 3.11+ compatibility
- Check build logs

### Frontend Issues

**"Failed to fetch"**
- Check VITE_API_BASE_URL is correct
- Verify backend is running
- Check CORS configuration

**"CORS policy error"**
- Update backend CORS_ORIGINS to include frontend domain
- Redeploy backend after CORS update

**"Articles not loading"**
- Verify backend /api/news endpoint works
- Check database has articles (run seed script)
- Check browser console for errors

---

## 📊 MONITORING

### Render Dashboard
- View logs: Backend service → "Logs" tab
- Check metrics: CPU, memory, requests
- Database stats: Database → "Metrics"

### Vercel Dashboard
- Analytics: Deployment → "Analytics"
- Function logs: Deployment → "Functions"
- Performance: Core Web Vitals

---

## 🚀 NEXT STEPS AFTER DEPLOYMENT

1. **Monitor for 24 hours**
   - Check error rates
   - Review logs
   - Test all features

2. **Set up monitoring** (optional)
   - Add Sentry for error tracking
   - Set up uptime monitoring (UptimeRobot)
   - Configure alerting

3. **Optimize**
   - Review slow queries
   - Add caching if needed
   - Optimize bundle size

4. **Add features**
   - Implement authentication
   - Add more data sources
   - Enhance AI capabilities

---

## 💰 COST ESTIMATE

**Free Tier**:
- Render PostgreSQL: Free (500 MB, expires in 90 days)
- Render Web Service: Free (750 hours/month, sleeps after 15 min inactivity)
- Vercel: Free (unlimited deployments)
- **Total**: $0/month

**Production Tier**:
- Render PostgreSQL Starter: $7/month (256 MB RAM)
- Render Web Service Starter: $7/month (512 MB RAM, always on)
- Vercel Pro: $20/month (optional, for teams)
- **Total**: $14-34/month

---

**Need help?** Check logs in Render/Vercel dashboards or refer to:
- `DEPLOY_RENDER_GUIDE.md`
- `DEPLOY_VERCEL_GUIDE.md`
- `SMOKE_TESTS.md`
