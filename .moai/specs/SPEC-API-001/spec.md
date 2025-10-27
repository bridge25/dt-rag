---
id: API-001
version: 0.1.0
status: active
created: 2025-10-09
updated: 2025-10-09
author: @Alfred
priority: critical

category: infrastructure
labels:
  - api-gateway
  - fastapi
  - rest-api
  - openapi
  - authentication

scope:
  packages:
    - apps/api/main.py
    - apps/api/routers/*
  files:
    - main.py
    - search.py
    - ingestion.py
    - taxonomy.py
    - classification_router.py
    - evaluation.py
    - monitoring_router.py
    - admin/api_keys.py
    - health.py

related_specs:
  - EMBED-001
  - SEARCH-001
  - CLASS-001
---

# @SPEC:API-001: RESTful API Gateway for DT-RAG v1.8.1

## HISTORY

### v0.1.0 (2025-10-09)
- **INITIAL**: API Gateway 역공학 및 EARS 명세 작성
- **AUTHOR**: @Alfred
- **SCOPE**: 8개 주요 router 분석 및 통합 API 설계
- **CONTEXT**: dt-rag v1.8.1 프로젝트의 RESTful API Gateway 시스템

---

## 개요

DT-RAG 프로젝트의 API Gateway는 FastAPI 기반 RESTful API로, 하이브리드 검색, 문서 분류, RAGAS 평가, 모니터링, 관리 기능을 제공한다. OpenAPI 3.0.3 표준을 준수하며, 인증/인가, Rate Limiting, 에러 처리, 모니터링을 통합한다.

### 핵심 기능

1. **Hybrid Search API**: BM25 + Vector 하이브리드 검색, LLM 답변 생성
2. **Document Ingestion API**: 문서 업로드, 배치 처리, 상태 추적
3. **Taxonomy Management API**: 계층적 분류체계 관리, DAG 검증, 롤백
4. **Classification API**: 문서 분류, HITL 워크플로, 배치 처리
5. **Evaluation API**: RAGAS 메트릭, 품질 모니터링, 배치 평가
6. **Monitoring API**: 시스템 헬스, LLM 비용 추적, Langfuse 통합
7. **Admin API**: API 키 관리, 사용자 권한, 감사 로깅
8. **Health Check API**: 기본 헬스체크, 서비스 상태 확인

---

## EARS 요구사항

### Ubiquitous Requirements (기본 요구사항)

- 시스템은 RESTful API 표준을 준수해야 한다
- 시스템은 OpenAPI 3.0.3 스펙을 자동 생성해야 한다
- 시스템은 모든 API 엔드포인트에 대해 인증/인가를 수행해야 한다
- 시스템은 일관된 에러 응답 형식(RFC 7807 Problem Details)을 제공해야 한다
- 시스템은 CORS를 지원하여 크로스 도메인 요청을 허용해야 한다
- 시스템은 API 버전 관리를 지원해야 한다 (/api/v1)
- 시스템은 Swagger UI 및 ReDoc 문서를 제공해야 한다
- 시스템은 모든 요청/응답을 로깅해야 한다

### Event-driven Requirements (이벤트 기반)

**FR-API-001: Search API**
- WHEN POST /api/v1/search 요청 시, 시스템은 BM25 + Vector 하이브리드 검색을 수행해야 한다
- WHEN 검색 p95 latency가 1초를 초과하면, 시스템은 경고를 로깅해야 한다
- WHEN 캐시가 활성화되고 동일 쿼리 요청 시, 시스템은 캐시된 결과를 반환해야 한다
- WHEN POST /answer 요청 시, 시스템은 Gemini LLM을 사용하여 자연어 답변을 생성해야 한다

**FR-API-002: Ingestion API**
- WHEN POST /ingestion/upload 요청 시, 시스템은 문서를 비동기로 처리해야 한다
- WHEN 파일 크기가 50MB를 초과하면, 시스템은 400 Bad Request를 반환해야 한다
- WHEN 지원하지 않는 파일 포맷 업로드 시, 시스템은 400 Bad Request를 반환해야 한다
- WHEN GET /ingestion/status/{job_id} 요청 시, 시스템은 처리 상태를 반환해야 한다

**FR-API-003: Taxonomy API**
- WHEN GET /taxonomy/{version}/tree 요청 시, 시스템은 계층적 분류체계를 반환해야 한다
- WHEN POST /taxonomy/nodes 요청 시, 시스템은 DAG 순환 검증을 수행해야 한다
- WHEN POST /taxonomy/rollback 요청 시, 시스템은 TTR ≤ 15분 내에 롤백을 완료해야 한다
- WHEN 버전이 존재하지 않으면, 시스템은 404 Not Found를 반환해야 한다

**FR-API-004: Classification API**
- WHEN POST /classify 요청 시, 시스템은 의미론적 분류를 수행해야 한다
- WHEN 신뢰도가 0.7 미만이면, 시스템은 HITL 플래그를 설정해야 한다
- WHEN POST /classify/batch 요청 시, 시스템은 최대 100개 항목을 처리해야 한다
- WHEN GET /classify/hitl/tasks 요청 시, 시스템은 대기 중인 HITL 작업을 반환해야 한다

**FR-API-005: Evaluation API**
- WHEN POST /evaluation/evaluate 요청 시, 시스템은 RAGAS 메트릭을 계산해야 한다
- WHEN 메트릭이 임계값 미달이면, 시스템은 품질 경고를 생성해야 한다
- WHEN POST /evaluation/evaluate/batch 요청 시, 시스템은 최대 50개 평가를 처리해야 한다
- WHEN Gemini API 키가 없으면, 시스템은 503 Service Unavailable을 반환해야 한다

**FR-API-006: Monitoring API**
- WHEN GET /monitoring/health 요청 시, 시스템은 시스템 헬스 상태를 반환해야 한다
- WHEN GET /monitoring/llm-costs 요청 시, 시스템은 Langfuse에서 LLM 비용을 조회해야 한다
- WHEN Langfuse가 설정되지 않았으면, 시스템은 설정 안내 메시지를 반환해야 한다
- WHEN 시스템 리소스가 임계값을 초과하면, 시스템은 degraded 상태를 반환해야 한다

**FR-API-007: Admin API**
- WHEN POST /admin/api-keys 요청 시, 시스템은 admin 권한을 검증해야 한다
- WHEN API 키 생성 시, 시스템은 암호학적으로 안전한 키를 생성해야 한다
- WHEN DELETE /admin/api-keys/{key_id} 요청 시, 시스템은 감사 로그를 기록해야 한다
- WHEN 권한이 없는 사용자가 요청 시, 시스템은 403 Forbidden을 반환해야 한다

**FR-API-008: Health Check API**
- WHEN GET /healthz 요청 시, 시스템은 즉시 응답해야 한다 (< 100ms)
- WHEN 데이터베이스 연결 실패 시, 시스템은 unhealthy 상태를 반환해야 한다
- WHEN Redis 연결 실패 시, 시스템은 degraded 상태를 반환해야 한다

### State-driven Requirements (상태 기반)

- WHILE 시스템이 실행 중일 때, 시스템은 모든 HTTP 요청을 로깅하고 메트릭을 추적해야 한다
- WHILE Rate Limit이 활성화된 상태일 때, 시스템은 분당 요청 수를 제한해야 한다
- WHILE Sentry가 활성화된 상태일 때, 시스템은 모든 예외를 Sentry로 전송해야 한다
- WHILE 데이터베이스 연결이 끊긴 상태일 때, 시스템은 폴백 모드로 동작해야 한다
- WHILE CORS가 활성화된 상태일 때, 시스템은 허용된 Origin에서의 요청만 처리해야 한다

### Optional Features (선택적 기능)

- WHERE Sentry DSN이 설정되면, 시스템은 에러 추적을 활성화할 수 있다
- WHERE Langfuse가 설정되면, 시스템은 LLM 비용을 추적할 수 있다
- WHERE Redis가 설정되면, 시스템은 분산 캐싱을 사용할 수 있다
- WHERE 커스텀 OpenAPI 스펙 생성기가 있으면, 시스템은 향상된 문서를 생성할 수 있다

### Constraints (제약사항)

**NFR-API-001: 성능**
- Search API의 p95 latency는 1초 미만이어야 한다
- Health Check API의 응답 시간은 100ms 미만이어야 한다
- Batch Classification API는 최대 100개 항목을 처리해야 한다
- Batch Evaluation API는 최대 50개 평가를 처리해야 한다
- 문서 업로드는 최대 50MB까지 허용해야 한다

**NFR-API-002: OpenAPI 문서**
- IF OpenAPI 스펙이 요청되면, 시스템은 최신 스펙을 자동 생성해야 한다
- IF Swagger UI가 요청되면, 시스템은 인터랙티브 문서를 제공해야 한다
- 모든 엔드포인트는 OpenAPI 스키마에 정의되어야 한다
- Request/Response 모델은 Pydantic으로 검증되어야 한다

**NFR-API-003: 에러 처리**
- IF HTTP 예외가 발생하면, 시스템은 RFC 7807 형식으로 응답해야 한다
- IF 일반 예외가 발생하면, 시스템은 500 Internal Server Error를 반환해야 한다
- 에러 응답은 type, title, status, detail, instance, timestamp를 포함해야 한다
- 모든 예외는 로깅되어야 한다

**NFR-API-004: 인증/인가**
- API 키는 최소 32자 이상이어야 한다
- API 키는 bcrypt로 해시되어 저장되어야 한다
- Admin 작업은 admin scope API 키만 허용해야 한다
- API 키는 IP 제한 및 Rate Limit을 지원해야 한다

**NFR-API-005: 보안**
- CORS는 허용된 Origin만 접근 가능해야 한다
- Trusted Host Middleware는 허용된 호스트만 접근 가능해야 한다
- 모든 민감한 정보는 로그에 노출되지 않아야 한다
- API 키 생성은 감사 로그에 기록되어야 한다

---

## API 엔드포인트 목록

### 1. Search API (FR-API-001)

#### POST /search
Bridge Pack 호환 하이브리드 검색

**Request**:
```json
{
  "q": "검색 쿼리",
  "filters": {},
  "bm25_topk": 12,
  "vector_topk": 12,
  "rerank_candidates": 50,
  "final_topk": 5
}
```

**Response**:
```json
{
  "hits": [
    {
      "chunk_id": "uuid",
      "score": 0.95,
      "text": "텍스트 내용",
      "taxonomy_path": ["AI", "RAG"],
      "source": {
        "title": "문서 제목",
        "source_url": "https://...",
        "search_type": "hybrid"
      }
    }
  ],
  "latency": 0.234,
  "request_id": "uuid",
  "total_candidates": 50,
  "sources_count": 3,
  "taxonomy_version": "1.8.1"
}
```

**Error Codes**:
- 400: Invalid request (빈 쿼리, 잘못된 파라미터)
- 401: Unauthorized (API 키 없음)
- 500: Search error (검색 엔진 실패)

#### POST /answer
LLM 기반 자연어 답변 생성

**Request**:
```json
{
  "q": "질문",
  "mode": "answer",
  "final_topk": 5,
  "filters": {}
}
```

**Response**:
```json
{
  "question": "질문",
  "answer": "AI 생성 답변",
  "sources": [...],
  "source_count": 5,
  "search_time": 0.234,
  "generation_time": 1.456,
  "total_time": 1.690,
  "model": "gemini-2.5-flash-latest",
  "language": "ko",
  "mode": "answer",
  "request_id": "uuid",
  "timestamp": "2025-10-09T..."
}
```

**Error Codes**:
- 503: LLM service not available (Gemini API 키 없음)

#### POST /v2/search
최적화된 검색 (커스텀 파라미터)

**Request**:
```json
{
  "q": "쿼리",
  "filters": {},
  "bm25_k1": 1.5,
  "bm25_b": 0.75,
  "bm25_topk": 20,
  "vector_topk": 20,
  "bm25_weight": 0.5,
  "vector_weight": 0.5,
  "enable_reranking": true,
  "rerank_candidates": 50,
  "final_topk": 10,
  "use_cache": true,
  "use_optimized_engines": true,
  "max_query_time": 2.0
}
```

#### GET /admin/search-analytics
검색 시스템 분석 정보 (관리자)

#### POST /admin/cache/warm-up
검색 캐시 웜업 (관리자)

#### DELETE /admin/cache/clear
검색 캐시 클리어 (관리자)

#### POST /admin/optimize-indices
검색 인덱스 최적화 (관리자)

#### GET /admin/metrics
실시간 검색 메트릭 (관리자)

---

### 2. Ingestion API (FR-API-002)

#### POST /ingestion/upload
문서 업로드 및 비동기 처리

**Request** (multipart/form-data):
```
file: UploadFile (required)
taxonomy_path: str (optional, default: "general")
source_url: str (optional)
author: str (optional)
language: str (default: "ko")
priority: int (default: 5, range: 1-10)
```

**Headers**:
- X-Correlation-ID: 요청 추적 ID (optional)
- X-Idempotency-Key: 중복 방지 키 (optional)

**Response** (202 Accepted):
```json
{
  "job_id": "uuid",
  "correlation_id": "uuid",
  "status": "pending",
  "estimated_completion_minutes": 1,
  "message": "Document accepted for processing"
}
```

**Error Codes**:
- 400: Bad Request (파일 크기 초과, 지원하지 않는 포맷, 잘못된 taxonomy_path)
- 409: Conflict (중복 idempotency_key)
- 500: Internal Server Error

#### GET /ingestion/status/{job_id}
처리 상태 조회

**Response**:
```json
{
  "job_id": "uuid",
  "correlation_id": "uuid",
  "status": "completed",
  "progress": 100,
  "result": {...},
  "error": null,
  "created_at": "2025-10-09T...",
  "updated_at": "2025-10-09T..."
}
```

**Error Codes**:
- 404: Job not found

---

### 3. Taxonomy API (FR-API-003)

#### GET /taxonomy/{version}/tree
계층적 분류체계 조회

**Response**:
```json
[
  {
    "label": "AI",
    "version": "1.8.1",
    "node_id": "ai_root_001",
    "children": [
      {
        "label": "RAG",
        "version": "1.8.1",
        "node_id": "ai_rag_001",
        "canonical_path": ["AI", "RAG"],
        "children": [...]
      }
    ]
  }
]
```

**Error Codes**:
- 404: Taxonomy version not found

#### GET /taxonomy/versions
사용 가능한 버전 목록

#### POST /taxonomy/initialize
DAG 시스템 초기화 (관리자)

#### GET /taxonomy/validate
DAG 구조 검증 (순환 검증)

**Response**:
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [],
  "cycles": [],
  "orphaned_nodes": [],
  "validation_timestamp": "2025-10-09T...",
  "version": 1
}
```

#### POST /taxonomy/nodes
새 노드 생성

**Request**:
```json
{
  "node_name": "노드명",
  "parent_node_id": 123,
  "description": "설명",
  "metadata": {}
}
```

#### PATCH /taxonomy/nodes/{node_id}/move
노드 이동 (순환 검증)

**Request**:
```json
{
  "new_parent_id": 456,
  "reason": "이동 사유"
}
```

#### GET /taxonomy/nodes/{node_id}/ancestry
노드 조상 경로 조회

#### POST /taxonomy/rollback
버전 롤백 (TTR ≤ 15분)

**Request**:
```json
{
  "target_version": 5,
  "reason": "롤백 사유",
  "performed_by": "admin_user"
}
```

#### GET /taxonomy/history
버전 히스토리 조회

#### GET /taxonomy/status
Taxonomy 시스템 상태

---

### 4. Classification API (FR-API-004)

#### POST /classify
문서 청크 분류

**Request**:
```json
{
  "text": "분류할 텍스트",
  "max_suggestions": 3
}
```

**Response**:
```json
{
  "classifications": [
    {
      "path": ["AI", "RAG", "Dynamic"],
      "confidence": 0.85,
      "reasoning": "분류 근거"
    }
  ],
  "canonical": ["AI", "RAG", "Dynamic"],
  "confidence": 0.85,
  "hitl": false,
  "alternatives": [...],
  "processing_time_ms": 123
}
```

**Headers**:
- X-Correlation-ID: 요청 추적 ID
- X-Classification-Confidence: 최고 신뢰도
- X-Candidates-Count: 후보 수

**Error Codes**:
- 400: Empty text, text too long (>10000 chars)
- 500: Classification failed

#### POST /classify/batch
배치 분류 (최대 100개)

**Request**:
```json
{
  "items": [
    {"text": "텍스트1", "max_suggestions": 3},
    {"text": "텍스트2", "max_suggestions": 3}
  ],
  "taxonomy_version": null
}
```

**Response** (50개 이하: 즉시, 50개 초과: 202 Accepted):
```json
{
  "batch_id": "uuid",
  "results": [...],
  "summary": {
    "total_items": 2,
    "hitl_required": 0,
    "avg_confidence": 0.85,
    "categories": [...]
  },
  "processing_time_ms": 456
}
```

#### GET /classify/hitl/tasks
HITL 작업 목록 조회

**Query Parameters**:
- limit: int (default: 50, max: 100)
- priority: str (optional)

**Response**:
```json
[
  {
    "task_id": "uuid",
    "chunk_id": "uuid",
    "text": "텍스트",
    "suggested_classification": ["AI", "RAG"],
    "confidence": 0.65,
    "alternatives": [...],
    "created_at": "2025-10-09T...",
    "priority": "normal"
  }
]
```

#### POST /classify/hitl/review
HITL 리뷰 제출

**Request**:
```json
{
  "chunk_id": "uuid",
  "approved_path": ["AI", "RAG", "Dynamic"],
  "confidence_override": 0.95,
  "reviewer_notes": "수동 확인 완료"
}
```

#### GET /classify/analytics
분류 분석 정보

#### GET /classify/confidence/{chunk_id}
신뢰도 상세 분석

#### GET /classify/status
분류 시스템 상태

---

### 5. Evaluation API (FR-API-005)

#### POST /evaluation/evaluate
RAG 응답 평가 (RAGAS)

**Request**:
```json
{
  "query": "질문",
  "response": "RAG 응답",
  "retrieved_contexts": ["컨텍스트1", "컨텍스트2"],
  "ground_truth": "정답 (optional)"
}
```

**Response**:
```json
{
  "evaluation_id": "uuid",
  "query": "질문",
  "response": "RAG 응답",
  "metrics": {
    "context_precision": 0.85,
    "context_recall": 0.90,
    "faithfulness": 0.92,
    "answer_relevancy": 0.88
  },
  "overall_score": 0.8875,
  "quality_flags": [],
  "recommendations": [],
  "timestamp": "2025-10-09T..."
}
```

**Headers**:
- X-Evaluation-ID: 평가 ID
- X-Overall-Score: 전체 점수
- X-Has-Quality-Issues: 품질 이슈 여부

**Error Codes**:
- 400: Empty query/response, no contexts
- 500: Evaluation failed

#### POST /evaluation/evaluate/batch
배치 평가 (최대 50개)

**Request**:
```json
{
  "evaluations": [
    {
      "query": "질문1",
      "response": "응답1",
      "retrieved_contexts": [...]
    },
    ...
  ]
}
```

**Response**:
```json
{
  "batch_id": "uuid",
  "results": [...],
  "summary": {
    "total_evaluations": 10,
    "average_scores": {
      "context_precision": 0.85,
      "context_recall": 0.87,
      "faithfulness": 0.90,
      "answer_relevancy": 0.86,
      "overall_score": 0.87
    },
    "quality_issues_count": 2,
    "evaluations_with_issues": 2,
    "processing_time_per_eval_ms": 234
  },
  "processing_time_ms": 2340
}
```

#### GET /evaluation/thresholds
품질 임계값 조회

**Response**:
```json
{
  "context_precision_min": 0.7,
  "context_recall_min": 0.7,
  "faithfulness_min": 0.8,
  "answer_relevancy_min": 0.75
}
```

#### PUT /evaluation/thresholds
품질 임계값 업데이트 (관리자)

#### GET /evaluation/status
평가 시스템 상태

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-09T...",
  "gemini_api": {
    "configured": true,
    "model": "gemini-2.5-flash-latest",
    "cost_per_1m_input_tokens_usd": 0.075,
    "cost_per_1m_output_tokens_usd": 0.30
  },
  "langfuse_integration": {...},
  "evaluation_features": {
    "context_precision": true,
    "context_recall": true,
    "faithfulness": true,
    "answer_relevancy": true,
    "batch_evaluation": true,
    "quality_monitoring": true
  },
  "configuration": {
    "max_batch_size": 50,
    "default_thresholds": {...}
  }
}
```

---

### 6. Monitoring API (FR-API-006)

#### GET /monitoring/health
시스템 헬스 체크

**Response**:
```json
{
  "status": "healthy",
  "timestamp": 1728456789.123,
  "system_info": {
    "cpu_percent": 23.5,
    "memory_percent": 45.2,
    "memory_available_gb": 8.34,
    "disk_percent": 62.1,
    "disk_free_gb": 123.45
  },
  "services": {
    "api": "running",
    "database": "fallback_mode",
    "cache": "memory_only"
  }
}
```

#### GET /monitoring/llm-costs
LLM 비용 추적 (Langfuse)

**Response**:
```json
{
  "status": "active",
  "timestamp": "2025-10-09T...",
  "total_queries": 1234,
  "costs": {
    "total_usd": 1.2345,
    "total_krw": 1605,
    "breakdown_krw": {
      "gemini_2.5_flash": 1200,
      "openai_embedding_3_large": 405
    }
  },
  "per_query": {
    "avg_cost_usd": 0.001,
    "avg_cost_krw": 1.3,
    "target_krw": 10.0,
    "is_within_budget": true,
    "budget_utilization_percent": 13.0
  },
  "pricing_info": {...},
  "exchange_rate": 1300,
  "langfuse_status": {...}
}
```

**Error Cases**:
- status: "unavailable" (Langfuse 미설치)
- status: "disabled" (LANGFUSE_ENABLED=false)
- status: "not_configured" (API 키 없음)

#### GET /monitoring/langfuse-status
Langfuse 통합 상태

---

### 7. Admin API (FR-API-007)

#### POST /admin/api-keys
API 키 생성 (admin 권한 필수)

**Request**:
```json
{
  "name": "Production Key",
  "description": "프로덕션 서비스용 키",
  "scope": "read",
  "permissions": [],
  "allowed_ips": ["192.168.1.0/24"],
  "rate_limit": 1000,
  "expires_days": 365,
  "owner_id": "user_123"
}
```

**Response** (201 Created):
```json
{
  "api_key": "sk_prod_abc123...",
  "key_info": {
    "key_id": "uuid",
    "name": "Production Key",
    "scope": "read",
    "rate_limit": 1000,
    "expires_at": "2026-10-09T...",
    "created_at": "2025-10-09T...",
    ...
  }
}
```

**Error Codes**:
- 400: Invalid request (잘못된 scope, IP 형식)
- 403: Forbidden (admin 권한 없음)
- 500: Creation failed

#### GET /admin/api-keys
API 키 목록 조회 (admin)

**Query Parameters**:
- owner_id: str (optional)
- active_only: bool (default: true)
- limit: int (default: 100, max: 1000)
- offset: int (default: 0)

#### GET /admin/api-keys/{key_id}
API 키 상세 조회 (admin)

#### PUT /admin/api-keys/{key_id}
API 키 업데이트 (admin)

**Request**:
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "allowed_ips": ["192.168.2.0/24"],
  "rate_limit": 2000,
  "is_active": true
}
```

#### DELETE /admin/api-keys/{key_id}
API 키 폐기 (admin)

**Request**:
```json
{
  "reason": "보안 침해 의심"
}
```

#### GET /admin/api-keys/{key_id}/usage
API 키 사용 통계 (admin)

**Query Parameters**:
- days: int (default: 7, max: 90)

**Response**:
```json
{
  "key_id": "uuid",
  "total_requests": 12345,
  "failed_requests": 23,
  "requests_last_24h": 456,
  "requests_last_7d": 3456,
  "most_used_endpoints": [
    {"endpoint": "/search", "count": 5678},
    {"endpoint": "/classify", "count": 3456}
  ],
  "last_used_at": "2025-10-09T..."
}
```

#### POST /admin/api-keys/generate
샘플 키 생성 (admin, 테스트용)

**Query Parameters**:
- key_type: str (default: "production")
- count: int (default: 1, max: 10)

#### POST /admin/api-keys/validate
API 키 형식 검증 (admin)

**Request**:
```json
{
  "api_key": "sk_prod_abc123..."
}
```

**Response**:
```json
{
  "is_valid": true,
  "errors": [],
  "entropy_bits": 256,
  "format": "base64",
  "length": 48,
  "character_composition": {...},
  "weak_patterns": false
}
```

---

### 8. Health Check API (FR-API-008)

#### GET /healthz
기본 헬스체크

**Response**:
```json
{
  "status": "healthy",
  "timestamp": 1728456789.123,
  "service": "dt-rag-api"
}
```

#### GET /health
상세 헬스체크

**Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "1728456789.123",
  "version": "1.8.1",
  "environment": "production"
}
```

**Status Values**:
- healthy: 모든 서비스 정상
- degraded: 일부 서비스 문제
- unhealthy: 주요 서비스 장애

---

### 9. Metadata Endpoints

#### GET /
API 루트 정보

**Response**:
```json
{
  "name": "Dynamic Taxonomy RAG API",
  "version": "1.8.1",
  "description": "RESTful API for dynamic taxonomy RAG system",
  "team": "A",
  "spec": "OpenAPI v1.8.1",
  "status": "Production Ready",
  "database": "PostgreSQL + pgvector",
  "documentation": {
    "swagger_ui": "/docs",
    "redoc": "/redoc",
    "openapi_spec": "/api/v1/openapi.json"
  },
  "features": {...},
  "api_endpoints": {...},
  "environment": "production",
  "timestamp": 1728456789.123
}
```

#### GET /api/versions
API 버전 목록

**Response**:
```json
{
  "versions": [
    {
      "version": "v1",
      "status": "current",
      "base_url": "/api/v1",
      "documentation": "/docs",
      "features": [...]
    }
  ],
  "current": "v1",
  "deprecated": [],
  "sunset_policy": "https://..."
}
```

#### GET /api/v1/rate-limits
Rate Limit 정보

**Response**:
```json
{
  "limits": {
    "requests_per_minute": 100,
    "requests_per_hour": 5000,
    "requests_per_day": 50000,
    "concurrent_requests": 10
  },
  "current_usage": {...},
  "reset_times": {...},
  "upgrade_info": {...}
}
```

#### GET /docs
Swagger UI 문서

#### GET /redoc
ReDoc 문서

#### GET /api/v1/openapi.json
OpenAPI 스펙 (JSON)

---

## Request/Response 모델

### 공통 Request 헤더

```
Authorization: Bearer <api_key>
Content-Type: application/json
X-Correlation-ID: <uuid>  (optional, for tracing)
X-Idempotency-Key: <key>  (optional, for duplicate prevention)
```

### 공통 Response 헤더

```
Content-Type: application/json
X-Request-ID: <uuid>
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1728456900
```

### 에러 응답 형식 (RFC 7807)

```json
{
  "type": "https://httpstatuses.com/400",
  "title": "HTTP Error",
  "status": 400,
  "detail": "Invalid request: query cannot be empty",
  "instance": "https://api.example.com/search",
  "timestamp": 1728456789.123
}
```

### Pydantic 모델 예시

```python
# Search
class SearchRequest(BaseModel):
    q: str = Field(..., min_length=1)
    filters: Optional[Dict[str, Any]] = None
    bm25_topk: int = Field(12, ge=1, le=100)
    vector_topk: int = Field(12, ge=1, le=100)
    rerank_candidates: int = Field(50, ge=1, le=1000)
    final_topk: int = Field(5, ge=1, le=50)

class SearchHit(BaseModel):
    chunk_id: str
    score: float = Field(ge=0.0)
    text: Optional[str] = None
    taxonomy_path: Optional[List[str]] = None
    source: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    hits: List[SearchHit]
    latency: float = Field(ge=0.0)
    request_id: str
    total_candidates: Optional[int] = None
    sources_count: Optional[int] = None
    taxonomy_version: str = "1.8.1"

# Classification
class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    max_suggestions: int = Field(3, ge=1, le=10)

class TaxonomyNode(BaseModel):
    path: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str

class ClassifyResponse(BaseModel):
    classifications: List[TaxonomyNode]
    canonical: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    hitl: bool
    alternatives: List[TaxonomyNode]
    processing_time_ms: float

# Evaluation
class EvaluationRequest(BaseModel):
    query: str = Field(..., min_length=1)
    response: str = Field(..., min_length=1)
    retrieved_contexts: List[str] = Field(..., min_items=1)
    ground_truth: Optional[str] = None

class EvaluationMetrics(BaseModel):
    context_precision: Optional[float] = Field(None, ge=0.0, le=1.0)
    context_recall: Optional[float] = Field(None, ge=0.0, le=1.0)
    faithfulness: Optional[float] = Field(None, ge=0.0, le=1.0)
    answer_relevancy: Optional[float] = Field(None, ge=0.0, le=1.0)

class EvaluationResult(BaseModel):
    evaluation_id: str
    query: str
    response: str
    metrics: EvaluationMetrics
    overall_score: float = Field(ge=0.0, le=1.0)
    quality_flags: List[str]
    recommendations: List[str]
    timestamp: datetime
```

---

## 에러 코드 체계

### HTTP 상태 코드

**2xx Success**
- 200 OK: 요청 성공
- 201 Created: 리소스 생성 성공
- 202 Accepted: 비동기 처리 수락
- 204 No Content: 성공, 본문 없음

**4xx Client Errors**
- 400 Bad Request: 잘못된 요청 (빈 쿼리, 파라미터 오류, 파일 크기 초과)
- 401 Unauthorized: 인증 실패 (API 키 없음, 만료)
- 403 Forbidden: 권한 없음 (admin 권한 필요)
- 404 Not Found: 리소스 없음 (job_id, key_id, version)
- 409 Conflict: 리소스 충돌 (중복 idempotency_key)
- 429 Too Many Requests: Rate Limit 초과

**5xx Server Errors**
- 500 Internal Server Error: 서버 내부 오류
- 503 Service Unavailable: 서비스 사용 불가 (Gemini API 키 없음, 데이터베이스 연결 실패)

### 도메인별 에러 메시지

**Search Errors**
- "Search error: Query cannot be empty"
- "Search error: Hybrid search engine not available"
- "Optimized search engine not available"

**Ingestion Errors**
- "File size exceeds 50MB limit"
- "Unsupported file format: {extension}"
- "Taxonomy path must have 1-10 elements"
- "Duplicate request with idempotency key: {key}"

**Classification Errors**
- "Text content cannot be empty"
- "Text content exceeds maximum length of 10000 characters"
- "Batch size exceeds maximum of 100 items"
- "Classification operation failed"

**Evaluation Errors**
- "Query cannot be empty"
- "Response cannot be empty"
- "At least one retrieved context is required"
- "Batch size exceeds maximum of 50 evaluations"
- "LLM service not available. Check GEMINI_API_KEY environment variable."

**Admin Errors**
- "Admin access required. Your API key does not have sufficient permissions."
- "Failed to create API key: {error}"
- "API key not found: {key_id}"

---

## 인증/인가

### API 키 인증

**Header**:
```
Authorization: Bearer sk_prod_abc123...
```

**검증 흐름**:
1. Header에서 API 키 추출
2. 데이터베이스에서 해시 조회
3. bcrypt 검증
4. 만료 여부 확인
5. IP 제한 확인
6. Rate Limit 확인
7. Scope 및 Permissions 확인

### Scope 체계

- **read**: 조회 작업만 허용 (GET /search, GET /taxonomy/tree)
- **write**: 쓰기 작업 허용 (POST /classify, POST /ingestion/upload)
- **admin**: 관리 작업 허용 (POST /admin/api-keys, DELETE /admin/api-keys)

### Dependencies

```python
from fastapi import Depends, HTTPException
from apps.api.deps import verify_api_key

@router.post("/admin/api-keys")
async def create_api_key(
    api_key: str = Depends(verify_api_key)
):
    if api_key.scope != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    ...
```

---

## Rate Limiting

### Redis 기반 Rate Limiter

**구현**:
- Redis를 사용한 분산 Rate Limiting
- Sliding Window 알고리즘
- 키: `rate_limit:{api_key}:{endpoint}:{minute}`

**Tier별 제한**:
- **Free**: 100 req/min, 5000 req/hour, 50000 req/day
- **Standard**: 1000 req/min, 50000 req/hour, 500000 req/day
- **Premium**: 10000 req/min, 500000 req/hour, 5000000 req/day
- **Enterprise**: Unlimited

**응답 헤더**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1728456900
Retry-After: 60  (429 응답 시)
```

**429 응답**:
```json
{
  "type": "https://httpstatuses.com/429",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Rate limit exceeded. Retry after 60 seconds.",
  "instance": "/api/v1/search",
  "timestamp": 1728456789.123,
  "rate_limit": {
    "limit": 1000,
    "remaining": 0,
    "reset": 1728456900
  }
}
```

---

## Middleware 구성

### 1. CORS Middleware

```python
CORSMiddleware(
    allow_origins=["https://example.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit"],
    max_age=3600
)
```

### 2. Trusted Host Middleware

```python
TrustedHostMiddleware(
    allowed_hosts=["api.example.com", "*.example.com"]
)
```

### 3. Rate Limit Middleware

```python
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Extract API key
    api_key = extract_api_key(request)

    # Check rate limit
    allowed = await rate_limiter.check_rate_limit(api_key, request.url.path)

    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    response = await call_next(request)
    return response
```

### 4. Request Logging Middleware

```python
@app.middleware("http")
async def log_requests_and_track_metrics(request: Request, call_next):
    start_time = time.time()

    # Log request
    logger.info(f"Request: {request.method} {request.url}")

    # Process request
    response = await call_next(request)

    # Calculate response time
    response_time_ms = (time.time() - start_time) * 1000

    # Log response
    logger.info(f"Response: {response.status_code} ({response_time_ms:.2f}ms)")

    # Track metrics
    if MONITORING_AVAILABLE:
        await track_request_metrics(request, response_time_ms, response.status_code)

    return response
```

---

## OpenAPI 스펙 생성

### 자동 생성

FastAPI는 Pydantic 모델을 기반으로 OpenAPI 스펙을 자동 생성한다.

**스키마 접근**:
- JSON: GET /api/v1/openapi.json
- Swagger UI: GET /docs
- ReDoc: GET /redoc

### 커스텀 스키마

```python
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add custom security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "API Key"
        }
    }

    # Add global security requirement
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### Swagger UI 커스터마이징

```python
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Documentation",
        swagger_ui_parameters={
            "deepLinking": True,
            "displayRequestDuration": True,
            "docExpansion": "none",
            "operationsSorter": "alpha",
            "filter": True,
            "tryItOutEnabled": True
        }
    )
```

---

## 모니터링 및 로깅

### 로깅 구조

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

**로그 레벨**:
- DEBUG: 디버그 정보
- INFO: 정상 작동 정보 (요청/응답)
- WARNING: 경고 (폴백 모드, 캐시 미스)
- ERROR: 에러 (예외, 실패)

**로깅 포인트**:
- 모든 HTTP 요청/응답
- API 키 검증
- Rate Limit 체크
- 데이터베이스 쿼리
- 예외 발생

### Sentry 통합

```python
if SENTRY_AVAILABLE:
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        init_sentry(
            dsn=sentry_dsn,
            environment=config.environment,
            release="1.8.1",
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1
        )
```

**추적 항목**:
- 모든 HTTP 예외
- 일반 예외
- 성능 프로파일링 (10% sampling)
- 트랜잭션 추적 (10% sampling)

### Langfuse 통합

**LLM 비용 추적**:
- Gemini 2.5 Flash: $0.075 per 1M input tokens, $0.30 per 1M output tokens
- OpenAI text-embedding-3-large: $0.00013 per 1K tokens

**추적 데이터**:
- 모델명
- 입력/출력 토큰 수
- 총 비용 (USD, KRW)
- 쿼리당 평균 비용
- 예산 준수 여부 (목표: ₩10/query)

---

## 배포 및 운영

### 환경 변수

```bash
# API 설정
ENVIRONMENT=production
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000

# 데이터베이스
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true

# LLM 설정
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Langfuse 설정
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com

# Sentry 설정
SENTRY_DSN=https://...@sentry.io/...

# CORS 설정
CORS_ALLOW_ORIGINS=https://example.com,http://localhost:3000
CORS_ALLOW_CREDENTIALS=true

# 보안 설정
TRUSTED_HOSTS=api.example.com,*.example.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=5000
RATE_LIMIT_PER_DAY=50000

# 환율
USD_TO_KRW=1300
```

### 의존성

```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.28.0
redis>=5.0.0
openai>=1.0.0
sentence-transformers
langfuse>=3.6.0
sentry-sdk>=1.38.0
python-multipart  # for file uploads
```

### 실행

```bash
# 개발 모드
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Docker
docker run -p 8000:8000 dt-rag-api:1.8.1
```

### Health Check 모니터링

```bash
# 기본 헬스체크
curl http://localhost:8000/healthz

# 상세 헬스체크
curl http://localhost:8000/health

# 시스템 헬스
curl -H "Authorization: Bearer <api_key>" \
  http://localhost:8000/api/v1/monitoring/health
```

### 성능 메트릭

**목표 지표**:
- Search API p95 latency: < 1s
- Health Check response time: < 100ms
- API 가용성: > 99.9%
- 에러율: < 0.1%

**모니터링 대시보드**:
- Swagger UI: /docs
- ReDoc: /redoc
- Health: /health
- Monitoring: /api/v1/monitoring/health
- LLM Costs: /api/v1/monitoring/llm-costs

---

## 보안 고려사항

### 1. API 키 보안

- API 키는 bcrypt로 해시되어 저장
- 평문 키는 생성 시 1회만 반환
- 키 생성/폐기는 감사 로그에 기록
- IP 제한 및 Rate Limit 지원
- 만료 기간 설정 가능

### 2. 입력 검증

- 모든 입력은 Pydantic으로 검증
- 파일 크기 제한 (50MB)
- 텍스트 길이 제한 (10000자)
- 배치 크기 제한 (100개)
- SQL Injection 방지 (SQLAlchemy ORM)

### 3. CORS 정책

- 허용된 Origin만 접근 가능
- Credentials 전송 제어
- 노출 헤더 제한

### 4. Rate Limiting

- Redis 기반 분산 Rate Limiting
- 티어별 차등 제한
- 429 응답 시 Retry-After 헤더 제공

### 5. 에러 처리

- 민감한 정보는 로그/응답에 노출 금지
- 일반 예외는 500 Internal Server Error로 변환
- RFC 7807 표준 에러 형식 사용

### 6. 감사 로깅

- API 키 생성/수정/폐기
- 관리자 작업
- 실패한 인증 시도
- Rate Limit 초과

---

## 향후 개선사항

### 기능 확장
- [ ] OAuth 2.0 통합
- [ ] GraphQL 엔드포인트
- [ ] WebSocket 실시간 알림
- [ ] API 사용량 대시보드

### 성능 최적화
- [ ] Redis 기반 응답 캐싱
- [ ] Connection Pooling 튜닝
- [ ] CDN 통합
- [ ] HTTP/2 지원

### 보안 강화
- [ ] API 키 로테이션 자동화
- [ ] 2FA 지원
- [ ] IP Whitelist 관리 UI
- [ ] DDoS 방어

### 모니터링 강화
- [ ] Prometheus 메트릭 노출
- [ ] Grafana 대시보드
- [ ] 알림 시스템 (Slack, PagerDuty)
- [ ] SLO/SLA 추적

---

## 참조

### 외부 문서
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAPI 3.0.3 Specification](https://spec.openapis.org/oas/v3.0.3)
- [RFC 7807 Problem Details](https://datatracker.ietf.org/doc/html/rfc7807)
- [Pydantic Documentation](https://docs.pydantic.dev/)

### 내부 문서
- `.moai/specs/SPEC-EMBED-001/spec.md` - 벡터 임베딩 서비스
- `.moai/specs/SPEC-SEARCH-001/spec.md` - 하이브리드 검색 시스템
- `.moai/specs/SPEC-CLASS-001/spec.md` - 분류 시스템

### 관련 파일
- `apps/api/main.py` - FastAPI 애플리케이션 진입점
- `apps/api/routers/search.py` - 검색 라우터
- `apps/api/routers/ingestion.py` - 문서 수집 라우터
- `apps/api/routers/taxonomy.py` - 분류체계 라우터
- `apps/api/routers/classification_router.py` - 분류 라우터
- `apps/api/routers/evaluation.py` - 평가 라우터
- `apps/api/routers/monitoring_router.py` - 모니터링 라우터
- `apps/api/routers/admin/api_keys.py` - API 키 관리 라우터
- `apps/api/routers/health.py` - 헬스체크 라우터

---

**문서 버전**: v0.1.0
**최종 업데이트**: 2025-10-09
**작성자**: @Alfred
**상태**: Active
