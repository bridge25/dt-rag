# DT-RAG Docker Deployment Guide

## Prerequisites

- Docker Engine 20.10+
- Docker Compose V2
- Minimum 8GB RAM
- Minimum 20GB free disk space

## Quick Start

### 1. Environment Setup

Copy and configure environment variables:

```bash
cp .env.docker .env
```

Edit `.env` and set required values:
- `POSTGRES_PASSWORD`: PostgreSQL password (default: postgres)
- `SECRET_KEY`: API secret key (generate secure random string)
- `OPENAI_API_KEY`: OpenAI API key
- `GEMINI_API_KEY`: Google Gemini API key
- `NEXT_PUBLIC_API_KEY`: Frontend API key

### 2. Build Images

Build all services:

```bash
docker compose build
```

Build specific service:

```bash
docker compose build api
docker compose build frontend
```

### 3. Start Services

Start all services in detached mode:

```bash
docker compose up -d
```

View logs:

```bash
docker compose logs -f
docker compose logs -f api
docker compose logs -f frontend
```

### 4. Health Check

Check service status:

```bash
docker compose ps
```

Test API health:

```bash
curl http://localhost:8000/health
```

Test Frontend health:

```bash
curl http://localhost:3000/api/health
```

## Service Architecture

```
┌─────────────────┐
│   Frontend      │  Port 3000
│   (Next.js)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   API           │  Port 8000
│   (FastAPI)     │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐  ┌────────┐
│Postgres│  │ Redis  │
│  5432  │  │  6379  │
└────────┘  └────────┘
```

## Services

### PostgreSQL (Production)
- Image: `pgvector/pgvector:pg16`
- Port: `5432`
- Database: `dt_rag`
- Volume: `postgres_data`

### PostgreSQL (Test)
- Image: `pgvector/pgvector:pg16`
- Port: `5433`
- Database: `dt_rag_test`
- Volume: `postgres_test_data`

### Redis
- Image: `redis:7-alpine`
- Port: `6379`
- Volume: `redis_data`
- Persistence: AOF enabled

### API (Backend)
- Build: `Dockerfile.api`
- Port: `8000`
- Dependencies: PostgreSQL, Redis
- Healthcheck: `/health` endpoint
- Auto-migration: Alembic runs on startup

### Frontend
- Build: `apps/frontend/Dockerfile`
- Port: `3000`
- Dependencies: API service
- Mode: Production standalone build

## Common Operations

### Stop Services

```bash
docker compose down
```

### Restart Service

```bash
docker compose restart api
docker compose restart frontend
```

### View Service Logs

```bash
docker compose logs -f api
docker compose logs -f frontend
```

### Execute Commands in Container

```bash
docker compose exec api bash
docker compose exec postgres psql -U postgres -d dt_rag
```

### Database Operations

Enter PostgreSQL:

```bash
docker compose exec postgres psql -U postgres -d dt_rag
```

Run migrations manually:

```bash
docker compose exec api alembic upgrade head
```

Create migration:

```bash
docker compose exec api alembic revision --autogenerate -m "description"
```

### Clean Reset

Stop and remove all containers, volumes:

```bash
docker compose down -v
```

Rebuild and restart:

```bash
docker compose build --no-cache
docker compose up -d
```

## Production Considerations

### Security

1. Change default passwords in `.env`
2. Use strong `SECRET_KEY` (generate with `openssl rand -hex 32`)
3. Enable HTTPS with reverse proxy (nginx/traefik)
4. Restrict database ports to internal network only

### Performance

1. Adjust PostgreSQL connection pool:
   - `CONNECTION_POOL_SIZE=20`
   - `MAX_OVERFLOW=10`

2. Configure Redis cache expiration

3. Set resource limits in `docker-compose.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Monitoring

1. Enable Sentry:
   - Set `SENTRY_DSN` in `.env`

2. Enable Langfuse:
   - Set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` in `.env`

3. View container stats:

```bash
docker stats
```

### Backup

Backup database:

```bash
docker compose exec postgres pg_dump -U postgres dt_rag > backup.sql
```

Restore database:

```bash
docker compose exec -T postgres psql -U postgres dt_rag < backup.sql
```

Backup volumes:

```bash
docker run --rm -v dt-rag_postgres_data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres_data.tar.gz /data
```

## Troubleshooting

### API Container Won't Start

1. Check logs:
```bash
docker compose logs api
```

2. Verify database connection:
```bash
docker compose exec postgres pg_isready -U postgres
```

3. Check migrations:
```bash
docker compose exec api alembic current
```

### Frontend Build Fails

1. Clear npm cache in container
2. Rebuild without cache:
```bash
docker compose build --no-cache frontend
```

### Database Connection Refused

1. Ensure PostgreSQL is healthy:
```bash
docker compose ps postgres
```

2. Check network:
```bash
docker network inspect dt_rag_dt_rag_network
```

### Port Already in Use

Change ports in `.env`:
```
API_PORT=8001
FRONTEND_PORT=3001
POSTGRES_PORT=5433
REDIS_PORT=6380
```

## Development Mode

For development with hot reload, use local environment instead:

1. Start only database services:
```bash
docker compose up -d postgres postgres-test redis
```

2. Run API locally:
```bash
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
```

3. Run Frontend locally:
```bash
cd apps/frontend
npm run dev
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Build images
        run: docker compose build

      - name: Run tests
        run: docker compose run api pytest

      - name: Deploy
        run: |
          docker compose down
          docker compose up -d
```

## Additional Resources

- API Documentation: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Monitoring Dashboard: http://localhost:3000/monitoring
- HITL Review: http://localhost:3000/hitl
