# Production Setup Guide

**DT-RAG v1.8.1 Production Deployment**

---

## 🎯 Quick Start

### Minimal Production Configuration (5 steps)

```bash
# 1. Clone and navigate to project
cd /path/to/dt-rag

# 2. Copy production environment template
cp .env.example .env.production

# 3. Edit critical variables (REQUIRED)
nano .env.production
# Set: ENABLE_TEST_API_KEYS=false
# Set: SECRET_KEY=<generate-secure-key>
# Set: POSTGRES_PASSWORD=<strong-password>
# Set: GEMINI_API_KEY=<your-key>
# Set: OPENAI_API_KEY=<your-key>

# 4. Deploy with production config
docker-compose --env-file .env.production up -d

# 5. Create first admin API key
./scripts/create_first_admin_key.sh
```

---

## 📋 Pre-Deployment Checklist

### 1. System Requirements

**Minimum Hardware**:
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB SSD
- Network: 100 Mbps

**Recommended Hardware**:
- CPU: 8+ cores
- RAM: 16GB+
- Storage: 200GB+ SSD (NVMe preferred)
- Network: 1 Gbps

**Software Requirements**:
- Docker Engine 24.0+
- Docker Compose 2.20+
- Linux kernel 5.10+ (for optimal performance)
- SSL certificates (for HTTPS)

---

### 2. Environment Variables Configuration

Create `.env.production` file:

```bash
# ===== CRITICAL SECURITY SETTINGS =====
# NEVER use test keys in production
ENABLE_TEST_API_KEYS=false

# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<GENERATE_SECURE_256_BIT_KEY>

# Strong password (16+ characters, mixed case, numbers, symbols)
POSTGRES_PASSWORD=<GENERATE_STRONG_PASSWORD>

# ===== DATABASE =====
DATABASE_URL=postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/dt_rag
POSTGRES_PORT=5432

# ===== REDIS =====
REDIS_URL=redis://redis:6379
REDIS_PORT=6379

# ===== LLM API KEYS =====
# Get from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>

# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>

# ===== ENVIRONMENT =====
ENVIRONMENT=production
NODE_ENV=production

# ===== FRONTEND =====
# IMPORTANT: Change to your actual domain
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
# Will be set after first admin key creation
NEXT_PUBLIC_API_KEY=<TO_BE_GENERATED>

# ===== MONITORING (Optional but Recommended) =====
# Get from: https://sentry.io
SENTRY_DSN=

# Get from: https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com

# ===== CORS (Adjust for your domains) =====
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# ===== RATE LIMITING =====
# Adjust based on expected traffic
RATE_LIMIT_ENABLED=true
```

---

### 3. Generate Secure Keys

#### Generate SECRET_KEY
```bash
# Option 1: Python
python -c "import secrets; print(secrets.token_hex(32))"

# Option 2: OpenSSL
openssl rand -hex 32
```

#### Generate Strong Database Password
```bash
# Option 1: Python (alphanumeric + special chars)
python -c "import secrets, string; chars=string.ascii_letters+string.digits+'!@#$%^&*'; print(''.join(secrets.choice(chars) for _ in range(32)))"

# Option 2: OpenSSL
openssl rand -base64 32
```

---

### 4. Docker Compose Configuration

Update `docker-compose.yml` for production:

```yaml
services:
  api:
    environment:
      # Remove or comment out default test key setting
      # - ENABLE_TEST_API_KEYS=${ENABLE_TEST_API_KEYS:-true}  # REMOVE THIS
      - ENABLE_TEST_API_KEYS=false  # ADD THIS

    # Add resource limits
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
        reservations:
          cpus: '2'
          memory: 2G

    # Add restart policy
    restart: always

  postgres:
    # Add resource limits
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

    # Add volume for backups
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups

    restart: always

  redis:
    # Add maxmemory policy
    command: >
      redis-server
      --appendonly yes
      --maxmemory 1gb
      --maxmemory-policy allkeys-lru

    deploy:
      resources:
        limits:
          memory: 1G

    restart: always
```

---

## 🚀 Deployment Steps

### Step 1: Prepare Environment

```bash
# 1. Create production directory
sudo mkdir -p /opt/dt-rag
cd /opt/dt-rag

# 2. Clone repository
git clone https://github.com/your-org/dt-rag.git .
git checkout v1.8.1  # Use stable release

# 3. Create production environment file
cp .env.example .env.production

# 4. Edit environment variables
nano .env.production
# Follow the configuration guide above
```

### Step 2: Security Setup

```bash
# 1. Set proper file permissions
chmod 600 .env.production
chmod 600 .env

# 2. Create secure directories
mkdir -p backups logs
chmod 700 backups
chmod 755 logs

# 3. Set ownership (if using non-root user)
sudo chown -R $USER:$USER /opt/dt-rag
```

### Step 3: Database Initialization

```bash
# 1. Start database only
docker-compose up -d postgres redis

# 2. Wait for database to be ready
docker-compose exec postgres pg_isready -U postgres

# 3. Run migrations
docker-compose run --rm api alembic upgrade head

# 4. Verify tables created
docker-compose exec postgres psql -U postgres -d dt_rag -c "\dt"
```

### Step 4: Create First Admin Key

Create a script `scripts/create_first_admin_key.sh`:

```bash
#!/bin/bash
# Create first admin API key for production

set -e

echo "🔐 Creating first admin API key for production..."

# Start API temporarily
docker-compose up -d api

# Wait for API to be healthy
echo "⏳ Waiting for API to be healthy..."
for i in {1..30}; do
  if docker-compose exec api curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is healthy"
    break
  fi
  sleep 2
done

# Create admin key directly in database
docker-compose exec postgres psql -U postgres -d dt_rag <<-EOSQL
-- Generate admin key
DO \$\$
DECLARE
  admin_key TEXT := 'admin_' || encode(gen_random_bytes(32), 'base64');
  admin_key_hash TEXT;
BEGIN
  -- Hash the key (PBKDF2 equivalent in PostgreSQL)
  admin_key_hash := encode(digest(admin_key || 'salt', 'sha256'), 'hex');

  -- Insert into database
  INSERT INTO api_keys (
    key_id, key_hash, name, description, scope, permissions,
    rate_limit, is_active, created_at
  ) VALUES (
    encode(gen_random_bytes(16), 'hex'),
    admin_key_hash,
    'Production Admin Key',
    'Initial admin key for production deployment',
    'admin',
    ARRAY['*'],
    10000,
    true,
    NOW()
  );

  -- Output the key (ONLY TIME IT WILL BE SHOWN)
  RAISE NOTICE 'Admin API Key (SAVE THIS): %', admin_key;
END\$\$;
EOSQL

echo ""
echo "⚠️  IMPORTANT: Save the admin key shown above!"
echo "⚠️  It will NOT be shown again!"
echo ""
```

Make it executable:
```bash
chmod +x scripts/create_first_admin_key.sh
./scripts/create_first_admin_key.sh
```

**Alternative: Use Python script**

Create `scripts/create_admin_key.py`:

```python
#!/usr/bin/env python3
"""Create first admin API key for production"""
import asyncio
import sys
sys.path.insert(0, '/app')

from apps.api.database import async_session
from apps.api.security.api_key_storage import APIKeyManager, APIKeyCreateRequest

async def create_admin_key():
    async with async_session() as db:
        manager = APIKeyManager(db)

        request = APIKeyCreateRequest(
            name="Production Admin Key",
            description="Initial admin key for production",
            owner_id="system",
            permissions=["*"],
            scope="admin",
            rate_limit=10000
        )

        plaintext_key, key_info = await manager.create_api_key(
            request=request,
            created_by="system",
            client_ip="127.0.0.1"
        )

        print("\n" + "="*80)
        print("🔐 ADMIN API KEY (SAVE THIS - SHOWN ONLY ONCE)")
        print("="*80)
        print(f"\nKey: {plaintext_key}")
        print(f"Key ID: {key_info.key_id}")
        print(f"Scope: {key_info.scope}")
        print(f"Rate Limit: {key_info.rate_limit}/hour")
        print("\n" + "="*80)
        print("⚠️  Store this key in a secure location (password manager, vault)")
        print("⚠️  Set NEXT_PUBLIC_API_KEY to this value for frontend")
        print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(create_admin_key())
```

Run:
```bash
docker-compose exec api python scripts/create_admin_key.py
```

### Step 5: Full Deployment

```bash
# 1. Build and start all services
docker-compose --env-file .env.production up -d --build

# 2. Verify all services are healthy
docker-compose ps

# Expected output:
# NAME                STATUS
# dt_rag_api         Up (healthy)
# dt_rag_postgres    Up (healthy)
# dt_rag_redis       Up (healthy)
# dt_rag_frontend    Up

# 3. Check logs for any errors
docker-compose logs -f --tail=100
```

### Step 6: Post-Deployment Verification

```bash
# 1. Health check
curl http://localhost:8000/health

# Expected:
# {"status":"healthy","database":"connected","redis":"connected",...}

# 2. Test API authentication (use your admin key)
curl -H "X-API-Key: admin_YOUR_KEY_HERE" \
  http://localhost:8000/api/v1/admin/api-keys/

# Expected: JSON list of API keys

# 3. Test rate limiting
for i in {1..6}; do
  curl -H "X-API-Key: invalid_key" http://localhost:8000/api/v1/search/ \
    -X POST -d '{"q":"test"}' 2>&1 | grep -o "403\|429" || echo "Request $i"
done

# Expected: First 5 return 403, 6th should show rate limiting

# 4. Frontend check
curl http://localhost:3000
# Should return HTML
```

---

## 🔒 Security Hardening

### 1. HTTPS Setup (REQUIRED for production)

**Option A: Nginx Reverse Proxy**

Create `nginx.conf`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # API backend
    location /api/ {
        proxy_pass http://dt_rag_api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend
    location / {
        proxy_pass http://dt_rag_frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Option B: Traefik (Docker-native)**

Add to `docker-compose.yml`:
```yaml
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=false"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=your@email.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"
    networks:
      - dt_rag_network

  api:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.yourdomain.com`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"
```

### 2. Firewall Configuration

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable

# Block direct access to internal ports
sudo ufw deny 5432/tcp     # PostgreSQL
sudo ufw deny 6379/tcp     # Redis
sudo ufw deny 8000/tcp     # API (use reverse proxy)
```

### 3. Docker Security

Update `docker-compose.yml`:
```yaml
services:
  api:
    # Run as non-root user
    user: "1000:1000"

    # Read-only root filesystem
    read_only: true

    # Tmpfs for writable directories
    tmpfs:
      - /tmp
      - /app/.cache

    # Security options
    security_opt:
      - no-new-privileges:true

    # Drop unnecessary capabilities
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

---

## 📊 Monitoring Setup

### 1. Sentry Error Tracking

```bash
# 1. Sign up at https://sentry.io
# 2. Create new project (Python/FastAPI)
# 3. Copy DSN

# 4. Add to .env.production
echo "SENTRY_DSN=https://your-dsn@sentry.io/project" >> .env.production

# 5. Restart API
docker-compose restart api

# 6. Test error reporting
curl -X POST http://localhost:8000/api/v1/search/ \
  -H "X-API-Key: invalid" -d '{"q":"test"}'

# Check Sentry dashboard for error
```

### 2. Langfuse LLM Monitoring

```bash
# 1. Sign up at https://cloud.langfuse.com
# 2. Create project and get keys

# 3. Add to .env.production
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com

# 4. Restart API
docker-compose restart api

# 5. Test LLM call tracking
curl -H "X-API-Key: $ADMIN_KEY" \
  http://localhost:8000/monitoring/llm-costs
```

### 3. Prometheus + Grafana (Optional)

See `docs/monitoring/prometheus-setup.md` for detailed guide.

---

## 💾 Backup Strategy

### Automated Database Backups

Create `scripts/backup.sh`:
```bash
#!/bin/bash
set -e

BACKUP_DIR="/opt/dt-rag/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="dt_rag_backup_${TIMESTAMP}.sql"

echo "🔄 Starting backup: $BACKUP_FILE"

# Create backup
docker-compose exec -T postgres pg_dump -U postgres dt_rag > "${BACKUP_DIR}/${BACKUP_FILE}"

# Compress
gzip "${BACKUP_DIR}/${BACKUP_FILE}"

# Delete backups older than 30 days
find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +30 -delete

echo "✅ Backup completed: ${BACKUP_FILE}.gz"
```

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * /opt/dt-rag/scripts/backup.sh >> /var/log/dt-rag-backup.log 2>&1
```

---

## 🔄 Update Procedure

```bash
# 1. Backup current database
./scripts/backup.sh

# 2. Pull latest code
git fetch origin
git checkout v1.8.2  # New version

# 3. Update dependencies
docker-compose build --no-cache

# 4. Run migrations
docker-compose run --rm api alembic upgrade head

# 5. Restart services with zero-downtime (if using multiple replicas)
docker-compose up -d --no-deps --build api

# 6. Verify health
curl http://localhost:8000/health
```

---

## 🚨 Troubleshooting

### Common Issues

**1. API returns 403 for all requests**
```bash
# Check if ENABLE_TEST_API_KEYS is false
docker-compose exec api env | grep ENABLE_TEST_API_KEYS

# Verify admin key exists
docker-compose exec postgres psql -U postgres -d dt_rag \
  -c "SELECT key_id, name FROM api_keys WHERE scope='admin';"

# Check API logs
docker-compose logs api | grep SECURITY
```

**2. Database connection fails**
```bash
# Check database is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres pg_isready -U postgres

# Check credentials
docker-compose exec api env | grep DATABASE_URL
```

**3. Frontend can't reach API**
```bash
# Check NEXT_PUBLIC_API_URL
docker-compose exec frontend env | grep NEXT_PUBLIC_API_URL

# Test API from frontend container
docker-compose exec frontend wget -qO- http://api:8000/health
```

---

## 📞 Support

- Documentation: `docs/`
- Issues: GitHub Issues
- Security: security@yourdomain.com

---

**Last Updated**: 2025-10-08
**Version**: 1.8.1
**Status**: Production Ready ✅
