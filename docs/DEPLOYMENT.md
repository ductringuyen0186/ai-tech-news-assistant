# 🚀 Production Deployment Guide
# AI Tech News Assistant

## Quick Deploy Options

### Option 1: One-Click Cloud Deployment (Recommended)

#### Backend → Railway/Render
1. **Railway** (Recommended - Free tier with PostgreSQL)
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login and deploy
   railway login
   railway link
   railway up
   ```

2. **Render** (Alternative - Free tier)
   - Connect your GitHub repo to Render
   - Use the provided `render.yaml` configuration
   - Auto-deploys on git push

#### Frontend → Vercel
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy (from frontend/ directory)
cd frontend
vercel

# Update API URL in environment
vercel env add VITE_API_BASE_URL https://your-backend-url.railway.app
```

### Option 2: Docker Local/VPS Deployment

#### Quick Start
```bash
# Make deploy script executable
chmod +x deploy.sh

# Deploy everything locally
./deploy.sh

# Or deploy specific version
./deploy.sh v1.0.0 deploy
```

#### VPS Deployment
```bash
# Build and push to your registry
./deploy.sh latest prod

# On your VPS:
docker-compose -f docker-compose.prod.yml up -d
```

## Environment Configuration

### Backend Environment Variables
```env
# Required
ENVIRONMENT=production
CORS_ORIGINS=https://your-frontend-domain.vercel.app
DATABASE_URL=postgresql://... (auto-provided by Railway/Render)

# Optional
OPENAI_API_KEY=sk-...
REDIS_URL=redis://...
```

### Frontend Environment Variables  
```env
VITE_API_BASE_URL=https://your-backend-domain.railway.app
```

## Domain Setup

### Custom Domain (Optional)
1. **Backend**: Add custom domain in Railway/Render dashboard
2. **Frontend**: Add custom domain in Vercel dashboard  
3. **Update CORS**: Add your custom domain to `CORS_ORIGINS`

### SSL/HTTPS
- ✅ **Automatic**: Railway, Render, and Vercel provide free SSL
- ✅ **Custom domains**: SSL certificates auto-generated

## Monitoring & Health Checks

### Health Endpoints
- **Backend**: `https://your-backend-url/health`
- **Frontend**: `https://your-frontend-url/health`  

### Logging
- **Railway**: Built-in logs dashboard
- **Render**: Built-in logs viewer
- **Vercel**: Function logs and analytics

### Alerts (Optional)
```bash
# Add monitoring (optional)
# UptimeRobot, StatusCake, or similar for uptime monitoring
```

## Database Management

### Railway PostgreSQL (Recommended)
- ✅ **Automatic**: Database created and connected
- ✅ **Backups**: Daily automated backups
- ✅ **Migrations**: Auto-applied on deployment

### SQLite (Local/VPS)
- ✅ **Backups**: Automated daily backups to `./backups/`
- ✅ **Persistence**: Docker volume mounted
- ⚠️ **Scaling**: Limited to single instance

## Cost Estimation

### Free Tier (Perfect for MVP)
- **Railway**: Free $5/month credit (covers backend + database)  
- **Vercel**: Free (frontend hosting + CDN)
- **Total**: $0/month for reasonable usage

### Paid Scaling
- **Railway**: $5-20/month (backend + database)
- **Vercel**: $0-20/month (frontend)  
- **Total**: $5-40/month for production traffic

## Security Best Practices

### Environment Variables
- ✅ **Never commit**: Use `.env.production` template only
- ✅ **Use platform secrets**: Railway/Render/Vercel dashboards
- ✅ **Rotate keys**: Regular API key rotation

### CORS Configuration
```python
# Update backend CORS for production
CORS_ORIGINS=https://yourdomain.com,https://ai-tech-news.vercel.app
```

### Rate Limiting (Recommended)
```python
# Add to backend (already configured)
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

## Deployment Automation

### GitHub Actions (Included)
- ✅ **Auto-deploy**: Pushes to main trigger deployment
- ✅ **Testing**: Runs tests before deployment  
- ✅ **Notifications**: Deployment status updates

### Manual Deployment
```bash
# Local testing
docker-compose up -d

# Production deployment  
git push origin main  # Auto-deploys via GitHub Actions
```

## Troubleshooting

### Common Issues
1. **CORS Errors**: Check `CORS_ORIGINS` environment variable
2. **Database Connection**: Verify `DATABASE_URL` in production
3. **API Not Found**: Ensure backend URL is correct in frontend env

### Debug Commands
```bash
# Check service health
curl https://your-backend-url/health

# View logs
railway logs  # or render logs, docker-compose logs

# Test API connection  
curl https://your-backend-url/api/v1/news
```

## Success Checklist

### Pre-Deployment
- [ ] Environment variables configured
- [ ] CORS origins updated
- [ ] Database URL set (for cloud deployment)
- [ ] API keys added to platform secrets

### Post-Deployment  
- [ ] Backend health check passes
- [ ] Frontend loads correctly
- [ ] API requests work from frontend
- [ ] Database connection verified
- [ ] SSL certificates active

### Production Ready
- [ ] Custom domain configured (optional)
- [ ] Monitoring/alerts set up (optional)  
- [ ] Backup strategy in place
- [ ] Rate limiting configured
- [ ] Error tracking enabled (optional)

## 🎉 You're Live!

Once deployed, your AI Tech News Assistant will be accessible at:
- **Frontend**: `https://your-app.vercel.app`
- **Backend API**: `https://your-backend.railway.app`
- **API Docs**: `https://your-backend.railway.app/docs`

**Total deployment time**: ~15 minutes for cloud deployment! 🚀
