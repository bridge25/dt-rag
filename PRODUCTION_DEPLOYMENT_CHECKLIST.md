# Production Deployment Checklist

## 배포 일자: 2025-10-08
## 버전: v1.8.1

---

## ✅ 완료된 사항

### 1. Infrastructure
- [x] PostgreSQL 16 with pgvector extension (running on port 5432)
- [x] Redis 7 for caching and rate limiting (running on port 6379)
- [x] Docker Compose orchestration configured
- [x] Health checks implemented for all services
- [x] Volume persistence configured (postgres_data, redis_data)

### 2. Database
- [x] All migrations applied (version: 0010)
- [x] API key tables created (api_keys, api_key_usage, api_key_audit_log)
- [x] Taxonomy tables created
- [x] Document and chunk tables with pgvector support
- [x] Admin API key created (Initial Admin Key)

### 3. Security
- [x] Database-backed API key authentication
- [x] PBKDF2 password hashing (100,000 iterations)
- [x] Rate limiting with Redis (Fixed Window algorithm)
- [x] CORS configuration with explicit origins
- [x] Security audit logging
- [x] API key validation with entropy checks

### 4. API Features
- [x] Health check endpoint with database/Redis status
- [x] Search endpoints (hybrid BM25 + vector)
- [x] Classification with HITL support
- [x] Document ingestion pipeline
- [x] Taxonomy management
- [x] Agent factory system
- [x] Monitoring endpoints
- [x] Admin API key management endpoints

### 5. Frontend
- [x] Next.js production build configured
- [x] API client with automatic API key injection
- [x] Dashboard with system status monitoring
- [x] Docker containerization

---

## ⚠️ Critical Issues - MUST FIX BEFORE PRODUCTION

### 1. 보안 설정 강화
- [ ] **ENABLE_TEST_API_KEYS=false로 변경** (현재: true)
  - 위치: docker-compose.yml line 79
  - 현재 상태: 테스트 API 키가 활성화되어 있어 보안 위험
  - 조치: Production 환경에서는 반드시 false로 설정

### 2. 레거시 API 키 제거
- [ ] **deps.py에서 ALLOWED_TEST_KEYS 제거 또는 조건부 처리**
  - 위치: apps/api/deps.py:258-261
  - 문제: 약한 패턴의 레거시 키가 하드코딩되어 있음
  - 조치: ENABLE_TEST_API_KEYS=false일 때 완전히 비활성화

### 3. SECRET_KEY 관리
- [ ] **SECRET_KEY를 환경 변수로만 관리**
  - 현재: docker-compose.yml에 기본값 설정됨
  - 조치: .env 파일에서만 관리하고 docker-compose.yml에서 기본값 제거
  - 보안: 최소 256비트 엔트로피 필요

### 4. Frontend API URL 설정
- [ ] **NEXT_PUBLIC_API_URL을 외부 도메인으로 변경**
  - 현재: http://localhost:8000
  - 문제: 브라우저에서 접근 불가
  - 조치: 실제 API 도메인 또는 리버스 프록시 URL로 변경

---

## 🔧 권장 사항 - Production 최적화

### 1. 환경 변수 분리
- [ ] .env.production 파일 생성 및 관리
- [ ] 민감 정보 시크릿 관리 시스템으로 이관 (AWS Secrets Manager, Vault 등)
- [ ] GEMINI_API_KEY, OPENAI_API_KEY 검증

### 2. 모니터링 설정
- [ ] Sentry DSN 설정 (현재: 비어있음)
- [ ] Langfuse 설정 검증 (현재: 키 없음)
- [ ] 로그 수집 및 중앙화 (ELK, CloudWatch 등)
- [ ] 메트릭 수집 (Prometheus, Grafana)

### 3. 백업 전략
- [ ] PostgreSQL 자동 백업 설정
  - 일일 전체 백업
  - 트랜잭션 로그 백업
  - 백업 보관 정책 (7일/30일/90일)
- [ ] Redis AOF 영구 저장 검증
- [ ] 복구 절차 문서화 및 테스트

### 4. 성능 최적화
- [ ] Database connection pool 튜닝
  - 현재: pool_size=20, max_overflow=30
  - 모니터링 후 조정 필요
- [ ] Redis connection pool 최적화
  - 현재: max_connections=10
- [ ] Rate limit 정책 검토
  - GET: 100/min, POST: 50/min
  - Production 트래픽에 맞게 조정

### 5. 네트워크 보안
- [ ] HTTPS 설정 (리버스 프록시 또는 로드 밸런서)
- [ ] SSL/TLS 인증서 설정
- [ ] 방화벽 규칙 설정
- [ ] DDoS 방어 설정

### 6. High Availability
- [ ] Multi-container deployment (replicas)
- [ ] Load balancer 설정
- [ ] Database replication (read replicas)
- [ ] Redis Sentinel or Cluster

### 7. 컴플라이언스
- [ ] GDPR 준수 검토 (PII 처리)
- [ ] 데이터 보존 정책 설정
- [ ] 감사 로그 보관 정책
- [ ] 사용자 데이터 삭제 절차

---

## 📋 배포 전 테스트 체크리스트

### API 테스트
- [ ] Health check 엔드포인트 (/health)
- [ ] Search 엔드포인트 (hybrid search)
- [ ] Classification 엔드포인트
- [ ] Document upload
- [ ] API key authentication
- [ ] Rate limiting

### Frontend 테스트
- [ ] 브라우저에서 http://localhost:3000 접근
- [ ] Dashboard 페이지 데이터 로딩 확인
- [ ] Search 기능 테스트
- [ ] Document upload 테스트
- [ ] 모든 페이지 네비게이션 테스트

### Integration 테스트
- [ ] E2E workflow 테스트
- [ ] Database transaction 무결성
- [ ] Cache invalidation 검증
- [ ] Error handling 및 fallback

### 보안 테스트
- [ ] API key 없이 접근 시도 (403 예상)
- [ ] 약한 API key로 접근 시도 (거부 예상)
- [ ] Rate limit 초과 테스트 (429 예상)
- [ ] SQL injection 방어 테스트
- [ ] XSS 방어 테스트

---

## 🚀 배포 절차

### 1. Pre-deployment
```bash
# 1. 환경 변수 검증
grep -E "ENABLE_TEST_API_KEYS|SECRET_KEY|NEXT_PUBLIC_API_URL" .env

# 2. 데이터베이스 백업
docker exec dt_rag_postgres pg_dump -U postgres dt_rag > backup_$(date +%Y%m%d_%H%M%S).sql

# 3. 현재 상태 스냅샷
docker ps > deployment_snapshot.txt
docker logs dt_rag_api > api_logs_pre_deployment.txt
```

### 2. Deployment
```bash
# 1. ENABLE_TEST_API_KEYS=false 설정
# .env 파일 수정

# 2. 컨테이너 재시작
docker-compose down
docker-compose up -d --build

# 3. Health check 대기
for i in {1..30}; do
  curl -s http://localhost:8000/health | jq '.status'
  sleep 2
done
```

### 3. Post-deployment
```bash
# 1. 서비스 상태 확인
docker ps --filter "name=dt_rag"

# 2. API 테스트 (관리자 키 사용)
curl -H "X-API-Key: {ADMIN_KEY}" http://localhost:8000/api/v1/admin/api-keys/

# 3. Frontend 접근 확인
curl http://localhost:3000

# 4. 로그 모니터링 시작
docker logs -f dt_rag_api
```

### 4. Rollback 절차 (문제 발생 시)
```bash
# 1. 이전 버전으로 복구
docker-compose down
git checkout {previous_stable_commit}
docker-compose up -d

# 2. 데이터베이스 복구 (필요시)
docker exec -i dt_rag_postgres psql -U postgres dt_rag < backup_YYYYMMDD_HHMMSS.sql

# 3. 상태 확인
curl http://localhost:8000/health
```

---

## 📞 운영 연락처

### 긴급 연락망
- 시스템 관리자: [연락처]
- 데이터베이스 관리자: [연락처]
- 보안 담당자: [연락처]

### 모니터링 대시보드
- API Health: http://localhost:8000/health
- Monitoring: http://localhost:8000/monitoring/health
- Frontend: http://localhost:3000

---

## 📝 변경 이력

### 2025-10-08 - Phase 8 완료
- Redis 기반 커스텀 rate limiter 구현
- Database-backed API key management
- API key CRUD endpoints (admin)
- Health endpoint에 database/Redis 상태 추가
- 레거시 API 키 임시 지원 (테스트 모드)

---

## ⚡ Quick Fix Commands

### ENABLE_TEST_API_KEYS 비활성화
```bash
# docker-compose.yml 수정 후
docker-compose restart api
```

### 새 Admin API Key 생성
```bash
curl -X POST http://localhost:8000/api/v1/admin/api-keys/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: {CURRENT_ADMIN_KEY}" \
  -d '{
    "name": "Production Admin Key",
    "description": "Production administrator key",
    "scope": "admin",
    "rate_limit": 10000
  }'
```

### 레거시 API 키 revoke
```bash
curl -X DELETE http://localhost:8000/api/v1/admin/api-keys/test_key_002 \
  -H "X-API-Key: {ADMIN_KEY}" \
  -d '{"reason": "Security policy: Remove test keys from production"}'
```

---

**Status**: 🟡 Ready for Production with Critical Fixes Required

**Next Steps**:
1. ENABLE_TEST_API_KEYS=false 설정
2. 레거시 API 키 제거
3. Frontend API URL 설정
4. 보안 테스트 수행
5. Production 배포
