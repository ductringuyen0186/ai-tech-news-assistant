# Production Deployment Guide 🚀

## Pre-Deployment Checklist

### Environment Preparation

#### 1. Generate Secure SECRET_KEY
```bash
# Linux/macOS
openssl rand -hex 32

# Windows PowerShell
-join (1..64 | ForEach-Object { '{0:x}' -f (Get-Random -Max 16) })

# Python
python -c "import secrets; print(secrets.token_hex(32))"
```

#### 2. Prepare Production Environment File

Create `backend/.env.production`:
```env
# Application
APP_NAME=AI Tech News Assistant
VERSION=2.0.0
ENVIRONMENT=production
DEBUG=false
RELOAD=false

# Security - CRITICAL: Change these!
SECRET_KEY=YOUR_GENERATED_SECRET_KEY_HERE
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server
HOST=0.0.0.0
PORT=8001

# Database - Use PostgreSQL in production
DATABASE_URL=postgresql://user:password@db-host:5432/ai_tech_news
DATABASE_ECHO=false

# Redis for caching
REDIS_URL=redis://redis-host:6379/0

# AI/LLM
OLLAMA_HOST=http://ollama-host:11434
OLLAMA_MODEL=llama3.2:1b

# CORS - Add your production domain
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/production.log
```

---

## Deployment Methods

### Method 1: Docker Compose (Recommended)

#### Prerequisites
- Docker & Docker Compose installed
- Domain name configured
- SSL certificates ready

#### Steps

1. **Create Production Docker Compose**

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: ai-news-db
    environment:
      POSTGRES_USER: ai_news_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ai_tech_news
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - ai-news-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: ai-news-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - ai-news-network
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: ai-news-backend
    environment:
      - DATABASE_URL=postgresql://ai_news_user:${DB_PASSWORD}@postgres:5432/ai_tech_news
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - postgres
      - redis
    networks:
      - ai-news-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: ai-news-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
    depends_on:
      - backend
    networks:
      - ai-news-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  ai-news-network:
    driver: bridge
```

2. **Create Backend Dockerfile**

Create `backend/Dockerfile.prod`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8001/health')"

# Run application
CMD ["gunicorn", "production_main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8001", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

3. **Create Nginx Configuration**

Create `nginx/nginx.conf`:
```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8001;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Frontend
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;

            # Caching for static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

        # Backend API
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;

            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket support (if needed)
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Health check endpoint
        location /health {
            proxy_pass http://backend/health;
            access_log off;
        }
    }
}
```

4. **Deploy**

```bash
# Set environment variables
export SECRET_KEY=$(openssl rand -hex 32)
export DB_PASSWORD=$(openssl rand -base64 32)

# Build frontend
cd frontend
npm run build

# Start services
cd ..
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose logs -f backend

# Run database migrations
docker-compose exec backend alembic upgrade head
```

---

### Method 2: Cloud Platform (Railway/Render)

#### Railway Deployment

1. **Install Railway CLI**
```bash
npm install -g @railway/cli
railway login
```

2. **Initialize Project**
```bash
railway init
railway link
```

3. **Add PostgreSQL**
```bash
railway add postgresql
```

4. **Configure Environment**
```bash
# Add environment variables in Railway dashboard
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://... # Auto-populated by Railway
ALLOWED_ORIGINS=https://your-app.railway.app
```

5. **Deploy**
```bash
# Backend
cd backend
railway up

# Frontend (deploy separately to Vercel/Netlify)
```

#### Render Deployment

1. **Create `render.yaml`**:
```yaml
services:
  - type: web
    name: ai-news-backend
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "gunicorn production_main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT"
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: ai-news-db
          property: connectionString
      - key: PYTHON_VERSION
        value: 3.11.0

databases:
  - name: ai-news-db
    databaseName: ai_tech_news
    user: ai_news_user
```

2. **Deploy via Git**
```bash
git push render main
```

---

### Method 3: VPS (Ubuntu/Debian)

#### Full Manual Setup

1. **Server Setup**
```bash
# SSH into server
ssh user@your-server-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip \
                    nginx postgresql redis-server \
                    certbot python3-certbot-nginx \
                    git supervisor

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

2. **Database Setup**
```bash
# Create PostgreSQL database and user
sudo -u postgres psql
CREATE DATABASE ai_tech_news;
CREATE USER ai_news_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ai_tech_news TO ai_news_user;
\q
```

3. **Application Setup**
```bash
# Create app directory
sudo mkdir -p /var/www/ai-tech-news
sudo chown $USER:$USER /var/www/ai-tech-news

# Clone repository
cd /var/www/ai-tech-news
git clone https://github.com/yourusername/ai-tech-news-assistant.git .

# Backend setup
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn

# Create .env file
cp .env.example .env
nano .env  # Edit with production values

# Run migrations
alembic upgrade head
```

4. **Configure Supervisor**

Create `/etc/supervisor/conf.d/ai-news.conf`:
```ini
[program:ai-news-backend]
directory=/var/www/ai-tech-news/backend
command=/var/www/ai-tech-news/backend/venv/bin/gunicorn production_main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 127.0.0.1:8001
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/ai-news/backend.err.log
stdout_logfile=/var/log/ai-news/backend.out.log
environment=PATH="/var/www/ai-tech-news/backend/venv/bin"

[program:ai-news-worker]
directory=/var/www/ai-tech-news/backend
command=/var/www/ai-tech-news/backend/venv/bin/celery -A app.celery worker --loglevel=info
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/ai-news/celery.err.log
stdout_logfile=/var/log/ai-news/celery.out.log
```

```bash
# Create log directory
sudo mkdir -p /var/log/ai-news
sudo chown www-data:www-data /var/log/ai-news

# Start services
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

5. **Configure Nginx**

Create `/etc/nginx/sites-available/ai-news`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Frontend
    root /var/www/ai-tech-news/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://127.0.0.1:8001/health;
        access_log off;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ai-news /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

6. **Setup SSL**
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
sudo systemctl reload nginx
```

7. **Frontend Build**
```bash
cd /var/www/ai-tech-news/frontend
npm install
npm run build
```

---

## Post-Deployment

### 1. Verify Deployment
```bash
# Check backend health
curl https://yourdomain.com/api/v1/health

# Check frontend
curl https://yourdomain.com

# Test API
curl https://yourdomain.com/api/v1/
```

### 2. Setup Monitoring

#### Error Tracking (Sentry)
```python
# backend/production_main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0,
    environment="production"
)
```

#### Uptime Monitoring
- **UptimeRobot** - Free tier available
- **Better Uptime** - 14-day trial
- **Pingdom** - Professional monitoring

### 3. Setup Backups

#### Database Backups
```bash
# Create backup script
cat > /usr/local/bin/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/ai-news"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
pg_dump ai_tech_news | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/backup-db.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-db.sh
```

### 4. Performance Optimization

#### Enable Redis Caching
```python
# backend/.env
REDIS_URL=redis://localhost:6379/0

# Update code to use Redis for caching
```

#### Database Indexes
```sql
-- Add indexes for common queries
CREATE INDEX idx_articles_published_at ON articles(published_at DESC);
CREATE INDEX idx_articles_source ON articles(source);
CREATE INDEX idx_articles_categories ON articles USING GIN(categories);
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -h localhost -U ai_news_user -d ai_tech_news

# Check logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### 2. Nginx 502 Bad Gateway
```bash
# Check backend is running
sudo supervisorctl status ai-news-backend

# Check backend logs
sudo tail -f /var/log/ai-news/backend.err.log

# Test backend directly
curl http://127.0.0.1:8001/health
```

#### 3. SSL Certificate Issues
```bash
# Renew certificates
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run
```

---

## Maintenance

### Regular Tasks
- [ ] Daily: Check error logs
- [ ] Weekly: Review application metrics
- [ ] Monthly: Update dependencies
- [ ] Quarterly: Security audit
- [ ] Yearly: SSL certificate renewal (auto with certbot)

### Update Procedure
```bash
# 1. Backup database
/usr/local/bin/backup-db.sh

# 2. Pull latest code
cd /var/www/ai-tech-news
git pull origin main

# 3. Update dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt

# 4. Run migrations
alembic upgrade head

# 5. Restart services
sudo supervisorctl restart ai-news-backend
sudo supervisorctl restart ai-news-worker

# 6. Clear cache
redis-cli FLUSHDB

# 7. Rebuild frontend
cd ../frontend
npm install
npm run build
```

---

## Security Best Practices

1. **Keep secrets out of version control**
2. **Use environment variables for sensitive data**
3. **Enable firewall (ufw on Ubuntu)**
4. **Regular security updates**
5. **Monitor access logs**
6. **Implement rate limiting**
7. **Use strong passwords**
8. **Enable 2FA where possible**

---

**Deployment Complete! 🎉**

Your AI Tech News Assistant is now live in production!
