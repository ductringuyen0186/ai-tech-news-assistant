# News Ingestion System

## Overview

The new ingestion system provides automated scraping of tech news from multiple RSS feeds, with intelligent deduplication, category tagging, and error handling.

### Features

✅ **Multi-source RSS Scraping** - 5 default tech news sources (Hacker News, TechCrunch, Ars Technica, The Verge, MIT Technology Review)  
✅ **Duplicate Detection** - Prevents duplicate articles via URL checking  
✅ **Smart Categorization** - Automatic category assignment for articles  
✅ **Error Resilience** - Graceful error handling with detailed error tracking  
✅ **Progress Tracking** - Real-time status and statistics  
✅ **Flexible Deployment** - Foreground or background execution  

---

## API Endpoints

### 1. Trigger Ingestion
```
POST /api/ingest
```

**Request Body:**
```json
{
  "background": true,
  "sources": null
}
```

**Parameters:**
- `background` (bool, optional): Run in background (true) or foreground (false). Default: true
- `sources` (array, optional): Custom RSS feeds to ingest. If null, uses default feeds.

**Custom Sources Example:**
```json
{
  "background": false,
  "sources": [
    {
      "name": "Custom Tech News",
      "url": "https://example.com/feed.xml",
      "category": "technology"
    }
  ]
}
```

**Response (Background):**
```json
{
  "message": "Ingestion started in background",
  "job_id": "bg_ingest_001",
  "background": true
}
```

**Response (Foreground):**
```json
{
  "message": "Ingestion completed: 47 articles saved",
  "job_id": null,
  "background": false
}
```

---

### 2. Get Ingestion Status
```
GET /api/ingest/status
```

**Response:**
```json
{
  "status": "completed",
  "result": {
    "status": "completed",
    "start_time": "2025-10-21T10:30:15.123456",
    "end_time": "2025-10-21T10:35:42.654321",
    "duration_seconds": 327.5,
    "total_feeds": 5,
    "total_articles_found": 125,
    "total_articles_saved": 47,
    "duplicates_skipped": 75,
    "errors_encountered": 3,
    "success_rate": "37.6%",
    "sources_processed": {
      "Hacker News": 25,
      "TechCrunch": 30,
      "Ars Technica": 28,
      "The Verge": 22,
      "MIT Technology Review": 20
    },
    "error_details": [
      {
        "source": "TechCrunch",
        "error": "Connection timeout",
        "timestamp": "2025-10-21T10:31:20.123456"
      }
    ]
  }
}
```

---

### 3. Get Ingestion Statistics
```
GET /api/ingest/stats
```

**Response:**
```json
{
  "total_articles": 1250,
  "total_sources": 5,
  "total_categories": 8,
  "last_result": {
    "status": "completed",
    "start_time": "2025-10-21T10:30:15.123456",
    "duration_seconds": 327.5,
    "total_articles_saved": 47,
    "duplicates_skipped": 75,
    "errors_encountered": 3
  }
}
```

---

## Default RSS Feeds

The system includes 5 pre-configured tech news sources:

| Source | Category | URL |
|--------|----------|-----|
| Hacker News | AI | https://feeds.feedburner.com/oreilly/radar |
| TechCrunch | Startups | https://techcrunch.com/feed/ |
| Ars Technica | Technology | https://feeds.arstechnica.com/arstechnica/index |
| The Verge | Technology | https://www.theverge.com/rss/index.xml |
| MIT Technology Review | AI | https://www.technologyreview.com/feed/ |

---

## Usage Examples

### cURL Examples

**Start background ingestion:**
```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"background": true}'
```

**Start foreground ingestion:**
```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"background": false}'
```

**Get latest ingestion status:**
```bash
curl http://localhost:8000/api/ingest/status
```

**Get database statistics:**
```bash
curl http://localhost:8000/api/ingest/stats
```

---

### Python Examples

```python
import httpx

# Trigger ingestion
client = httpx.Client()

response = client.post(
    "http://localhost:8000/api/ingest",
    json={"background": True}
)
print(response.json())
# Output: {"message": "Ingestion started in background", ...}

# Get status
response = client.get("http://localhost:8000/api/ingest/status")
status = response.json()
print(f"Status: {status['status']}")
print(f"Articles saved: {status['result']['total_articles_saved']}")

# Get stats
response = client.get("http://localhost:8000/api/ingest/stats")
stats = response.json()
print(f"Total articles in DB: {stats['total_articles']}")
print(f"Total sources: {stats['total_sources']}")
```

---

### JavaScript/Fetch Examples

```javascript
// Trigger ingestion
fetch('http://localhost:8000/api/ingest', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ background: true })
})
  .then(r => r.json())
  .then(data => console.log(data.message))

// Get status
fetch('http://localhost:8000/api/ingest/status')
  .then(r => r.json())
  .then(data => {
    console.log(`Status: ${data.status}`);
    console.log(`Articles: ${data.result.total_articles_saved}`);
  })

// Get stats
fetch('http://localhost:8000/api/ingest/stats')
  .then(r => r.json())
  .then(stats => {
    console.log(`Total articles: ${stats.total_articles}`);
    console.log(`Total sources: ${stats.total_sources}`);
  })
```

---

## Architecture

### IngestionService

Core service handling all ingestion logic:

```python
class IngestionService:
    def ingest_all(sources: Optional[List[Dict]]) -> IngestionResult
    def _ingest_feed(feed_config: Dict) -> None
    def _process_entry(entry: Dict, source: str, category) -> None
    def _get_or_create_category(name: str) -> Category
    def _get_source_id(name: str) -> int
    def get_stats() -> Dict
```

**Key Features:**
- Synchronous implementation for simplicity and reliability
- Database transaction handling (commit all or rollback all)
- Detailed error tracking and recovery
- RSS parsing via `feedparser` library
- HTTP fetching via `httpx`

### IngestionResult

Detailed result object with metrics:
- `status`: PENDING, RUNNING, COMPLETED, FAILED, PARTIAL
- `total_feeds`: Number of feeds processed
- `total_articles_found`: Articles discovered in RSS
- `total_articles_saved`: Successfully inserted into DB
- `duplicates_skipped`: Exact matches (by URL) skipped
- `errors_encountered`: Number of errors
- `success_rate`: Percentage of articles successfully saved
- `duration_seconds`: Total time taken

### API Routes

Lightweight routes in `src/api/routes/ingestion.py`:
- `POST /api/ingest` - Trigger ingestion (foreground or background)
- `GET /api/ingest/status` - Last ingestion result
- `GET /api/ingest/stats` - Current DB statistics

---

## Database Schema

### Articles
```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    url VARCHAR(1000) UNIQUE NOT NULL,
    content TEXT,
    summary TEXT,
    author VARCHAR(200),
    published_at DATETIME,
    source_id INTEGER FOREIGN KEY,
    language VARCHAR(10),
    word_count INTEGER,
    reading_time INTEGER,
    created_at DATETIME,
    updated_at DATETIME
);
```

### Sources
```sql
CREATE TABLE sources (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    url VARCHAR(500) UNIQUE NOT NULL,
    rss_url VARCHAR(500),
    is_active BOOLEAN,
    scrape_frequency INTEGER,
    last_scraped DATETIME,
    created_at DATETIME,
    updated_at DATETIME
);
```

### Categories
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    is_active BOOLEAN,
    created_at DATETIME
);
```

### Article-Category Relationship
```sql
CREATE TABLE article_categories (
    article_id INTEGER FOREIGN KEY,
    category_id INTEGER FOREIGN KEY,
    PRIMARY KEY (article_id, category_id)
);
```

---

## Error Handling

The system handles errors gracefully:

1. **Feed Fetch Errors** - Individual feed failures don't stop other feeds
2. **Entry Processing Errors** - Bad entries are logged and skipped
3. **Database Errors** - Transaction rolled back, detailed error recorded
4. **Duplicate Detection** - Silently skipped with counter incremented

All errors are tracked in `error_details` for debugging.

---

## Performance Considerations

### Optimizations
- ✅ Batch processing (commit once per feed)
- ✅ Duplicate detection via URL lookup (O(1) with index)
- ✅ Connection pooling (httpx Client reuse)
- ✅ Efficient category/source lookups
- ✅ Minimal memory usage (streaming processing)

### Typical Performance
- **5 feeds** → 2-5 minutes (depends on network/content)
- **150+ articles** scraped per run
- **50+ articles** typically saved (after dedup)
- **Success rate** 35-50% (many are duplicates from daily updates)

---

## Monitoring & Debugging

### Check Ingestion Health
```bash
# Get latest status
curl http://localhost:8000/api/ingest/status

# Get stats
curl http://localhost:8000/api/ingest/stats

# Check logs
tail -f logs/ingestion.log
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Many duplicates | Same articles published daily | Normal; dedup working correctly |
| Low save rate | Feed unavailable | Check error_details in status |
| No new articles | Feeds not updated | Wait 24h for feed updates |
| Database error | Connection issues | Check database connectivity |
| Timeout errors | Slow feeds | Increase timeout in config |

---

## Future Enhancements

Planned improvements:

- [ ] Async ingestion pipeline (for faster processing)
- [ ] Scheduled ingestion jobs (APScheduler)
- [ ] Content extraction and cleaning
- [ ] Article summarization via LLM
- [ ] Vector embeddings for semantic search
- [ ] Article ranking/relevance scoring
- [ ] User preference filtering
- [ ] Email digest generation
- [ ] Real-time webhook notifications
- [ ] Feed health monitoring dashboard

---

## Testing

### Manual Testing

```bash
# Start backend
cd backend
python main.py

# In another terminal, trigger ingestion
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"background": false}'

# Check status
curl http://localhost:8000/api/ingest/status

# View stats
curl http://localhost:8000/api/ingest/stats
```

### Automated Testing

```bash
pytest tests/services/test_ingestion_service.py -v
pytest tests/api/test_ingestion_routes.py -v
```

---

## Deployment

### Production Checklist

- [ ] Database has proper indexes on `articles.url`, `sources.name`, `categories.name`
- [ ] CORS is configured to allow frontend domain
- [ ] Rate limiting is enabled (if needed)
- [ ] Error logging is configured (Sentry/DataDog)
- [ ] Health checks are monitored
- [ ] Backup strategy is in place
- [ ] Ingestion logs are archived

### Environment Variables

```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost/ai_news
INGEST_TIMEOUT=30
INGEST_BATCH_SIZE=5
```

---

## Support

For issues or questions:
1. Check logs: `logs/ingestion.log`
2. Review error_details in status endpoint
3. Test feed URLs individually
4. Check database connectivity
