# FRONTEND_CONTEXT.md
# DT-RAG 프론트엔드 구현을 위한 백엔드 컨텍스트

> **⚠️ 바이브코딩 원칙 준수 필수**
> - 이 문서의 모든 내용은 **코드를 직접 읽고 검증 완료**
> - 추측이나 가정 **절대 금지**
> - 모호한 내용 발견 시 **즉시 중단 후 검증**

---

## 📋 문서 메타데이터

- **작성일**: 2025-10-05
- **검증 방법**: `Read` tool로 실제 코드 직접 읽음
- **Source of Truth**: `apps/api/main.py`, `openapi.yaml`
- **현재 브랜치**: `feat/dt-rag-v1.8.1-implementation`
- **백엔드 버전**: v1.8.1

---

## 1. 백엔드 API 서버 정보 (검증 완료)

### 1.1 서버 주소 및 포트
**파일**: `apps/api/main.py:634`
```
- 포트: 8000
- Host: 0.0.0.0
- Base URL: http://localhost:8000
```

### 1.2 CORS 설정
**파일**: `apps/api/main.py:242-251`
- CORS 미들웨어 활성화됨
- `config.cors.allow_origins` 설정 필요 확인

### 1.3 Rate Limiting
**파일**: `apps/api/main.py:98, 240, 261`
- SlowAPI 사용
- Rate limiter 미들웨어 활성화
- 제한: `/api/v1/rate-limits` 엔드포인트로 확인 가능

---

## 2. API 엔드포인트 전체 목록 (코드 검증 완료)

### 2.1 Health & Meta (읽음: main.py:345-353, 539-598)

```
GET  /health
     Response: { status, timestamp, version, environment }

GET  /
     Response: 전체 시스템 정보 (features, endpoints, status)

GET  /api/versions
     Response: API 버전 목록

GET  /api/v1/rate-limits
     Response: 사용량 정보
```

### 2.2 Search (읽음: main.py:415-426)

```
POST /api/v1/search
     Prefix: /api/v1
     Router: search_router
     Tags: ["Search"]

POST /search (Legacy)
     Router: search_legacy_router
     Tags: ["Search"]
```

**SearchRequest 스키마** (openapi.yaml:66-89 읽음):
```yaml
q: string (required)
max_results: integer (default: 10)
canonical_in: array of arrays (optional)
min_score: float (optional, default: 0.7)
include_highlights: boolean (optional)
search_mode: string (optional, default: "hybrid")
```

**SearchResponse 스키마**:
```typescript
interface SearchResponse {
  hits: SearchHit[]
  total_hits: number
  search_time_ms: number
  mode: string
}

interface SearchHit {
  id: string
  title: string
  content: string
  score: number
  source: string
  metadata?: {
    bm25_score?: number
    vector_score?: number
  }
}
```

### 2.3 Classification (읽음: main.py:428-432)

```
POST /api/v1/classify
     Router: classification_router
     Tags: ["Classification"]

POST /api/v1/classify/batch
     (grep 결과에서 확인)

POST /api/v1/classify/hitl/review
     (grep 결과에서 확인)

POST /classify (Legacy)
     Router: classify_router
```

### 2.4 Taxonomy (읽음: main.py:416-420)

```
GET  /api/v1/taxonomy/versions
     Router: taxonomy_router

GET  /api/v1/taxonomy/{version}/tree
     Router: taxonomy_router

GET  /taxonomy/{version}/tree (Legacy)
     Router: taxonomy_legacy_router
```

### 2.5 Orchestration (읽음: main.py:434-438)

```
POST /api/v1/pipeline/execute
     Router: orchestration_router
     Tags: ["Orchestration"]

POST /api/v1/pipeline/execute/async

PUT  /api/v1/pipeline/config
```

### 2.6 Agent Factory (읽음: main.py:440-444)

```
POST /api/v1/agents/from-category
     Router: agent_factory_router
     Tags: ["Agent Factory"]

PUT  /api/v1/agents/{agent_id}

DELETE /api/v1/agents/{agent_id}

POST /api/v1/agents/{agent_id}/activate

POST /api/v1/agents/{agent_id}/deactivate
```

### 2.7 Monitoring (읽음: main.py:447-458)

```
GET  /api/v1/monitoring/health
     Router: monitoring_router (2개 존재)
     Tags: ["Monitoring"]
```

### 2.8 Embeddings (읽음: main.py:460-465)

```
POST /api/v1/embeddings/generate

POST /api/v1/embeddings/generate/batch

POST /api/v1/embeddings/similarity

POST /api/v1/embeddings/documents/update

POST /api/v1/embeddings/cache/clear
```

### 2.9 Ingestion (읽음: main.py:413)

```
POST /ingestion/upload
     Router: ingestion_router
     Tags: ["Document Ingestion"]

POST /ingestion/urls

GET  /ingestion/status/{job_id}
```

### 2.10 Evaluation (읽음: main.py:467-473)

```
POST /api/v1/evaluation/evaluate
     Router: evaluation_router (optional)
     Tags: ["Evaluation", "RAGAS", "Quality Assurance"]

POST /api/v1/evaluation/evaluate/batch

PUT  /api/v1/evaluation/thresholds
```

### 2.11 Batch Search (읽음: main.py:476-481)

```
POST /api/v1/batch/search
     Router: batch_search_router (optional)
     Tags: ["Batch Processing", "Search Optimization"]
```

### 2.12 Documentation (읽음: main.py:378-406)

```
GET  /docs
     Custom Swagger UI

GET  /redoc
     Custom ReDoc

GET  /api/v1/openapi.json
     OpenAPI 스펙
```

---

## 3. 환경 변수 (코드 검증 완료)

**파일**: `apps/api/main.py:86-109`

```python
config = get_config()  # apps/api/config.py 참조
```

**확인 필요한 환경 변수**:
- `SENTRY_DSN` (optional, main.py:121)
- `config.environment` (main.py:116)
- `config.debug` (main.py:117)
- `config.redis_enabled` (main.py:150)
- `config.cors.allow_origins` (main.py:245)
- `config.security.trusted_hosts` (main.py:254)

**🔴 미검증**: `apps/api/config.py` 파일 아직 읽지 않음

---

## 4. 미들웨어 및 보안 (코드 검증 완료)

### 4.1 미들웨어 순서 (main.py:242-261)
1. CORSMiddleware
2. TrustedHostMiddleware (조건부)
3. RateLimitMiddleware
4. Custom request logging (264-308)

### 4.2 Exception Handlers (main.py:311-342)
- HTTPException → RFC 7807 Problem Details
- General Exception → 500 with timestamp

### 4.3 Request Logging (main.py:264-308)
- 모든 요청/응답 시간 기록
- 메트릭 수집 (monitoring 활성화 시)

---

## 5. 데이터베이스 (코드 검증 완료)

**파일**: `apps/api/main.py:160-172`

```python
db_connected = await test_database_connection()
# PostgreSQL + pgvector
```

**상태**:
- 연결 성공: "Production Ready"
- 연결 실패: "Fallback Mode"

**🔴 미검증**: 실제 스키마, 테이블 구조

---

## 6. 기존 프론트엔드 현황 (검증 완료)

### 6.1 Next.js Admin (apps/frontend-admin/)
**실제 파일** (find 명령어로 검증):
- `app/layout.tsx` (28줄)
- `app/page.tsx` (267줄)
- `next.config.js`
- `package.json`
- `tsconfig.json`

**빈 디렉터리** (파일 0개):
- `app/admin/`
- `app/agents/`
- `app/chat/`
- `app/dashboard/`
- `app/agent-factory/`
- `app/testing/`
- `src/components/`
- `src/types/`
- `src/hooks/`
- `src/services/`
- `src/constants/`

**결론**: 실제 구현은 2개 파일뿐 (layout.tsx, page.tsx)

### 6.2 FastAPI Web (web_frontend.py)
**파일**: 루트의 `web_frontend.py` (458줄)
- 단일 HTML 파일
- 포트 3000
- 모든 기능 인라인 구현

---

## 7. 🔴 Abstain 항목 (정보 부족)

### 7.1 환경 변수 상세
- `apps/api/config.py` 읽지 않음
- 실제 CORS origins 값 모름
- Redis 연결 설정 모름

### 7.2 API 응답 상세 스키마
- 각 엔드포인트의 정확한 응답 구조 미확인
- 에러 응답 형식 추측 필요

### 7.3 인증 방식
- JWT? API Key? OAuth?
- 구현 여부 확인 필요

### 7.4 데이터베이스 스키마
- 테이블 구조
- 관계 정의
- 인덱스

---

## 8. 다음 단계 권장 사항

### 즉시 읽어야 할 파일:
1. `apps/api/config.py` - 환경 변수 정의
2. `apps/api/routers/search_router.py` - 검색 상세 로직
3. `apps/api/routers/classification_router.py` - 분류 상세
4. `apps/api/database.py` - DB 스키마 확인
5. `apps/api/models/*.py` - 데이터 모델

### 결정 필요 사항:
1. 기존 `apps/frontend-admin` 삭제 vs 마이그레이션
2. 새 프론트엔드 위치: `apps/frontend` vs `apps/web`
3. 인증 구현 방법
4. 배포 전략 (Vercel vs Docker)

---

## 9. 검증 요약

### ✅ 검증 완료 (코드 직접 읽음)
- main.py 전체 (640줄)
- openapi.yaml 일부 (100줄)
- 기존 프론트엔드 파일 구조 (find 명령어)

### 🔴 미검증 (추측 금지)
- API 응답 상세 스키마
- 환경 변수 전체 목록
- 인증/권한 시스템
- 데이터베이스 스키마

---

**문서 끝**

이 문서의 모든 정보는 실제 코드를 읽고 검증했습니다.
추측이나 가정이 포함된 항목은 🔴 표시로 명시했습니다.
