# Security Framework Deployment Guide

This guide covers deploying the Dynamic Taxonomy RAG Security Framework v1.8.1 in various environments.

## 🚀 Quick Start (Development)

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Local Development Setup

1. **Clone and Setup**
```bash
git clone <repository-url>
cd dt-rag
pip install -r apps/security/requirements.txt
```

2. **Environment Configuration**
```bash
export SECURITY_LEVEL=development
export JWT_SECRET=dev-secret-key-change-in-production
export DATABASE_URL=postgresql://user:pass@localhost/dtrag_dev
export REDIS_URL=redis://localhost:6379/0
```

3. **Initialize Security Framework**
```bash
python apps/security/scripts/init_security.py \
    --security-level development \
    --admin-username admin@localhost \
    --admin-password AdminPass123!
```

4. **Start Development Server**
```bash
uvicorn apps.security.main:app --reload --host 0.0.0.0 --port 8000
```

## 🐳 Docker Deployment

### Development Environment

```bash
cd apps/security/docker
docker-compose up -d
```

This starts:
- Security API (port 8000)
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- Nginx reverse proxy (ports 80/443)
- Prometheus monitoring (port 9090)
- Grafana dashboards (port 3000)

### Production Environment

1. **Prepare Environment Variables**
```bash
# Create .env file
cat > .env << EOF
JWT_SECRET=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 24)
REDIS_PASSWORD=$(openssl rand -base64 24)
GRAFANA_PASSWORD=$(openssl rand -base64 16)
SECURITY_LEVEL=production
EOF
```

2. **Deploy with Production Configuration**
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## ☸️ Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (1.25+)
- kubectl configured
- Helm 3.x

### Deploy with Helm

1. **Add Helm Repository**
```bash
helm repo add dtrag-security ./k8s/helm
helm repo update
```

2. **Install Security Framework**
```bash
helm install dtrag-security dtrag-security/security-framework \
    --namespace dtrag-security \
    --create-namespace \
    --set security.level=production \
    --set security.jwtSecret="$(openssl rand -base64 32)" \
    --set postgresql.auth.password="$(openssl rand -base64 24)"
```

### Manual Kubernetes Deployment

1. **Create Namespace**
```bash
kubectl create namespace dtrag-security
```

2. **Deploy Components**
```bash
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/secrets/
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/
kubectl apply -f k8s/ingress/
```

## 🔒 Production Security Hardening

### 1. SSL/TLS Configuration

**Generate SSL Certificates**
```bash
# Self-signed for testing
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout apps/security/docker/ssl/server.key \
    -out apps/security/docker/ssl/server.crt

# Let's Encrypt for production
certbot certonly --standalone -d your-domain.com
```

**Nginx SSL Configuration**
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/server.crt;
    ssl_certificate_key /etc/nginx/ssl/server.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    location / {
        proxy_pass http://security-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. Database Security

**PostgreSQL Configuration**
```bash
# Enable SSL
echo "ssl = on" >> /var/lib/postgresql/data/postgresql.conf

# Restrict connections
echo "host all all 0.0.0.0/0 md5" > /var/lib/postgresql/data/pg_hba.conf

# Enable audit logging
echo "log_statement = 'all'" >> /var/lib/postgresql/data/postgresql.conf
```

**Database Encryption at Rest**
```bash
# Enable transparent data encryption
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = 'server.crt';
ALTER SYSTEM SET ssl_key_file = 'server.key';
```

### 3. Application Security

**Environment Variables (Production)**
```bash
# Core security
export SECURITY_LEVEL=production
export JWT_SECRET="$(openssl rand -base64 32)"
export ENABLE_MFA=true
export ENABLE_AUDIT_ENCRYPTION=true
export ENABLE_CSRF_PROTECTION=true

# Database encryption
export ENABLE_DATABASE_ENCRYPTION=true
export DATABASE_ENCRYPTION_KEY="$(openssl rand -base64 32)"

# Rate limiting
export RATE_LIMIT_REQUESTS=100
export RATE_LIMIT_WINDOW=3600

# PII detection
export PII_CONFIDENCE_THRESHOLD=0.9
export ENABLE_PII_CONTEXT_ANALYSIS=true
```

## 📊 Monitoring & Observability

### 1. Prometheus Metrics

The security framework exposes metrics at `/security/metrics`:

- Authentication metrics (success/failure rates)
- PII detection statistics
- Vulnerability scan results
- Audit log integrity checks
- Performance metrics

### 2. Grafana Dashboards

Pre-configured dashboards available:

- **Security Overview**: High-level security metrics
- **Authentication**: Login attempts, failures, MFA usage
- **PII Detection**: Data privacy compliance metrics
- **Audit Trail**: Log integrity and compliance status
- **Vulnerability Management**: Scan results and remediation

### 3. Alerting Rules

Configure alerts for:

```yaml
# prometheus-alerts.yml
groups:
- name: security-alerts
  rules:
  - alert: HighFailedLoginRate
    expr: rate(security_auth_failures_total[5m]) > 0.1
    for: 2m
    annotations:
      summary: High failed login rate detected

  - alert: PIIDataExposure
    expr: security_pii_exposures_total > 0
    for: 0m
    annotations:
      summary: PII data exposure detected

  - alert: VulnerabilityDetected
    expr: security_vulnerabilities_critical_total > 0
    for: 0m
    annotations:
      summary: Critical vulnerability detected
```

## 🔄 Backup & Recovery

### 1. Database Backup

**Automated PostgreSQL Backup**
```bash
#!/bin/bash
# backup-security-db.sh
BACKUP_DIR="/backups/security"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

pg_dump -h postgres -U dtrag dtrag_security \
    | gzip > "${BACKUP_DIR}/security_backup_${TIMESTAMP}.sql.gz"

# Encrypt backup
gpg --symmetric --cipher-algo AES256 \
    "${BACKUP_DIR}/security_backup_${TIMESTAMP}.sql.gz"
```

**Backup Schedule (cron)**
```bash
# Daily backup at 2 AM
0 2 * * * /opt/scripts/backup-security-db.sh

# Weekly full backup
0 1 * * 0 /opt/scripts/full-backup.sh
```

### 2. Audit Log Backup

```bash
#!/bin/bash
# backup-audit-logs.sh
AUDIT_DIR="/app/audit_logs"
BACKUP_DIR="/backups/audit"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

tar -czf "${BACKUP_DIR}/audit_logs_${TIMESTAMP}.tar.gz" "${AUDIT_DIR}"

# Verify integrity
python -m apps.security.audit.verify_backup \
    "${BACKUP_DIR}/audit_logs_${TIMESTAMP}.tar.gz"
```

### 3. Configuration Backup

```bash
#!/bin/bash
# backup-config.sh
kubectl get configmaps -n dtrag-security -o yaml > config-backup.yaml
kubectl get secrets -n dtrag-security -o yaml > secrets-backup.yaml
```

## 🚀 Scaling & Performance

### 1. Horizontal Scaling

**Security API Scaling**
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: security-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: security-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 2. Database Performance

**PostgreSQL Optimization**
```sql
-- Connection pooling
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';

-- Audit table partitioning
CREATE TABLE audit_logs_y2024m01 PARTITION OF audit_logs
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

**Redis Optimization**
```bash
# Memory optimization
redis-cli CONFIG SET maxmemory 512mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Persistence tuning
redis-cli CONFIG SET save "900 1 300 10 60 10000"
```

### 3. Caching Strategy

```python
# Application-level caching
@cached(ttl=300)  # 5 minutes
async def get_user_permissions(user_id: str):
    return await rbac.get_user_permissions(user_id)

@cached(ttl=3600)  # 1 hour
async def get_pii_patterns():
    return await pii_detector.load_patterns()
```

## 🔧 Maintenance & Updates

### 1. Security Updates

**Automated Security Scanning**
```bash
#!/bin/bash
# security-update.sh

# Update vulnerability database
python -m apps.security.scanning.update_databases

# Run security scan
python -m apps.security.scanning.scan_system

# Generate security report
python -m apps.security.reporting.generate_report --type security
```

### 2. Database Maintenance

```sql
-- Regular maintenance
VACUUM ANALYZE audit_logs;
REINDEX TABLE audit_logs;

-- Archive old data
DELETE FROM audit_logs
WHERE created_at < NOW() - INTERVAL '7 years';
```

### 3. Log Rotation

```bash
# logrotate configuration
/app/audit_logs/*.log {
    daily
    missingok
    rotate 365
    compress
    notifempty
    create 0644 dtrag dtrag
    postrotate
        systemctl reload dtrag-security
    endscript
}
```

## 🚨 Incident Response

### 1. Security Incident Playbook

**Preparation**
```bash
# Create incident response team
kubectl create clusterrole incident-responder \
    --verb=get,list,watch,create,update,patch \
    --resource=pods,services,configmaps,secrets

# Prepare forensic tools
docker build -t security-forensics tools/forensics/
```

**Detection & Analysis**
```bash
# Check security alerts
curl -s http://grafana:3000/api/alerts | jq '.[] | select(.state == "alerting")'

# Analyze audit logs
python -m apps.security.audit.analyze_incident \
    --start "2024-01-01 00:00:00" \
    --end "2024-01-01 23:59:59"

# Export forensic data
python -m apps.security.forensics.export_evidence \
    --incident-id INC-2024-001 \
    --output /tmp/evidence.zip
```

**Containment**
```bash
# Disable compromised user
python -m apps.security.auth.disable_user --user-id user123

# Block malicious IPs
kubectl patch configmap security-config \
    --patch '{"data":{"blocked_ips":"192.168.1.100,10.0.0.50"}}'

# Rotate secrets
kubectl create secret generic jwt-secret \
    --from-literal=secret="$(openssl rand -base64 32)" \
    --dry-run=client -o yaml | kubectl apply -f -
```

### 2. Disaster Recovery

**Complete System Recovery**
```bash
#!/bin/bash
# disaster-recovery.sh

# Restore database
gunzip -c /backups/security/latest.sql.gz | psql -h postgres -U dtrag dtrag_security

# Restore audit logs
tar -xzf /backups/audit/latest.tar.gz -C /app/audit_logs/

# Verify integrity
python -m apps.security.audit.verify_integrity

# Restart services
kubectl rollout restart deployment/security-api
```

## 📋 Compliance Checklists

### GDPR Compliance
- [ ] Data processing activities registered
- [ ] Consent management implemented
- [ ] Data subject rights automated
- [ ] Breach notification system active
- [ ] Privacy by design implemented
- [ ] Data retention policies enforced

### CCPA Compliance
- [ ] Consumer privacy rights implemented
- [ ] Data sales tracking disabled
- [ ] Opt-out mechanisms available
- [ ] Privacy notices updated
- [ ] Third-party data sharing monitored

### PIPA Compliance (Korean)
- [ ] Personal information protection measures
- [ ] Consent requirements implemented
- [ ] Data retention policies compliant
- [ ] Breach notification procedures
- [ ] Privacy officer designated

### Security Standards
- [ ] OWASP Top 10 protections implemented
- [ ] Vulnerability scanning automated
- [ ] Penetration testing scheduled
- [ ] Security training completed
- [ ] Incident response plan tested
- [ ] Business continuity plan verified

## 📞 Support & Troubleshooting

### Common Issues

1. **High Memory Usage**
```bash
# Check memory usage
kubectl top pods -n dtrag-security

# Scale up resources
kubectl patch deployment security-api -p '{"spec":{"template":{"spec":{"containers":[{"name":"security-api","resources":{"requests":{"memory":"512Mi"}}}]}}}}'
```

2. **Database Connection Issues**
```bash
# Check database connectivity
kubectl exec -it deploy/security-api -- pg_isready -h postgres

# Restart database
kubectl rollout restart deployment/postgres
```

3. **Audit Log Integrity Errors**
```bash
# Verify audit trail
python -m apps.security.audit.verify_integrity --repair

# Rebuild hash chain
python -m apps.security.audit.rebuild_chain --from-sequence 12345
```

### Getting Help

- **Documentation**: `/docs` endpoint when running
- **API Reference**: `/redoc` endpoint
- **Health Status**: `/security/status` endpoint
- **Metrics**: `/security/metrics` endpoint

For critical security issues, contact the security team immediately.