# DT-RAG v1.8.1 Production Deployment Guide

## Quick Start (5 minutes)

### Step 1: Set Environment Variables

```bash
# Required: PostgreSQL connection
export DATABASE_URL="postgresql+asyncpg://username:password@hostname:5432/database_name"

# Required: OpenAI API key for embeddings
export OPENAI_API_KEY="sk-proj-..."

# Optional: Gemini API for fallback
export GEMINI_API_KEY="..."

# Optional: Redis for caching
export REDIS_HOST="localhost"
export REDIS_PORT="6379"

# Optional: Sentry for monitoring
export SENTRY_DSN="https://..."
```

**Important Notes:**
- If `DATABASE_URL` is not set, the system will use default: `postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag`
- For production, **always set explicit DATABASE_URL** with secure credentials
- Use `.env` file for local development:
  ```bash
  cp .env.example .env
  # Edit .env with your values
  ```

### Step 2: Database Schema Setup

**Option A: Fresh Installation**

```bash
# Connect to PostgreSQL
psql -U postgres -h localhost

# Create database
CREATE DATABASE dt_rag;

# Run setup script
\i setup_postgresql.sql
```

**Option B: Using psql directly**

```bash
psql $DATABASE_URL < setup_postgresql.sql
```

The `setup_postgresql.sql` script will:
- Create all required tables (documents, chunks, embeddings, doc_taxonomy, taxonomy_nodes)
- Install pgvector extension
- Create HNSW and GIN indexes for performance
- Set up proper foreign key constraints

### Step 3: Verify Installation

```bash
# Run production readiness check
python production_readiness_check.py

# Expected output:
# - Environment Variables: PASS
# - Dependencies: PASS (7/7)
# - Test Suite: PASS
# - Readiness Score: 95-100/100
```

### Step 4: Start Server

**Development:**
```bash
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Production:**
```bash
uvicorn apps.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info \
  --access-log
```

**With Gunicorn (recommended for production):**
```bash
gunicorn apps.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

## Environment Variables Reference

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:5432/db` |
| `OPENAI_API_KEY` | OpenAI API key for embeddings | `sk-proj-...` |

### Optional

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `GEMINI_API_KEY` | Gemini API for LLM fallback | None | `AIza...` |
| `REDIS_HOST` | Redis hostname for caching | `localhost` | `redis.example.com` |
| `REDIS_PORT` | Redis port | `6379` | `6379` |
| `SENTRY_DSN` | Sentry monitoring DSN | None | `https://...@sentry.io/...` |
| `RATE_LIMIT_READ` | Read endpoint rate limit | `100/minute` | `200/minute` |
| `RATE_LIMIT_WRITE` | Write endpoint rate limit | `50/minute` | `100/minute` |
| `RATE_LIMIT_ADMIN` | Admin endpoint rate limit | `200/minute` | `500/minute` |

## Database Schema Details

### Required Tables

The `setup_postgresql.sql` creates these tables:

1. **documents** - Document metadata
2. **chunks** - Text chunks for retrieval
3. **embeddings** - Vector embeddings (1536 dimensions)
4. **doc_taxonomy** - Document taxonomy relationships
5. **taxonomy_nodes** - Taxonomy hierarchy
6. **api_keys** - API key authentication
7. **api_key_usage** - Usage tracking
8. **api_key_audit_log** - Audit logging

### Required Extensions

- **pgvector** - Vector similarity search
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```

### Performance Indexes

- **HNSW index** on embeddings.embedding (vector similarity)
- **GIN index** on chunks (full-text search)
- Multiple composite indexes for filtering and sorting

## API Key Management

### Generate API Key

```bash
# Using Python script
python -c "
from apps.api.security.api_key_storage import APIKeyManager
import asyncio

async def create_key():
    manager = APIKeyManager()
    key = await manager.create_api_key(
        name='production-api',
        owner_id='admin',
        tier='admin',
        allowed_ips=['0.0.0.0/0'],  # Adjust for security
        expires_days=365
    )
    print(f'API Key: {key}')

asyncio.run(create_key())
"
```

### Use API Key

```bash
# Test endpoint with API key
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "top_k": 5
  }'
```

## Health Checks

### Endpoint: `/health`

```bash
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "version": "1.8.1",
  "database": "connected",
  "timestamp": "2025-10-01T18:00:00Z"
}
```

### Monitoring Endpoints

- `/metrics` - Prometheus metrics (if enabled)
- `/api/v1/monitoring/stats` - System statistics
- `/api/v1/monitoring/health` - Detailed health check

## Security Checklist

- [ ] DATABASE_URL uses strong password
- [ ] OPENAI_API_KEY is secured (not in code/logs)
- [ ] API keys generated and secured
- [ ] Rate limiting enabled (slowapi + Redis)
- [ ] HTTPS/TLS enabled (reverse proxy)
- [ ] CORS configured for allowed origins
- [ ] IP whitelist configured for admin endpoints
- [ ] Sentry DSN configured for error tracking
- [ ] Database backups scheduled
- [ ] API key rotation policy defined

## Troubleshooting

### Issue: "Database connection failed"

**Solution:**
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test PostgreSQL connection
psql $DATABASE_URL -c "SELECT version();"

# Check pgvector extension
psql $DATABASE_URL -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

### Issue: "pgvector extension not found"

**Solution:**
```bash
# Install pgvector (Ubuntu/Debian)
sudo apt install postgresql-15-pgvector

# Or compile from source
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Enable in database
psql $DATABASE_URL -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Issue: "Rate limit exceeded"

**Solution:**
```bash
# Adjust rate limits
export RATE_LIMIT_READ="200/minute"
export RATE_LIMIT_WRITE="100/minute"

# Or check Redis connection
redis-cli ping
```

### Issue: "Tests failing in production_readiness_check.py"

**Solution:**
```bash
# Check specific test category
python -m pytest tests/security/ -v
python -m pytest tests/test_hybrid_search.py -v

# View detailed logs
python production_readiness_check.py 2>&1 | tee deployment.log
```

## Performance Tuning

### PostgreSQL Configuration

```sql
-- Increase work_mem for vector operations
ALTER SYSTEM SET work_mem = '256MB';

-- Tune for SSD storage
ALTER SYSTEM SET random_page_cost = 1.1;

-- Connection pooling
ALTER SYSTEM SET max_connections = 100;

-- Reload configuration
SELECT pg_reload_conf();
```

### HNSW Index Tuning

```sql
-- Rebuild with custom parameters
DROP INDEX IF EXISTS idx_embeddings_hnsw;
CREATE INDEX idx_embeddings_hnsw ON embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### Application Configuration

```python
# In apps/core/db_session.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # Adjust based on workers
    max_overflow=10,
    pool_pre_ping=True,    # Verify connections
    echo=False
)
```

## Backup and Recovery

### Database Backup

```bash
# Full backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Compressed backup
pg_dump $DATABASE_URL | gzip > backup_$(date +%Y%m%d).sql.gz

# With vectors (use custom format)
pg_dump -Fc $DATABASE_URL > backup_$(date +%Y%m%d).dump
```

### Restore

```bash
# From SQL dump
psql $DATABASE_URL < backup_20251001.sql

# From custom format
pg_restore -d $DATABASE_URL backup_20251001.dump
```

## Deployment Platforms

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/dt_rag
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db
      - redis

  db:
    image: pgvector/pgvector:pg15
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=dt_rag
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pgdata:
```

### Kubernetes

See `k8s/` directory for deployment manifests.

## Document Ingestion Setup

### Migration 0006: PII Tracking

Before using document ingestion, run migration 0006 to add PII tracking columns:

```bash
# Using Alembic
alembic upgrade head

# Verify migration
psql $DATABASE_URL -c "SELECT column_name FROM information_schema.columns WHERE table_name='chunks' AND column_name IN ('token_count', 'has_pii', 'pii_types');"

# Expected output:
#  column_name
# --------------
#  token_count
#  has_pii
#  pii_types
```

The migration adds:
- `token_count`: Number of tokens in chunk (for cost estimation)
- `has_pii`: Boolean flag indicating PII presence
- `pii_types`: Array of detected PII types (e.g., email, phone, ssn)

### Required Libraries

Document ingestion requires these parser libraries (already in requirements.txt):

```bash
# Verify parser libraries are installed
python -c "
import pymupdf
import pymupdf4llm
from docx import Document
from bs4 import BeautifulSoup
import tiktoken
from tabulate import tabulate
print('All parser libraries installed successfully')
"
```

**Parser Support:**
- PDF: `pymupdf>=1.23.0`, `pymupdf4llm>=0.0.5`
- DOCX: `python-docx>=0.8.11`
- HTML: `beautifulsoup4>=4.12.0`, `lxml>=4.9.0`
- CSV: `tabulate>=0.9.0`
- TXT: Built-in

### Redis Job Queue Setup

Document ingestion uses Redis for job queue management:

```bash
# Start Redis (if not running)
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine

# Verify Redis connection
redis-cli ping
# Expected: PONG

# Check queue status
redis-cli LLEN job_queue
```

### API Endpoints

#### Upload Document

```bash
# Upload PDF document
curl -X POST "http://localhost:8000/api/v1/ingestion/upload" \
  -H "X-API-Key: your-api-key-here" \
  -F "file=@document.pdf" \
  -F "taxonomy_path=Technology,AI,Machine Learning" \
  -F "source_url=https://example.com/document.pdf" \
  -F "author=John Doe" \
  -F "language=en" \
  -F "priority=5"

# Response (HTTP 202):
{
  "job_id": "550e8400-e29b-41d4-a716-446655440005",
  "status": "pending",
  "estimated_completion_minutes": 2,
  "message": "Document accepted for processing"
}
```

**Supported File Formats:**
- `pdf`: PDF documents (up to 50MB)
- `docx`: Microsoft Word documents
- `csv`: CSV data files
- `html`: HTML web pages
- `txt`: Plain text files

#### Check Job Status

```bash
# Poll job status
curl -X GET "http://localhost:8000/api/v1/ingestion/status/{job_id}" \
  -H "X-API-Key: your-api-key-here"

# Response (processing):
{
  "job_id": "550e8400-e29b-41d4-a716-446655440005",
  "command_id": "550e8400-e29b-41d4-a716-446655440008",
  "status": "processing",
  "progress_percentage": 45.0,
  "current_stage": "Generating embeddings",
  "chunks_processed": 45,
  "total_chunks": 100,
  "started_at": "2025-01-14T12:00:00Z",
  "estimated_completion_at": "2025-01-14T12:02:00Z"
}

# Response (completed):
{
  "job_id": "550e8400-e29b-41d4-a716-446655440005",
  "status": "completed",
  "progress_percentage": 100.0,
  "chunks_processed": 100,
  "total_chunks": 100,
  "completed_at": "2025-01-14T12:02:00Z"
}
```

### Processing Pipeline

Document ingestion follows this pipeline:

1. **File Validation** - Format detection, size check (50MB limit)
2. **Content Extraction** - Parser-specific extraction (PDF, DOCX, CSV, HTML, TXT)
3. **Intelligent Chunking** - 500 tokens per chunk, 128 token overlap (tiktoken-based)
4. **PII Detection** - Korean patterns (resident number, phone, email, etc.)
5. **Embedding Generation** - OpenAI text-embedding-3-large (1536-dim, default)
6. **Vector Storage** - PostgreSQL with pgvector + BM25 index

### Environment Variables

Add these to your `.env` file:

```bash
# LLM API Keys (at least one required)
OPENAI_API_KEY=sk-proj-...          # For embeddings
GEMINI_API_KEY=...                  # Optional fallback

# Redis (required for job queue and caching)
REDIS_URL=redis://localhost:6379/0

# Document Processing (see .env.example for full configuration)
MAX_FILE_SIZE_MB=50                 # Maximum upload file size
CHUNK_SIZE=500                      # Tokens per chunk (default in code)
CHUNK_OVERLAP=128                   # Token overlap between chunks
```

### Troubleshooting

**Issue: "Failed to initialize parser for pdf"**

```bash
# Reinstall PDF parser
pip install --upgrade pymupdf pymupdf4llm

# Test PDF parser
python -c "import fitz; print(fitz.__doc__)"
```

**Issue: "Redis connection failed"**

```bash
# Check Redis is running
redis-cli ping

# Check Redis connection in Python
python -c "
import redis
r = redis.Redis(host='localhost', port=6379)
print(r.ping())
"
```

**Issue: "Embedding generation failed"**

```bash
# Verify OpenAI API key
echo $OPENAI_API_KEY

# Test embedding API (using default model)
python -c "
from openai import OpenAI
client = OpenAI()
response = client.embeddings.create(
    model='text-embedding-3-large',
    input='test'
)
print(f'Embedding dimension: {len(response.data[0].embedding)}')
print(f'Model: text-embedding-3-large')
"
# Expected: Embedding dimension: 1536
```

## Support

- **Issues**: https://github.com/your-org/dt-rag/issues
- **Documentation**: See `README.md` and `PRODUCTION_DEPLOYMENT_REPORT.md`
- **Production Readiness Check**: `python production_readiness_check.py`

---

**Last Updated**: 2025-10-02
**Version**: v1.8.1
