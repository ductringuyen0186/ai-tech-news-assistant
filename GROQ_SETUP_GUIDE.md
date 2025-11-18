# 🚀 Groq LLM Integration Guide

## Overview

**Groq** provides ultra-fast LLM inference using their custom LPU (Language Processing Unit) chips. Perfect for portfolio projects with generous free tier and blazing-fast speeds (500+ tokens/second).

### Why Groq?

✅ **Free Tier**: 30 requests/minute, no credit card required  
✅ **Ultra-Fast**: 500+ tokens/second (faster than GPT-4)  
✅ **Easy Setup**: OpenAI-compatible API  
✅ **Production Ready**: Used by thousands of developers  
✅ **No GPU Needed**: Cloud-based inference

---

## 📋 Quick Start (5 minutes)

### Step 1: Get Your Free API Key

1. Go to: https://console.groq.com
2. Sign up with GitHub or email (free, no credit card)
3. Navigate to: **API Keys** → **Create API Key**
4. Copy your key (starts with `gsk_...`)

### Step 2: Configure Backend

**Local Development:**
```bash
cd backend
# Edit .env file
nano .env  # or code .env
```

Add your Groq API key:
```bash
# LLM Configuration
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_actual_api_key_here
GROQ_MODEL=llama-3.2-3b-preview
```

**Production (Render):**
1. Go to: https://dashboard.render.com
2. Select your backend service: `ai-tech-news-assistant-backend`
3. Go to **Environment** tab
4. Add environment variables:
   ```
   LLM_PROVIDER = groq
   GROQ_API_KEY = gsk_your_actual_api_key_here
   GROQ_MODEL = llama-3.2-3b-preview
   ```
5. Click **Save Changes** (will trigger redeploy)

### Step 3: Test It Works

**Test API endpoint:**
```bash
# Test summarization (replace with actual article text)
curl -X POST "https://ai-tech-news-assistant-backend.onrender.com/api/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Artificial intelligence continues to advance rapidly. Recent breakthroughs in large language models have enabled new applications in natural language processing, code generation, and creative writing. Companies are racing to deploy AI solutions across industries.",
    "provider": "groq"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "summary": "Recent AI breakthroughs in large language models enable new applications in NLP, code generation, and creative writing, with companies racing to deploy solutions across industries.",
  "keywords": ["AI", "model", "algorithm"],
  "model": "llama-3.2-3b-preview",
  "provider": "groq",
  "tokens_used": 245
}
```

---

## 🔧 Available Models

Groq supports multiple models with different speed/quality tradeoffs:

| Model | Speed | Quality | Use Case |
|-------|-------|---------|----------|
| `llama-3.2-1b-preview` | ⚡⚡⚡ Fastest | Good | Quick summaries, simple tasks |
| `llama-3.2-3b-preview` | ⚡⚡ Very Fast | Better | **Recommended for most use cases** |
| `llama3-8b-8192` | ⚡ Fast | High | Detailed analysis, complex tasks |
| `llama3-70b-8192` | Normal | Highest | Production-grade quality |
| `mixtral-8x7b-32768` | Fast | High | Long context tasks |

**Recommendation**: Start with `llama-3.2-3b-preview` (balance of speed and quality)

---

## 📊 Rate Limits (Free Tier)

- **Requests**: 30 per minute
- **Tokens**: Unlimited on free tier
- **Context Window**: Up to 32,768 tokens (model dependent)

**Pro tip**: For portfolio projects, free tier is more than enough!

---

## 🛠️ Integration Points

### 1. Article Summarization API

**Endpoint**: `POST /api/summarize`

**Usage:**
```bash
# Summarize by article ID (from database)
curl -X POST "http://localhost:8000/api/summarize?article_id=1&provider=groq"

# Summarize by URL
curl -X POST "http://localhost:8000/api/summarize?url=https://techcrunch.com/article&provider=groq"

# Summarize raw text
curl -X POST "http://localhost:8000/api/summarize" \
  -H "Content-Type: application/json" \
  -d '{"text": "Your article text here...", "provider": "groq"}'
```

### 2. Frontend Integration

The frontend can call the summarization API when users click "Summarize" button:

```typescript
// frontend/src/components/NewsCard.tsx
const handleSummarize = async (articleId: string) => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/summarize?article_id=${articleId}&provider=groq`,
      { method: 'POST' }
    );
    const data = await response.json();
    
    if (data.success) {
      // Display summary to user
      setSummary(data.summary);
    }
  } catch (error) {
    console.error('Summarization failed:', error);
  }
};
```

### 3. Chat/Ask AI Feature

**Endpoint**: `POST /api/chat` (future implementation)

For conversational AI features like "Ask AI about this article":

```python
# backend/api/routes.py
@router.post("/chat", tags=["AI"])
async def chat_with_ai(messages: List[Dict[str, str]]):
    """AI chat endpoint using Groq"""
    from llm.factory import get_llm_provider
    
    provider = await get_llm_provider()
    result = await provider.chat(messages)
    
    return result
```

---

## 🧪 Testing Groq Integration

### Local Testing

1. **Start backend with Groq enabled:**
   ```bash
   cd backend
   # Make sure .env has GROQ_API_KEY set
   python main.py
   ```

2. **Test summarization:**
   ```bash
   # Test with sample text
   curl -X POST "http://localhost:8000/api/summarize" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Test article about AI and machine learning...",
       "provider": "groq"
     }'
   ```

3. **Check logs:**
   ```bash
   # Should see: "✅ Using Groq provider (configured)"
   ```

### Production Testing

```bash
# Test production backend
curl -X POST "https://ai-tech-news-assistant-backend.onrender.com/api/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Sample article text...",
    "provider": "groq"
  }'
```

---

## 🐛 Troubleshooting

### Issue: "Groq API key not configured"

**Solution**: Check environment variables
```bash
# Local
cat backend/.env | grep GROQ

# Production (Render)
# Check dashboard → Environment variables
```

### Issue: "Groq API returned 401 Unauthorized"

**Solution**: API key is invalid or expired
- Go to https://console.groq.com/keys
- Delete old key and create new one
- Update `.env` and redeploy

### Issue: "Rate limit exceeded"

**Solution**: You've hit 30 requests/minute
- Wait 60 seconds
- Consider implementing caching
- Upgrade to Groq Pro if needed (but free tier should be enough)

### Issue: "Module 'groq_provider' not found"

**Solution**: Import error
```bash
cd backend
pip install -r requirements.txt
# Make sure httpx is installed
pip install httpx
```

---

## 📈 Production Best Practices

### 1. Error Handling

The integration already includes proper error handling:
- API timeouts (30 seconds default)
- Rate limiting detection
- Automatic fallback to mock provider
- Detailed error logging

### 2. Caching

Consider adding caching for repeated summaries:

```python
# Future enhancement
from functools import lru_cache

@lru_cache(maxsize=100)
async def cached_summarize(text_hash: str):
    # Cache summaries by text hash
    pass
```

### 3. Monitoring

Monitor Groq usage in Render logs:
```bash
# Check logs
render logs -s ai-tech-news-assistant-backend --tail

# Look for:
# "✅ Using Groq provider"
# "Successfully summarized text with Groq"
```

---

## 🎯 Next Steps

### Immediate (Working Now)
- ✅ Groq provider implementation complete
- ✅ Summarization API endpoint ready
- ✅ Auto-detection and fallback working
- ✅ Production deployment configured

### Short Term (Next Features)
- 🔲 Connect frontend "Summarize" button to API
- 🔲 Add loading states and error handling in UI
- 🔲 Display summaries in article cards
- 🔲 Add "Ask AI" chat feature

### Long Term (Enhancements)
- 🔲 Implement caching for repeated summaries
- 🔲 Add batch summarization endpoint
- 🔲 Enable keyword extraction
- 🔲 Add sentiment analysis
- 🔲 Create personalized news digests

---

## 📚 Resources

- **Groq Console**: https://console.groq.com
- **Groq Documentation**: https://console.groq.com/docs
- **API Reference**: https://console.groq.com/docs/api-reference
- **Models Overview**: https://console.groq.com/docs/models
- **Rate Limits**: https://console.groq.com/docs/rate-limits

---

## 💡 Example Use Cases

### 1. Daily News Digest
```python
# Summarize all articles from today
articles = get_todays_articles()
for article in articles:
    summary = await groq_provider.summarize(article.content)
    article.ai_summary = summary
```

### 2. Smart Search
```python
# Use Groq for semantic understanding
user_query = "Tell me about AI breakthroughs"
enhanced_query = await groq_provider.chat([
    {"role": "user", "content": f"Extract keywords from: {user_query}"}
])
```

### 3. Content Moderation
```python
# Check article quality/relevance
result = await groq_provider.chat([
    {"role": "user", "content": f"Is this tech news? {article.content}"}
])
```

---

## 🎉 You're All Set!

Groq integration is now complete and ready to use. The system will:
1. ✅ Auto-detect Groq when API key is configured
2. ✅ Fall back to mock provider if unavailable
3. ✅ Handle errors gracefully
4. ✅ Log all operations for debugging

**Test it now:**
```bash
curl -X POST "https://ai-tech-news-assistant-backend.onrender.com/api/summarize" \
  -H "Content-Type: application/json" \
  -d '{"text": "AI is transforming industries...", "provider": "groq"}'
```

Happy summarizing! 🚀
