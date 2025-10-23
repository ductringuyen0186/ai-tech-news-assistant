# 🚀 Render Deployment Guide - Backend

## Prerequisites
- ✅ All 301 tests passing
- ✅ Code committed to GitHub (main branch)
- ✅ Render.com account with payment method

## Step-by-Step Deployment

### 1. Create PostgreSQL Database on Render

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **+ New** → **PostgreSQL**
3. Configure:
   - **Name**: `ai-tech-news-db`
   - **Database**: `aitech_db`
   - **User**: (auto-generated)
   - **Region**: Oregon (us-west)
   - **PostgreSQL Version**: 15
   - **Plan**: Free or Paid

4. After creation, copy the **Internal Database URL** or **External Database URL**
   - Format: `postgresql://user:password@host:5432/database`

### 2. Deploy FastAPI Backend

1. Click **+ New** → **Web Service**
2. Connect GitHub repository:
   - Select: `ductringuyen0186/ai-tech-news-assistant`
   - Branch: `main`

3. Configure Web Service:
   - **Name**: `ai-tech-news-backend`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 8000`
   - **Plan**: Starter ($7/month) or Free tier

4. Environment Variables:
   ```
   DATABASE_URL=postgresql://user:pass@host:5432/db
   ENVIRONMENT=production
   DEBUG=false
   PYTHONUNBUFFERED=1
   ```

5. Click **Create Web Service**

### 3. Verify Deployment

1. Wait for build to complete (3-5 minutes)
2. Check logs: Should see `✅ Application started successfully`
3. Test health endpoint:
   ```bash
   curl https://ai-tech-news-backend.onrender.com/health
   ```
   Expected response: `{"status":"healthy"}`

4. Monitor logs in Render dashboard for errors

### 4. Run Database Migrations (if needed)

1. In Render dashboard, go to Web Service → Shell
2. Run:
   ```bash
   alembic upgrade head
   ```

## Environment Variables to Set

| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | From PostgreSQL service | Required |
| `ENVIRONMENT` | `production` | Required |
| `DEBUG` | `false` | Security |
| `PYTHONUNBUFFERED` | `1` | Log streaming |
| `PORT` | `8000` | Auto-set by Render |

## Troubleshooting

### Build Failures
- Check Python 3.13 compatibility
- Verify requirements.txt dependencies
- Check build logs for specific errors

### Runtime Errors
- Check logs: `Logs` tab in Render dashboard
- Verify DATABASE_URL format
- Ensure database is accessible

### Health Check Failures
- Verify `/health` endpoint exists in `main.py`
- Check database connectivity
- Review application startup logs

## Backend URL Format

```
https://ai-tech-news-backend.onrender.com
```

Use this URL for frontend `VITE_API_BASE_URL` configuration.

## Next Steps

1. ✅ Backend deployed to Render
2. Deploy frontend to Vercel (see DEPLOY_VERCEL_GUIDE.md)
3. Update frontend `VITE_API_BASE_URL`
4. Run smoke tests

---

**Estimated Time**: 15-20 minutes  
**Cost**: Free tier or $7/month starter plan  
**Status**: Ready for manual deployment
