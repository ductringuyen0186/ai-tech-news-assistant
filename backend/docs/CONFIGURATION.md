# Environment Configuration Guide

The AI Tech News Assistant uses a comprehensive environment configuration system built with Pydantic for validation and type safety. This guide explains how to configure the application for different environments.

## Quick Start

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your settings:**
   - Set your `SECRET_KEY` (32+ characters)
   - Configure your LLM provider API keys
   - Adjust database settings if needed

3. **Validate your configuration:**
   ```bash
   python validate_config.py
   ```

4. **Check external service connectivity:**
   ```bash
   python validate_config.py --check-services
   ```

## Environment Types

The application supports four environment types:

### Development (`ENVIRONMENT=development`)
- Debug mode enabled
- Relaxed security settings
- Auto-reload enabled
- Detailed error messages
- Uses SQLite by default
- Ollama as default LLM provider

### Testing (`ENVIRONMENT=testing`)
- In-memory database
- Fast timeouts
- Minimal resource usage
- Detailed error logging
- No external service dependencies

### Staging (`ENVIRONMENT=staging`)
- Production-like configuration
- Real database connections
- Cloud LLM providers
- Monitoring enabled
- Security hardened

### Production (`ENVIRONMENT=production`)
- Debug mode disabled
- Strict security settings
- Enhanced monitoring
- Rate limiting enabled
- PostgreSQL recommended
- Cloud LLM providers

## Configuration Sections

### Core Application Settings

```env
# Required
ENVIRONMENT=development
SECRET_KEY=your-32-plus-character-secret-key
APP_NAME=AI Tech News Assistant

# Server
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=["http://localhost:3000"]
```

### Database Configuration

#### SQLite (Default for Development)
```env
DATABASE_TYPE=sqlite
SQLITE_DATABASE_PATH=./data/database.db
```

#### PostgreSQL (Recommended for Production)
```env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:password@localhost:5432/ai_tech_news
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=50
```

#### MySQL
```env
DATABASE_TYPE=mysql
DATABASE_URL=mysql://user:password@localhost:3306/ai_tech_news
```

### LLM Provider Configuration

#### OpenAI
```env
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7
```

#### Anthropic
```env
DEFAULT_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-api-key
ANTHROPIC_MODEL=claude-3-sonnet-20240229
ANTHROPIC_MAX_TOKENS=1000
```

#### Ollama (Local LLM)
```env
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=60
```

#### HuggingFace
```env
DEFAULT_LLM_PROVIDER=huggingface
HUGGINGFACE_API_KEY=your-api-key
HUGGINGFACE_MODEL=microsoft/DialoGPT-medium
```

### Vector Database Settings

```env
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
VECTOR_SIMILARITY_THRESHOLD=0.7
VECTOR_MAX_RESULTS=10
```

### News Sources

The application includes default RSS sources, but you can customize them:

```env
RSS_SOURCES=[
  {
    "name": "Custom Feed",
    "url": "https://example.com/feed.xml",
    "description": "Custom news source"
  }
]
RSS_TIMEOUT=10
RSS_MAX_ARTICLES=100
RSS_UPDATE_INTERVAL=3600
```

### Logging Configuration

```env
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE=./logs/app.log  # Optional
LOG_MAX_SIZE=10485760    # 10MB
LOG_BACKUP_COUNT=5
```

### Security Settings

```env
# CORS
ENABLE_CORS=true
ALLOWED_ORIGINS=["https://yourdomain.com"]
TRUSTED_HOSTS=["yourdomain.com"]

# Content limits
MAX_CONTENT_LENGTH=16777216  # 16MB

# Error handling
ENABLE_ERROR_MIDDLEWARE=true
ENABLE_CORRELATION_ID=true
ERROR_DETAIL_IN_RESPONSE=false  # Only true in development
```

### Performance & Monitoring

```env
# Rate limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Timeouts
LLM_REQUEST_TIMEOUT=30.0
EMBEDDING_REQUEST_TIMEOUT=15.0
NEWS_FETCH_TIMEOUT=10.0

# Caching
ENABLE_CACHING=true
CACHE_TTL=3600
CACHE_MAX_SIZE=1000

# Monitoring
ENABLE_METRICS=true
METRICS_ENDPOINT=/metrics
HEALTH_CHECK_TIMEOUT=5.0
```

## Environment-Specific Files

### Production Deployment
Use `.env.production` as a template:
```bash
cp .env.production .env
# Edit with production values
python validate_config.py --env .env.production
```

### Testing
Use `.env.testing` for test environments:
```bash
cp .env.testing .env.test
python validate_config.py --env .env.test
```

## Configuration Validation

The configuration system includes built-in validation:

### Automatic Validations
- Secret key length (minimum 32 characters)
- Production debug mode (must be disabled)
- CORS origins in production (no wildcards)
- Database URL format
- LLM provider API keys
- Directory permissions

### Custom Validation Script
```bash
# Basic validation
python validate_config.py

# With external service checks
python validate_config.py --check-services

# Specific environment file
python validate_config.py --env .env.production --check-services
```

## Security Best Practices

### Secret Management
1. **Never commit API keys** to version control
2. **Use strong secret keys** (32+ characters, random)
3. **Rotate keys regularly** in production
4. **Use environment variables** or secret management systems

### Production Hardening
1. **Disable debug mode**: `DEBUG=false`
2. **Restrict CORS origins**: No wildcards (`*`)
3. **Use HTTPS**: Configure reverse proxy
4. **Enable monitoring**: Set up metrics and health checks
5. **Implement rate limiting**: Protect against abuse

### Database Security
1. **Use connection pooling**: Configure appropriate pool sizes
2. **Enable SSL/TLS**: For database connections
3. **Restrict access**: Use firewall rules and VPNs
4. **Regular backups**: Implement backup strategies

## Troubleshooting

### Common Issues

#### Configuration Load Errors
```bash
# Check syntax and required fields
python validate_config.py
```

#### Database Connection Issues
```bash
# Verify database URL and credentials
python -c "from src.core.config import Settings; s=Settings(); print(s.get_database_path())"
```

#### LLM Provider Issues
```bash
# Test API key and connectivity
python validate_config.py --check-services
```

#### Permission Errors
```bash
# Check directory permissions
ls -la data/
mkdir -p data/chroma_db logs
```

### Debug Mode
Enable debug mode for detailed error information:
```env
DEBUG=true
LOG_LEVEL=DEBUG
ERROR_DETAIL_IN_RESPONSE=true
```

## Environment Variables Reference

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENVIRONMENT` | str | development | Environment type |
| `DEBUG` | bool | true | Debug mode |
| `SECRET_KEY` | str | - | Secret key for JWT/security |
| `DATABASE_TYPE` | str | sqlite | Database type |
| `DEFAULT_LLM_PROVIDER` | str | ollama | LLM provider |
| `LOG_LEVEL` | str | INFO | Logging level |
| `RATE_LIMIT_REQUESTS` | int | 100 | Rate limit per window |
| `CACHE_TTL` | int | 3600 | Cache TTL in seconds |

See `.env.example` for the complete list of available configuration options.

## Advanced Configuration

### Custom Configuration Loading
```python
from src.core.config import Settings

# Load with custom env file
settings = Settings(_env_file='.env.custom')

# Get LLM config for specific provider
openai_config = settings.get_llm_config(LLMProvider.OPENAI)

# Environment checks
if settings.is_production():
    # Production-specific logic
    pass
```

### Dynamic Configuration
```python
# Runtime configuration updates (use carefully)
settings.log_level = LogLevel.DEBUG
settings.rate_limit_requests = 200
```

### Configuration in Docker
```dockerfile
# Use build args for configuration
ARG ENVIRONMENT=production
ENV ENVIRONMENT=${ENVIRONMENT}

# Mount config files
VOLUME ["/app/config"]
```

For more examples and advanced usage, see the `validate_config.py` script and configuration tests.
