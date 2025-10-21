# 🚀 Deploying to Render with Groq (Option B)
## $7/Month Always-On Backend with FREE LLM

**Date:** October 21, 2025  
**Goal:** Deploy your AI Tech News Assistant backend to Render with Groq for fast, free LLM inference.

---

## 📋 Prerequisites

### 1. Get Groq API Key (FREE, No Credit Card)
```bash
# Step 1: Go to https://console.groq.com
# Step 2: Sign up with GitHub or email (FREE)
# Step 3: Go to "API Keys" section
# Step 4: Click "Create API Key"
# Step 5: Copy the key (starts with "gsk_...")
```

**Important:** Groq is FREE for portfolio usage:
- ✅ 30 requests/minute
- ✅ 500+ tokens/second (faster than GPT-4)
- ✅ No credit card required
- ✅ Perfect for demos

### 2. Create Render Account
```bash
# Go to https://render.com
# Sign up with GitHub (recommended)
# Free tier available
```

---

## 🎯 Deployment Architecture

```
┌─────────────────────────────────────────┐
│ Frontend (Vercel - FREE)                │
│ https://frontend-qwo8f66ka...vercel.app │
└────────────────┬────────────────────────┘
                 │
                 │ HTTP requests
                 ↓
┌─────────────────────────────────────────┐
│ Backend (Render - $7/mo)                │
│ https://your-app.onrender.com           │
│                                         │
│ - FastAPI app                           │
│ - Sentence Transformers (embeddings)    │
│ - SQLite database (persistent)          │
└────────────────┬────────────────────────┘
                 │
                 │ API calls
                 ↓
┌─────────────────────────────────────────┐
│ Groq API (FREE)                         │
│ https://api.groq.com                    │
│                                         │
│ - Llama 3.2 model                       │
│ - Ultra-fast inference                  │
│ - No cost for portfolio usage           │
└─────────────────────────────────────────┘
```

---

## 📝 Step-by-Step Deployment

### Step 1: Update Backend Configuration

Your backend is already configured! I've added:
- ✅ `backend/llm/groq_provider.py` - Groq integration
- ✅ `backend/llm/factory.py` - Auto provider selection
- ✅ `backend/utils/config.py` - Groq settings

### Step 2: Create `.env` for Production

Create `backend/.env.production`:

```bash
# Application
ENVIRONMENT=production
DEBUG=false

# Server
PORT=8000

# CORS - Add your Vercel URL
ALLOWED_ORIGINS=https://frontend-qwo8f66ka-ductringuyen0186s-projects.vercel.app,http://localhost:3000

# LLM Provider (Groq for production)
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_actual_api_key_here
GROQ_MODEL=llama-3.2-3b-preview

# Fallback to Ollama for local dev
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Embeddings (runs on Render)
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_BATCH_SIZE=16

# Database
DATABASE_URL=sqlite:///./data/news_assistant.db

# Logging
LOG_LEVEL=INFO
```

### Step 3: Deploy to Render

#### Option A: Using Render Dashboard (Easiest)

1. **Go to Render Dashboard**
   - Visit https://dashboard.render.com
   - Click "New +" → "Web Service"

2. **Connect GitHub**
   - Select your repository: `ductringuyen0186/ai-tech-news-assistant`
   - Click "Connect"

3. **Configure Service**
   ```
   Name: ai-tech-news-backend
   Region: Oregon (US West) - closest to Vercel
   Branch: main (or your current branch)
   Root Directory: backend
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python src/main.py
   ```

4. **Select Plan**
   - Choose "Starter" ($7/month)
   - ✅ Always-on (no sleeping)
   - ✅ 512MB RAM (enough for embeddings)
   - ✅ Persistent disk for SQLite

5. **Add Environment Variables**
   Click "Environment" tab and add these:
   ```
   ENVIRONMENT=production
   DEBUG=false
   PORT=8000
   ALLOWED_ORIGINS=https://frontend-qwo8f66ka-ductringuyen0186s-projects.vercel.app
   LLM_PROVIDER=groq
   GROQ_API_KEY=gsk_your_actual_api_key_here
   GROQ_MODEL=llama-3.2-3b-preview
   EMBEDDING_MODEL=all-MiniLM-L6-v2
   LOG_LEVEL=INFO
   ```

6. **Add Persistent Disk** (Important for SQLite)
   - Go to "Disks" tab
   - Click "Add Disk"
   - Mount Path: `/opt/render/project/src/data`
   - Size: 1GB (free tier)

7. **Deploy!**
   - Click "Create Web Service"
   - Wait 5-10 minutes for build
   - You'll get a URL: `https://your-app.onrender.com`

#### Option B: Using render.yaml (Automated)

Your `deployment/render.yaml` is already configured. Just need to update it:

```yaml
services:
  # Backend service
  - type: web
    name: ai-tech-news-backend
    runtime: python
    plan: starter  # $7/month
    buildCommand: pip install -r requirements.txt
    startCommand: python src/main.py
    rootDir: backend
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: LLM_PROVIDER
        value: groq
      - key: GROQ_API_KEY
        sync: false  # Set manually in dashboard
      - key: GROQ_MODEL
        value: llama-3.2-3b-preview
      - key: PORT
        value: 8000
    disk:
      name: data
      mountPath: /opt/render/project/src/data
      sizeGB: 1
```

Then:
```bash
# Push to GitHub
git add .
git commit -m "Add Groq provider and Render config"
git push

# In Render dashboard:
# 1. Connect repo
# 2. Render auto-detects render.yaml
# 3. Click "Apply"
# 4. Set GROQ_API_KEY manually
```

### Step 4: Verify Backend Deployment

Once deployed, test these endpoints:

```bash
# 1. Health check
curl https://your-app.onrender.com/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-10-21T...",
  "version": "1.0.0",
  "llm_provider": "groq",
  "llm_available": true
}

# 2. Test summarization
curl -X POST https://your-app.onrender.com/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "Artificial intelligence is transforming the tech industry..."}'

# Expected response:
{
  "success": true,
  "summary": "AI is revolutionizing technology...",
  "keywords": ["AI", "ML", "technology"],
  "model": "llama-3.2-3b-preview",
  "provider": "groq"
}
```

### Step 5: Connect Frontend to Backend

Update your Vercel environment variable:

```bash
cd frontend
vercel env add VITE_API_BASE_URL production

# When prompted, enter:
# https://your-app.onrender.com

# Redeploy frontend
vercel --prod
```

Or use Vercel dashboard:
1. Go to https://vercel.com/ductringuyen0186s-projects/frontend/settings/environment-variables
2. Add:
   - Name: `VITE_API_BASE_URL`
   - Value: `https://your-app.onrender.com`
   - Environment: Production
3. Redeploy

### Step 6: Test End-to-End

1. **Open your frontend:**
   https://frontend-qwo8f66ka-ductringuyen0186s-projects.vercel.app

2. **Try these features:**
   - ✅ Browse articles
   - ✅ Search articles (semantic search)
   - ✅ Click "Summarize" on an article
   - ✅ Use AI chat (if implemented)

3. **Check browser console:**
   - Should see successful API calls
   - No CORS errors
   - Fast responses from Groq

---

## 💰 Cost Breakdown

### Monthly Costs
- **Frontend (Vercel):** $0
- **Backend (Render Starter):** $7
- **LLM (Groq API):** $0 (free tier: 30 req/min)
- **Embeddings:** $0 (runs on your Render server)
- **Database:** $0 (SQLite on persistent disk)

**Total: $7/month**

### Cost Optimization Tips
1. **Groq free tier is generous:**
   - 30 requests/minute = 43,200 requests/day
   - More than enough for portfolio demos

2. **If you hit Groq limits:**
   - Implement simple caching (save summaries in DB)
   - Add rate limiting on frontend
   - Upgrade Groq plan ($0.27 per million tokens)

3. **If $7/month is too much:**
   - Use Render free tier ($0, but sleeps after 15 min)
   - Or just run locally with Docker Compose

---

## 🎯 How This Solves Your Question

> "How does Ollama work in deployed backend?"

**Answer:** It doesn't! That's why we use Groq instead:

### Problem with Ollama on Render:
```
❌ Ollama needs GPU for fast inference
❌ Render free tier has no GPU
❌ CPU-only Ollama = 30-60 seconds per request
❌ Model download on every cold start (1-7GB)
❌ High memory usage crashes free tier
```

### Solution with Groq:
```
✅ Groq runs on their infrastructure (not yours)
✅ Ultra-fast: 500+ tokens/second
✅ FREE tier: 30 requests/minute
✅ No model downloads needed
✅ Works perfectly on any hosting
✅ API calls from your backend
```

### Architecture Comparison:

**Ollama (Local Only):**
```
Your Computer
  ↓
Ollama (running locally)
  ↓
Model (loaded in RAM)
  ↓
Inference on your CPU/GPU
```

**Groq (Production):**
```
Your Render Server
  ↓
HTTP Request to Groq API
  ↓
Groq's LPU (Language Processing Unit)
  ↓
Ultra-fast inference
  ↓
Response to your server
  ↓
Response to frontend
```

---

## 🔧 Troubleshooting

### Backend won't start
```bash
# Check logs in Render dashboard
# Common issues:
1. Missing GROQ_API_KEY → Add in environment variables
2. Wrong start command → Should be: python src/main.py
3. Requirements install failed → Check requirements.txt

# Fix: Update environment variables and redeploy
```

### CORS errors in frontend
```bash
# Update backend ALLOWED_ORIGINS
ALLOWED_ORIGINS=https://frontend-qwo8f66ka-ductringuyen0186s-projects.vercel.app

# Redeploy backend
```

### Groq API errors
```bash
# Check API key is valid
curl -H "Authorization: Bearer gsk_your_key" \
  https://api.groq.com/openai/v1/models

# If 401 Unauthorized:
# 1. Regenerate API key at console.groq.com
# 2. Update GROQ_API_KEY in Render
# 3. Redeploy
```

### Slow responses
```bash
# Check which provider is being used
curl https://your-app.onrender.com/health

# Should see: "llm_provider": "groq"
# If "ollama" → Groq API key not configured
# If "mock" → No provider available
```

---

## ✅ Success Checklist

After deployment, verify:

- [ ] Backend health check returns 200
- [ ] `/health` shows `"llm_provider": "groq"`
- [ ] Frontend loads without errors
- [ ] Can browse articles
- [ ] Semantic search works
- [ ] Article summarization works (click "Summarize")
- [ ] No CORS errors in browser console
- [ ] Response times < 2 seconds
- [ ] Groq free tier not exceeded (check console.groq.com)

---

## 🎉 You're Done!

Your portfolio project is now:
- ✅ **Fully deployed** (frontend + backend)
- ✅ **Always-on** (no sleeping with $7/mo plan)
- ✅ **Fast AI** (Groq = 500+ tokens/second)
- ✅ **Free LLM** (Groq free tier)
- ✅ **Production-ready** (proper architecture)
- ✅ **Cost-effective** ($7/month total)

**Next steps:**
1. Test all features
2. Record a 2-min demo video
3. Update README with live links
4. Share on LinkedIn!

---

## 📚 Additional Resources

- **Groq Console:** https://console.groq.com
- **Groq Docs:** https://console.groq.com/docs
- **Render Docs:** https://render.com/docs
- **Your Vercel Dashboard:** https://vercel.com/ductringuyen0186s-projects
- **FastAPI Deployment:** https://fastapi.tiangolo.com/deployment/

---

Need help? Check the troubleshooting section or review your Render/Groq logs!
