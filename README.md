# Dynamic Taxonomy RAG - B/C팀 온보딩 단일 진입점

> **System Version**: 2.0.0  
> **API Spec**: v1.8.1  
> **Team**: A팀 (Taxonomy & Data Platform)  
> **Status**: 🚀 Production Ready (B/C팀 온보딩 준비 완료)  
> **Updated**: 2025-01-15 KST

## 🎯 시스템 개요

Dynamic Taxonomy RAG는 지능형 문서 분류 및 검색을 위한 프로덕션 레디 시스템입니다:

### 🚀 핵심 기능 (Day 2 완성)
- **📄 문서 수집 파이프라인**: PDF, Markdown, HTML 자동 파싱
- **🔍 지능형 청킹**: 500자 청크, 128자 오버랩으로 최적화
- **📊 완전한 관찰가능성**: Prometheus 메트릭 + Grafana 대시보드
- **🐳 Docker 배포**: 원클릭 배포 및 스케일링
- **💰 비용 관리**: 일일 $10 예산 한도 자동 모니터링
- **🔒 프로덕션 보안**: 비root 사용자, 다단계 빌드

### 📊 데이터베이스 아키텍처

| 테이블 | 목적 | 핵심 기능 |
|-------|------|----------|
| `taxonomy_nodes` | DAG 노드 정의 | 버전 관리, 정규 계층 구조 |
| `taxonomy_edges` | 부모-자식 관계 | 버전 인식, 순환 방지 |
| `documents` | 원본 문서 | 메타데이터, 체크섬, 콘텐츠 타입 |
| `chunks` | 텍스트 세그먼트 | **int4range 스팬**, 문자 위치 |
| `embeddings` | 벡터 저장소 | **vector(1536)**, BM25 토큰 |
| `doc_taxonomy` | 문서 분류 | 신뢰도 점수, 다중 소스 |
| `ingestion_jobs` | 수집 작업 추적 | 상태 관리, DLQ 지원 |

## 🚀 빠른 시작

### 1. 시스템 요구사항

```bash
# Docker & Docker Compose (필수)
docker --version  # 20.10+
docker-compose --version  # 2.0+

# Python (개발용)
python --version  # 3.11+
```

### 2. 환경 설정

```bash
# 환경 변수 파일 생성
cp .env.example .env
vim .env  # API 키 및 설정 수정

# 필수 설정값:
# - OPENAI_API_KEY (OpenAI API)
# - POSTGRES_PASSWORD (DB 비밀번호)
# - REDIS_PASSWORD (Redis 비밀번호)
```

### 3. 원클릭 배포

```bash
# 개발 환경 배포
./scripts/deploy.sh dev

# 프로덕션 환경 배포  
./scripts/deploy.sh prod
```

배포 완료 후 접속 정보:
- **API 서버**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)
- **pgAdmin**: http://localhost:5050 (dev 환경만)

> ⚠️ **보안 주의**: 프로덕션 배포 시 반드시 Grafana 기본 비밀번호(admin123)를 변경하세요. `docker-compose exec grafana grafana-cli admin reset-admin-password <new-password>`

### 4. 헬스 체크

```bash
# 시스템 상태 확인
./scripts/health-check.sh

# 개별 서비스 확인
curl http://localhost:8000/health        # API 서버
curl http://localhost:8000/system/health # 상세 상태
```

## 📄 문서 수집 API

### 문서 업로드

```bash
# PDF 문서 업로드
curl -X POST "http://localhost:8000/ingest" \
  -F "file=@document.pdf" \
  -H "Content-Type: multipart/form-data"

# 응답 예시:
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "message": "문서 수집 작업이 시작되었습니다"
}
```

### 작업 상태 확인

```bash
# 작업 상태 조회
curl http://localhost:8000/ingest/jobs/{job_id}/status

# 응답 예시:
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "progress": {
    "total_chunks": 15,
    "processed_chunks": 15,
    "failed_chunks": 0
  },
  "metadata": {
    "filename": "document.pdf",
    "file_size": 2048576,
    "page_count": 25
  }
}
```

### 작업 목록 조회

```bash
# 모든 작업 조회
curl http://localhost:8000/ingest/jobs

# 상태별 필터링
curl "http://localhost:8000/ingest/jobs?status=completed&limit=10"
```

## 📊 모니터링 및 관찰가능성

### Prometheus 메트릭

시스템에서 자동 수집되는 주요 메트릭:

```python
# HTTP 요청 메트릭
http_requests_total                    # 총 요청 수
http_request_duration_seconds         # 응답 시간 히스토그램
http_requests_in_progress             # 진행 중 요청 수

# 문서 수집 메트릭
documents_processed_total             # 처리된 문서 수
chunks_created_total                  # 생성된 청크 수
ingestion_job_duration_seconds        # 수집 작업 소요 시간
ingestion_errors_total                # 수집 오류 수

# 시스템 메트릭
api_cost_dollars_daily               # 일일 API 비용
database_connections_active          # 활성 DB 연결 수
```

### NFR (Non-Functional Requirements) 모니터링

시스템이 자동으로 모니터링하는 성능 기준:

| 메트릭 | 기준값 | 위반시 알림 |
|--------|--------|-------------|
| **응답시간 P95** | ≤ 4초 | 5분 간격 체크 |
| **응답시간 P50** | ≤ 1.5초 | 5분 간격 체크 |
| **에러율** | < 1% | 즉시 알림 |
| **일일 비용** | ≤ $10 | 예산 초과시 차단 |

### Grafana 대시보드

http://localhost:3000에서 확인 가능한 대시보드:

1. **시스템 개요**: 전체 성능 및 상태 요약
2. **API 성능**: 응답시간, 처리량, 에러율
3. **문서 수집**: 수집 통계, 실패율, 처리 속도
4. **비용 추적**: 일일/월간 API 비용 추이
5. **인프라 상태**: CPU, 메모리, 디스크 사용률

## 🔧 개발자 가이드

### 로컬 개발 환경

```bash
# Python 가상환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는 venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 마이그레이션
alembic upgrade head

# 개발 서버 시작
uvicorn apps.api.main:app --reload --port 8000
```

### API 엔드포인트

#### 문서 수집
- `POST /ingest` - 문서 업로드 및 수집 시작
- `GET /ingest/jobs/{job_id}/status` - 작업 상태 확인
- `GET /ingest/jobs` - 작업 목록 조회

#### 분류 및 검색 (구현됨)
- `POST /classify` - 문서 자동 분류
```bash
curl -X POST "http://localhost:8000/classify" -H "Content-Type: application/json" \
-d '{"text": "인공지능과 머신러닝"}'
# 응답: {"canonical": ["AI", "ML"], "confidence": 0.85, "alternatives": [...]}
```

- `POST /search` - 하이브리드 검색 (BM25 + Vector)
```bash
curl -X POST "http://localhost:8000/search" -H "Content-Type: application/json" \
-d '{"query": "딥러닝 모델", "limit": 10}'
# 응답: {"results": [...], "total": 25, "query_time_ms": 45}
```

#### 분류 체계 관리
- `GET /taxonomy/{version}/tree` - 분류 체계 트리 조회
```bash
curl "http://localhost:8000/taxonomy/3/tree"
# 응답: {"nodes": [...], "edges": [...], "version": 3}
```

- `GET /taxonomy/{version}/diff/{base}` - 버전 간 차이 비교
```bash
curl "http://localhost:8000/taxonomy/3/diff/2"
# 응답: {"added": [...], "removed": [...], "modified": [...]}
```

- `POST /taxonomy/{version}/rollback` - 이전 버전으로 롤백
```bash
curl -X POST "http://localhost:8000/taxonomy/rollback" -H "Content-Type: application/json" \
-d '{"target_version": 2}'
# 응답: {"success": true, "rollback_time_ms": 1250}
```

#### 시스템 모니터링  
- `GET /health` - 간단한 헬스 체크
- `GET /system/health` - 상세 시스템 상태
- `GET /metrics` - Prometheus 메트릭

## 🔐 인증 및 권한 관리 (Auth & RBAC)

### API 키 인증

모든 API 요청에는 API 키 헤더가 필요합니다:

```bash
curl -H "X-API-Key: your-api-key-here" "http://localhost:8000/classify"
```

### 권한 역할

| 역할 | 권한 | 접근 가능한 엔드포인트 |
|------|------|------------------------|
| **Admin** | 전체 관리 | 모든 엔드포인트 + 롤백/시스템 관리 |
| **Ops** | 운영 관리 | 분류, 검색, 모니터링, HITL 관리 |
| **User** | 기본 사용 | 분류, 검색, 문서 업로드 |

### 에러 응답 및 재시도 정책

#### 403 Forbidden (권한 없음)
```json
{
  "error": "insufficient_permissions",
  "message": "Admin role required for rollback operations",
  "required_role": "Admin",
  "current_role": "User"
}
```

#### 429 Too Many Requests (요청 제한)
```json
{
  "error": "rate_limit_exceeded",
  "message": "API rate limit exceeded",
  "limit": 100,
  "reset_time": "2025-01-15T10:30:00Z",
  "retry_after": 60
}
```

**재시도 지침**: 429 에러 시 `retry_after` 초만큼 대기 후 재시도. 지수 백오프 권장 (1s → 2s → 4s → 8s).

## 🤝 HITL (Human-in-the-Loop) 시스템

### 자동 큐잉 임계값

- **임계값**: `confidence < 0.70` → 자동으로 인간 검토 큐에 추가
- **우선순위**: confidence가 낮을수록 높은 우선순위

### 상태 전이도

```
pending → assigned → reviewing → resolved
   ↓         ↓          ↓         ↓
 (큐 대기)  (검토자 할당) (검토 중)  (완료)
```

### HITL API

#### 대기 중인 항목 조회
```bash
curl -H "X-API-Key: your-key" "http://localhost:8000/hitl/items?status=pending&limit=10"
# 응답: {"items": [...], "total": 25, "avg_confidence": 0.65}
```

#### 검토 완료 처리
```bash
curl -X POST -H "X-API-Key: your-key" -H "Content-Type: application/json" \
"http://localhost:8000/hitl/items/123e4567-e89b-12d3-a456-426614174000/resolve" \
-d '{"canonical": ["AI", "Deep Learning"], "confidence": 0.90, "reviewer_notes": "정확한 분류 확인"}'
# 응답: {"success": true, "updated_taxonomy": true, "learning_applied": true}
```

#### 상태별 통계
```bash
curl -H "X-API-Key: your-key" "http://localhost:8000/hitl/stats"
# 응답: {"pending": 15, "assigned": 3, "reviewing": 2, "resolved_today": 45}
```

## 📋 OpenAPI 스펙 & 클라이언트 생성

### OpenAPI 문서
- **스펙 파일**: `docs/openapi.yaml`
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### TypeScript 클라이언트 생성
```bash
# axios 기반 TypeScript 클라이언트 생성
npx @openapitools/openapi-generator-cli generate -i docs/openapi.yaml -g typescript-axios -o ./clients/typescript
# 사용법: import { DefaultApi } from './clients/typescript'
# const api = new DefaultApi({ basePath: 'http://localhost:8000' })
```

### Python 클라이언트 생성
```bash
# pydantic + requests 기반 Python 클라이언트 생성
openapi-generator-cli generate -i docs/openapi.yaml -g python -o ./clients/python --additional-properties=packageName=dt_rag_client
# 사용법: from dt_rag_client import DefaultApi, Configuration, ApiClient
# api = DefaultApi(ApiClient(Configuration(host='http://localhost:8000')))
```

### 테스트 실행

```bash
# 단위 테스트
pytest tests/ -v

# 커버리지 포함 테스트
pytest tests/ --cov=apps --cov-report=html

# 특정 테스트만 실행
pytest tests/test_ingestion.py -v
```

## 🐳 Docker 배포 상세

### 서비스 구성

docker-compose.yml에 정의된 서비스들:

```yaml
services:
  postgres:     # PostgreSQL + pgvector
  redis:        # Redis 캐시 및 세션
  api:          # FastAPI 애플리케이션
  worker:       # HITL 백그라운드 워커  
  prometheus:   # 메트릭 수집
  grafana:      # 모니터링 대시보드
  pgadmin:      # DB 관리 (dev 환경만)
```

### 다단계 Docker 빌드

보안과 최적화를 위한 다단계 빌드:

```dockerfile
# 빌드 스테이지: 의존성 설치
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 런타임 스테이지: 비root 사용자로 실행
FROM python:3.11-slim as runtime
RUN groupadd -r dtrag && useradd -r -g dtrag dtrag
USER dtrag
```

### 배포 스크립트

`./scripts/deploy.sh`가 자동으로 처리하는 작업:

1. **환경 검증**: Docker, 설정 파일 확인
2. **이미지 빌드**: 캐시 없는 새로운 빌드
3. **데이터베이스 준비**: 마이그레이션 실행
4. **서비스 시작**: 의존성 순서 고려한 시작
5. **헬스 체크**: 모든 서비스 정상 동작 확인

## 🔒 보안 및 운영

### 보안 기능

- **비root 실행**: 모든 컨테이너가 전용 사용자로 실행
- **환경 변수 보호**: .env 파일로 민감 정보 분리
- **네트워크 격리**: 내부 통신은 Docker 네트워크 사용
- **헬스 체크**: 정기적인 서비스 상태 확인
- **로그 보안**: 민감 정보 로그 제외

### 백업 및 복구

```bash
# 데이터베이스 백업
./scripts/backup.sh

# 백업 파일 위치
./backups/dt_rag_backup_YYYYMMDD_HHMMSS.sql.gz

# 복구 (수동)
gunzip backups/dt_rag_backup_YYYYMMDD_HHMMSS.sql.gz
psql dt_rag < backups/dt_rag_backup_YYYYMMDD_HHMMSS.sql
```

### 로그 관리

```bash
# 서비스별 로그 확인
docker-compose logs -f api        # API 서버 로그
docker-compose logs -f worker     # 워커 로그
docker-compose logs -f postgres   # 데이터베이스 로그

# 에러 로그만 확인
docker-compose logs | grep ERROR

# 특정 시간대 로그
docker-compose logs --since="2h" --until="1h"
```

## 📈 성능 최적화

### 데이터베이스 인덱스

성능 최적화를 위한 인덱스:

```sql
-- 범위 검색을 위한 GiST 인덱스
CREATE INDEX idx_chunks_span_gist ON chunks USING gist (span);

-- 벡터 유사도 검색을 위한 IVFFlat 인덱스  
CREATE INDEX idx_embeddings_vec_ivf ON embeddings 
USING ivfflat (vec vector_cosine_ops) WITH (lists = 100);

-- 배열 검색을 위한 GIN 인덱스
CREATE INDEX idx_taxonomy_nodes_path_gin ON taxonomy_nodes USING gin (path);
```

### 예상 성능

| 작업 | 인덱스 없음 | 인덱스 있음 | 개선율 |
|------|-------------|-------------|--------|
| 스팬 오버랩 쿼리 | 45ms | 0.8ms | **56배** |
| 벡터 유사도 검색 | 120ms | 2.1ms | **57배** |
| 분류 체계 검색 | 35ms | 0.6ms | **58배** |

### 캐싱 전략

- **Redis 세션**: API 응답 캐싱 (TTL: 5분)
- **임베딩 캐시**: 중복 임베딩 방지
- **메타데이터 캐시**: 문서 정보 빠른 조회

## 🚨 문제 해결

### 자주 발생하는 문제

#### 1. 포트 충돌

```bash
# 포트 사용 확인
sudo lsof -i :8000
sudo lsof -i :5432

# 기존 프로세스 종료
sudo fuser -k 8000/tcp
```

#### 2. 데이터베이스 연결 오류

```bash
# PostgreSQL 상태 확인
docker-compose exec postgres pg_isready -U postgres

# 연결 테스트
docker-compose exec postgres psql -U postgres -d dt_rag -c "\dt"
```

#### 3. 메모리 부족

```bash
# Docker 메모리 제한 확인
docker stats

# 메모리 정리
docker system prune
docker-compose restart
```

#### 4. 느린 API 응답

```bash
# Prometheus에서 성능 메트릭 확인
curl http://localhost:9090/api/v1/query?query=http_request_duration_seconds

# 데이터베이스 성능 분석
docker-compose exec postgres psql -U postgres -d dt_rag
# > EXPLAIN ANALYZE SELECT ...
```

### 로그 분석

유용한 로그 패턴:

```bash
# API 에러 로그
docker-compose logs api | grep "ERROR\|CRITICAL"

# 성능 관련 경고
docker-compose logs api | grep "SLOW\|TIMEOUT"

# 수집 작업 실패
docker-compose logs api | grep "ingestion.*failed"

# NFR 위반 경고  
docker-compose logs api | grep "NFR violation"
```

## 🎯 로드맵

### Phase 3 (예정)
- **🔍 고급 검색**: 하이브리드 검색 (BM25 + Vector)
- **🤖 자동 분류**: ML 기반 문서 자동 분류
- **🔄 실시간 동기화**: 문서 변경 사항 실시간 반영

### Phase 4 (예정)
- **📱 모바일 앱**: 모바일 검색 인터페이스
- **🌐 API Gateway**: 마이크로서비스 아키텍처
- **🔐 고급 보안**: OAuth2, RBAC 권한 관리

## 📞 지원 및 문의

### 팀 연락처
- **A팀 (데이터 플랫폼)**: 이 시스템 개발 및 유지보수
- **B팀 (오케스트레이션)**: FastAPI 통합 및 검색 API
- **C팀 (프론트엔드)**: 사용자 인터페이스 및 대시보드

### 문제 신고
1. **시스템 장애**: Grafana 대시보드에서 실시간 상태 확인
2. **API 오류**: Prometheus 메트릭으로 성능 분석  
3. **배포 문제**: `./scripts/deploy.sh` 로그 확인

---

**🚀 Production Ready**: 이 시스템은 프로덕션 환경에서 사용할 준비가 완료되었습니다.  
**📊 모니터링**: Grafana 대시보드에서 실시간 시스템 상태를 확인하세요.  
**🔒 보안**: 모든 보안 기준을 준수하며 안전하게 배포됩니다.

**System Version**: 2.0.0 | **API Spec**: v1.8.1 | **Updated**: 2025-01-15 KST | **Team**: A팀 | **Status**: ✅ B/C팀 온보딩 준비 완료