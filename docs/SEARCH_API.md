# Semantic Search API Documentation

## Overview

The Semantic Search API provides AI-powered article search using vector embeddings and similarity search. Unlike traditional keyword search, semantic search understands the **meaning** of your queries to find the most relevant articles.

**Key Features:**
- 🧠 **Semantic Understanding**: Finds articles based on meaning, not just keywords
- 🎯 **High Relevance**: Vector similarity using state-of-the-art embeddings
- 🔄 **Smart Reranking**: Multi-factor scoring (similarity + title match + recency)
- 🔍 **Advanced Filtering**: Filter by source, category, date range, and score
- ⚡ **Fast Performance**: Optimized vector search with in-memory caching

---

## Endpoints

### 1. POST /search

Perform semantic search on articles.

**Request Body:**

```json
{
  "query": "artificial intelligence breakthroughs in natural language processing",
  "limit": 10,
  "min_score": 0.5,
  "sources": ["hackernews", "techcrunch"],
  "categories": ["AI", "Machine Learning"],
  "published_after": "2025-01-01T00:00:00Z",
  "published_before": "2025-12-31T23:59:59Z",
  "use_reranking": true
}
```

**Request Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query (semantic meaning) |
| `limit` | integer | No | 20 | Maximum results (1-100) |
| `min_score` | float | No | 0.0 | Minimum similarity score (0.0-1.0) |
| `sources` | array[string] | No | all | Filter by sources (hackernews, techcrunch, reddit, github) |
| `categories` | array[string] | No | all | Filter by categories (AI, ML, Web3, etc.) |
| `published_after` | string (ISO 8601) | No | - | Start date for results |
| `published_before` | string (ISO 8601) | No | - | End date for results |
| `use_reranking` | boolean | No | true | Apply smart reranking algorithm |

**Response (200 OK):**

```json
{
  "query": "artificial intelligence breakthroughs in natural language processing",
  "results": [
    {
      "article_id": "abc123",
      "title": "GPT-4 Achieves New Benchmark in NLP Tasks",
      "url": "https://example.com/article",
      "source": "techcrunch",
      "categories": ["AI", "NLP"],
      "keywords": ["GPT-4", "language model", "benchmark"],
      "published_date": "2025-10-05T12:00:00Z",
      "score": 0.89,
      "embedding_id": "emb_abc123",
      "summary": "AI-generated summary of the article..."
    }
  ],
  "total_results": 15,
  "execution_time_ms": 124.5,
  "reranking_applied": true,
  "filters_applied": {
    "sources": ["techcrunch", "hackernews"],
    "categories": ["AI", "Machine Learning"],
    "min_score": 0.5
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | Original search query |
| `results` | array | List of matching articles (sorted by score) |
| `total_results` | integer | Total number of results found |
| `execution_time_ms` | float | Query execution time in milliseconds |
| `reranking_applied` | boolean | Whether reranking was applied |
| `filters_applied` | object | Applied filters summary |

**Result Item Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `article_id` | string | Unique article identifier |
| `title` | string | Article title |
| `url` | string | Article URL |
| `source` | string | News source (hackernews, techcrunch, etc.) |
| `categories` | array[string] | Article categories |
| `keywords` | array[string] | Extracted keywords |
| `published_date` | string (ISO 8601) | Publication date |
| `score` | float | Relevance score (0.0-1.0, higher is better) |
| `embedding_id` | string | Reference to embedding vector |
| `summary` | string | AI-generated summary (if available) |

**Error Responses:**

```json
// 400 Bad Request - Invalid query
{
  "detail": "Query cannot be empty"
}

// 422 Unprocessable Entity - Validation error
{
  "detail": [
    {
      "loc": ["body", "limit"],
      "msg": "ensure this value is less than or equal to 100",
      "type": "value_error.number.not_le"
    }
  ]
}

// 500 Internal Server Error - Search failed
{
  "detail": "Search failed: Embedding generation error"
}
```

---

### 2. GET /search/health

Check search service health and statistics.

**Response (200 OK):**

```json
{
  "status": "healthy",
  "total_indexed_articles": 1523,
  "last_indexed": "2025-10-06T10:30:00Z",
  "embedding_dimensions": 384,
  "model_name": "all-MiniLM-L6-v2",
  "service_info": {
    "vector_db": "SQLite with embeddings table",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
  }
}
```

**Status Values:**
- `healthy`: Service operational with indexed articles
- `degraded`: Service operational but no articles indexed
- `unhealthy`: Service not operational (check logs)

---

## Usage Examples

### Example 1: Basic Search

Find articles about AI breakthroughs:

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence breakthroughs",
    "limit": 5
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/search",
    json={
        "query": "artificial intelligence breakthroughs",
        "limit": 5
    }
)

data = response.json()
for article in data["results"]:
    print(f"{article['score']:.2f} - {article['title']}")
```

**JavaScript:**
```javascript
const response = await fetch('http://localhost:8000/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'artificial intelligence breakthroughs',
    limit: 5
  })
});

const data = await response.json();
data.results.forEach(article => {
  console.log(`${article.score.toFixed(2)} - ${article.title}`);
});
```

---

### Example 2: Search with Filters

Find recent AI articles from specific sources:

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning models",
    "limit": 10,
    "min_score": 0.6,
    "sources": ["hackernews", "techcrunch"],
    "categories": ["AI", "Machine Learning"],
    "published_after": "2025-01-01T00:00:00Z",
    "use_reranking": true
  }'
```

---

### Example 3: High-Precision Search

Find only highly relevant articles:

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "transformer architecture attention mechanisms",
    "limit": 5,
    "min_score": 0.8,
    "use_reranking": true
  }'
```

---

### Example 4: Check Service Health

```bash
curl -X GET "http://localhost:8000/search/health"
```

**Python:**
```python
import requests

health = requests.get("http://localhost:8000/search/health").json()
print(f"Status: {health['status']}")
print(f"Indexed Articles: {health['total_indexed_articles']}")
print(f"Model: {health['model_name']}")
```

---

## How It Works

### 1. Query Processing
Your query is converted into a 384-dimensional embedding vector using the `all-MiniLM-L6-v2` model from Sentence Transformers.

### 2. Vector Similarity Search
The query embedding is compared to all article embeddings using cosine similarity:

```
similarity = (query_vector · article_vector) / (||query_vector|| × ||article_vector||)
```

### 3. Filtering
Results are filtered based on your criteria:
- **Source**: Only articles from specified sources
- **Category**: Only articles with specified categories
- **Date Range**: Only articles published within date range
- **Min Score**: Only articles above minimum similarity threshold

### 4. Reranking (Optional)
When `use_reranking=true`, results are re-scored using a multi-factor algorithm:

```
final_score = (0.50 × vector_similarity) + 
              (0.30 × title_match_score) + 
              (0.20 × recency_score)
```

- **Vector Similarity (50%)**: Semantic similarity from embeddings
- **Title Match (30%)**: Keyword overlap with query in title
- **Recency (20%)**: Boost for recently published articles

---

## Performance Guidelines

### Optimal Query Length
- **Best**: 5-20 words (e.g., "deep learning neural networks computer vision")
- **Good**: 3-30 words
- **Acceptable**: 1-50 words
- **Not recommended**: > 50 words (may impact accuracy)

### Result Limits
- **Small queries**: `limit: 10-20` (fastest, < 100ms)
- **Medium queries**: `limit: 50` (fast, < 200ms)
- **Large queries**: `limit: 100` (may take 300-500ms)

### Caching
- Embeddings are cached per query for 5 minutes
- Repeated identical queries return instantly from cache

---

## Best Practices

### ✅ DO

1. **Use descriptive queries**: "transformer architecture for NLP" instead of "transformers"
2. **Enable reranking** for better relevance: `use_reranking: true`
3. **Set appropriate min_score**: 0.5 for broad results, 0.7+ for precision
4. **Use filters** to narrow results: sources, categories, dates
5. **Check health endpoint** before large batch operations

### ❌ DON'T

1. **Don't use single-word queries**: Too broad, low precision
2. **Don't use extremely long queries**: > 50 words may reduce accuracy
3. **Don't request excessive results**: `limit > 100` impacts performance
4. **Don't ignore score values**: < 0.5 may be irrelevant
5. **Don't hammer the API**: Use caching for repeated queries

---

## Troubleshooting

### No Results Returned

**Possible causes:**
1. `min_score` too high - Try lowering to 0.3-0.4
2. Filters too restrictive - Remove some filters
3. No articles indexed - Check `/search/health`

**Solution:**
```bash
# Check if articles are indexed
curl http://localhost:8000/search/health

# Try broader search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "AI", "limit": 10, "min_score": 0.3}'
```

---

### Low Relevance Scores

**Possible causes:**
1. Query too generic or broad
2. No articles match semantic meaning
3. Need to reindex articles with better embeddings

**Solution:**
- Make query more specific
- Enable reranking: `use_reranking: true`
- Check article categories and sources

---

### Slow Performance

**Possible causes:**
1. Large result limit (> 50)
2. Database not optimized
3. Embedding generation slow

**Solution:**
```bash
# Use smaller limits
{"query": "...", "limit": 20}

# Check service health
curl http://localhost:8000/search/health
```

---

## Integration Examples

### React/TypeScript Frontend

```typescript
import { useState } from 'react';

interface SearchResult {
  article_id: string;
  title: string;
  url: string;
  score: number;
  source: string;
  published_date: string;
}

interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
  execution_time_ms: number;
}

function ArticleSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          limit: 10,
          min_score: 0.5,
          use_reranking: true
        })
      });
      
      const data: SearchResponse = await response.json();
      setResults(data.results);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search articles..."
      />
      <button onClick={handleSearch} disabled={loading}>
        {loading ? 'Searching...' : 'Search'}
      </button>
      
      <div>
        {results.map((article) => (
          <div key={article.article_id}>
            <h3>{article.title}</h3>
            <p>Score: {article.score.toFixed(2)} | Source: {article.source}</p>
            <a href={article.url} target="_blank">Read More</a>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

### Python CLI Tool

```python
import requests
from typing import List, Dict

class SemanticSearchClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def search(
        self, 
        query: str, 
        limit: int = 10,
        min_score: float = 0.5,
        sources: List[str] = None,
        use_reranking: bool = True
    ) -> Dict:
        """Perform semantic search."""
        payload = {
            "query": query,
            "limit": limit,
            "min_score": min_score,
            "use_reranking": use_reranking
        }
        
        if sources:
            payload["sources"] = sources
        
        response = requests.post(
            f"{self.base_url}/search",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        return response.json()
    
    def health_check(self) -> Dict:
        """Check service health."""
        response = requests.get(f"{self.base_url}/search/health")
        response.raise_for_status()
        return response.json()


# Usage
if __name__ == "__main__":
    client = SemanticSearchClient()
    
    # Check health
    health = client.health_check()
    print(f"✓ Service: {health['status']}")
    print(f"✓ Indexed: {health['total_indexed_articles']} articles\n")
    
    # Perform search
    results = client.search(
        query="machine learning breakthroughs",
        limit=5,
        sources=["hackernews", "techcrunch"],
        use_reranking=True
    )
    
    print(f"Found {results['total_results']} results in {results['execution_time_ms']:.1f}ms\n")
    
    for i, article in enumerate(results['results'], 1):
        print(f"{i}. [{article['score']:.2f}] {article['title']}")
        print(f"   {article['source']} - {article['published_date'][:10]}")
        print(f"   {article['url']}\n")
```

---

## FAQ

### Q: What's the difference between semantic search and keyword search?

**Keyword Search**: Matches exact words  
- Query: "NLP models"
- Matches: Articles containing "NLP" and "models"

**Semantic Search**: Understands meaning  
- Query: "NLP models"
- Matches: Articles about transformers, BERT, GPT, language models (even if they don't contain exact words)

---

### Q: What embedding model is used?

`all-MiniLM-L6-v2` from Sentence Transformers
- **Dimensions**: 384
- **Performance**: Fast inference (< 50ms per query)
- **Quality**: High-quality semantic understanding
- **Size**: Lightweight (80MB model)

---

### Q: How is the relevance score calculated?

Without reranking:
- **Score = Cosine Similarity** (0.0 - 1.0)

With reranking:
- **Score = 0.5×similarity + 0.3×title_match + 0.2×recency**

---

### Q: Can I search in multiple languages?

Currently optimized for English. For multilingual search, consider using `paraphrase-multilingual-MiniLM-L12-v2` model (requires configuration change).

---

### Q: What's the maximum number of results?

Hard limit: 100 results per query  
Recommended: 10-20 for best performance

---

## Support

For issues, questions, or feature requests:
- **GitHub Issues**: [Create an issue](https://github.com/ductringuyen0186/ai-tech-news-assistant/issues)
- **Documentation**: [Project README](../README.md)
- **API Explorer**: Visit `/docs` endpoint for interactive API documentation

---

**Version**: 1.0.0  
**Last Updated**: October 6, 2025  
**Maintainer**: AI Tech News Assistant Team
