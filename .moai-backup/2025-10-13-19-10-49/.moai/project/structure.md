---
id: STRUCTURE-001
version: 2.0.0
status: active
created: 2025-10-01
updated: 2025-10-13
authors: ["@architect", "@sonheungmin"]
---

# . Structure Design

## HISTORY

### v2.0.0 (2025-10-13)
- **LEGACY_ANALYSIS**: 기존 프로젝트 구조 분석 완료 (apps/ 디렉토리, main.py, docker-compose.yml)
- **AUTHOR**: @architect
- **UPDATES**: 전체 아키텍처, 12개 모듈 책임 구분, 외부 시스템 통합, 추적성 전략 작성
- **PROJECT_TYPE**: Fullstack Monorepo (Backend: FastAPI, Frontend: Next.js 14)
- **CONTEXT**: DT-RAG v2.0.0 - Production-Ready Monorepo Structure

### v0.1.0 (2025-10-01)
- **INITIAL**: 프로젝트 구조 설계 문서 템플릿 생성
- **AUTHOR**: @architect

---

## @DOC:ARCHITECTURE-001 시스템 아키텍처

### 아키텍처 전략

**DT-RAG는 Fullstack Monorepo 구조로 설계되었으며, Backend (FastAPI + PostgreSQL + pgvector)와 Frontend (Next.js 14) 모두를 단일 저장소에서 관리합니다. 이는 "모듈 간 강한 타입 안정성"과 "빠른 Feature 개발"을 가능하게 합니다.**

```
DT-RAG Fullstack Monorepo Architecture
├── Backend (FastAPI 0.104+, Python 3.9+)
│   ├── RESTful API Layer (main.py, routers/)
│   ├── Business Logic Layer (agent_system/, orchestration/, classification/)
│   ├── Data Access Layer (database.py, DAO pattern)
│   ├── Infrastructure Layer (PostgreSQL + pgvector + Redis)
│   └── Background Worker Layer (agent_task_worker.py, Redis Queue)
│
├── Frontend (Next.js 14, React 18, TypeScript 5)
│   ├── User Frontend (apps/frontend)
│   │   ├── Pages (App Router)
│   │   ├── Components (shadcn/ui, Radix UI)
│   │   └── API Client (TanStack Query, Axios)
│   └── Admin Frontend (apps/frontend-admin)
│       ├── Admin Dashboard
│       ├── Agent Management UI
│       └── Monitoring UI
│
├── Database Layer (PostgreSQL 12+)
│   ├── pgvector (Vector Search)
│   ├── Full-text Search (BM25)
│   └── Alembic Migrations
│
└── External Services
    ├── OpenAI API (GPT-4, Embeddings)
    ├── Gemini API (Backup LLM)
    ├── Sentry (Error Tracking)
    └── LangFuse (LLM Observability)
```

**선택 이유**:
1. **Monorepo**: Backend와 Frontend 간 타입 공유 및 버전 동기화 용이
2. **FastAPI**: 비동기 I/O + Pydantic 자동 검증 + OpenAPI 문서화 자동 생성
3. **PostgreSQL + pgvector**: 관계형 DB + 벡터 검색 통합 (별도 Vector DB 불필요)
4. **Next.js 14**: App Router (서버 컴포넌트) + TanStack Query (서버 상태 관리)
5. **Redis**: Background Task Queue + API Rate Limiting + Caching

**트레이드오프**:
- ✅ 장점: 타입 안정성, 빠른 개발 속도, 통합 배포
- ⚠️ 단점: 모노레포 크기 증가 (현재 2,797 LOC), 빌드 시간 증가 가능성 (현재 < 5분)

---

## @DOC:MODULES-001 모듈별 책임 구분

### 1. API Layer (`apps/api/`)

**책임**: RESTful API 엔드포인트 제공 및 요청/응답 처리

**입력**: HTTP 요청 (JSON 페이로드)
**처리**: Pydantic 검증 → DAO 호출 → 비즈니스 로직 실행
**출력**: HTTP 응답 (JSON + 상태 코드)

| 컴포넌트 | 역할 | 주요 기능 |
|----------|------|-----------|
| `main.py` | FastAPI 애플리케이션 진입점 | 라우터 등록, 미들웨어 설정, 라이프사이클 관리 |
| `routers/` | API 엔드포인트 라우터 | taxonomy, search, classification, orchestration, agent_factory, monitoring |
| `schemas/` | Pydantic 요청/응답 모델 | 자동 검증 + OpenAPI 문서 생성 |
| `database.py` | DAO (Data Access Object) | 비동기 DB 쿼리 (AgentDAO, SearchDAO, TaxonomyDAO) |
| `security/` | 인증/인가 | API Key 검증, JWT 토큰, OAuth 2.0 |
| `middleware/` | 미들웨어 | CORS, Rate Limiting, Request Logging |
| `background/` | 백그라운드 작업 | AgentTaskWorker (Redis Queue) |

**주요 엔드포인트**:
```
POST /api/v1/agents/from-taxonomy       # Agent 생성
GET  /api/v1/agents/{id}/coverage       # Coverage 계산
POST /api/v1/agents/{id}/query          # Agent 쿼리
POST /api/v1/search                     # 하이브리드 검색
POST /api/v1/classify                   # 문서 분류
POST /api/v1/pipeline/execute           # LangGraph 파이프라인 실행
GET  /api/v1/monitoring/health          # 헬스 체크
```

---

### 2. Agent System (`apps/agent_system/`)

**책임**: Agent Growth Platform 핵심 로직 (SPEC-AGENT-GROWTH-001~004)

**입력**: Agent 생성 요청 (taxonomy_node_ids, retrieval_config)
**처리**: Coverage 계산, Gap Detection, XP/Leveling (Phase 2)
**출력**: Agent 인스턴스, Coverage 결과, Gap 목록

| 컴포넌트 | 역할 | 주요 기능 |
|----------|------|-----------|
| `coverage/meter.py` | CoverageMeterService | Coverage 계산, Gap Detection |
| `src/agent_dao.py` | AgentDAO | CRUD (Create, Read, Update, Delete, List) |
| `src/leveling.py` | LevelingService (Phase 2) | XP 계산, Level Up, Feature Unlocking |

**Coverage 계산 알고리즘**:
```python
# CoverageMeterService.calculate_coverage()
1. NetworkX graph traversal로 descendant nodes 추출
2. doc_taxonomy 테이블에서 confidence >= 0.7인 문서 수 계산 (GROUP BY node_id)
3. 각 노드별 coverage = (document_count / target_count) * 100
4. overall_coverage = SUM(document_counts) / SUM(target_counts) * 100
5. CoverageResult 반환 (agent_id, overall_coverage, node_coverage, document_counts)
```

---

### 3. Classification (`apps/classification/`)

**책임**: ML 기반 문서 자동 분류 시스템

**입력**: 문서 텍스트 (Plain Text, 향후 PDF/이미지 지원)
**처리**: Semantic Similarity 계산 → Confidence Threshold 필터링 → HITL 판단
**출력**: 분류 결과 (node_id, confidence, reasoning)

| 컴포넌트 | 역할 | 주요 기능 |
|----------|------|-----------|
| `classifier.py` | DocumentClassifier | Sentence-Transformers 기반 분류 |
| `semantic_matcher.py` | SemanticMatcher | Taxonomy Node와 문서 간 유사도 계산 (Cosine Similarity) |
| `hitl_handler.py` | HITLHandler | Confidence < 0.7 시 전문가 검토 대기열 추가 |

**분류 프로세스**:
```
1. 문서 텍스트 → Sentence-Transformers 임베딩 (768-dim)
2. Taxonomy Node 임베딩과 Cosine Similarity 계산
3. Top-K (default: 5) 후보 노드 추출
4. Confidence Threshold (default: 0.7) 필터링
5. IF confidence < 0.7 → HITL 대기열 (doc_taxonomy 테이블에 hitl_required=true 저장)
6. ELSE → 자동 분류 완료
```

---

### 4. Core (`apps/core/`)

**책임**: 공통 인프라 및 유틸리티

**입력**: 다양한 설정 값 (DATABASE_URL, OPENAI_API_KEY 등)
**처리**: 환경 변수 로드, DB 세션 관리, 로거 설정
**출력**: 공통 컴포넌트 (DB 세션, 설정 객체)

| 컴포넌트 | 역할 | 주요 기능 |
|----------|------|-----------|
| `db_session.py` | AsyncSession 관리 | SQLAlchemy AsyncEngine + Session Factory |
| `config.py` | 환경 설정 | Pydantic Settings (환경 변수 자동 로드) |
| `logger.py` | 로거 설정 | Structured Logging (JSON 형식) |

---

### 5. Evaluation (`apps/evaluation/`)

**책임**: RAG 품질 평가 (RAGAS 프레임워크 통합)

**입력**: Query, Retrieved Documents, Generated Answer
**처리**: RAGAS 메트릭 계산 (Faithfulness, Answer Relevancy, Context Precision)
**출력**: 평가 결과 (Faithfulness Score, Latency, Token Usage)

| 컴포넌트 | 역할 | 주요 기능 |
|----------|------|-----------|
| `ragas_evaluator.py` | RAGASEvaluator | RAGAS 메트릭 계산 (Faithfulness, Answer Relevancy) |
| `benchmark.py` | Benchmark Runner | 성능 벤치마크 (100개 쿼리 샘플링) |

**RAGAS 메트릭**:
- **Faithfulness**: 답변이 검색 결과에 근거하는지 (목표 ≥ 0.85)
- **Answer Relevancy**: 답변이 질문과 관련 있는지
- **Context Precision**: 검색 결과가 질문과 관련 있는지

---

### 6. Ingestion (`apps/ingestion/`)

**책임**: 문서 업로드 및 파싱 파이프라인

**입력**: 파일 업로드 (Multipart Form Data) 또는 URL 리스트
**처리**: 파일 파싱 → 청킹 → 임베딩 생성 → DB 저장
**출력**: Job ID + Processing Status

| 컴포넌트 | 역할 | 주요 기능 |
|----------|------|-----------|
| `parsers/` | 파일 파서 | Plain Text, JSON, CSV 파싱 (향후 PDF, DOCX 지원) |
| `chunking/` | 문서 청킹 | Semantic Chunking (512 토큰 단위) |
| `batch/` | 배치 처리 | 대량 문서 업로드 시 Background Task 처리 |
| `pii/` | PII 감지 | 개인정보 마스킹 (GDPR/CCPA 준수) |

**Ingestion Pipeline**:
```
1. POST /api/v1/ingestion/upload (파일 업로드)
2. 파일 파싱 (parsers/) → 청킹 (chunking/)
3. 임베딩 생성 (Sentence-Transformers)
4. documents 테이블 INSERT (PostgreSQL)
5. 자동 분류 (classification/) → doc_taxonomy INSERT
6. Job Status: pending → running → completed
```

---

### 7. Knowledge Builder (`apps/knowledge_builder/`)

**책임**: 지식 베이스 관리 및 Coverage 분석

**입력**: Agent ID, Taxonomy Node IDs
**처리**: Coverage 계산, Gap Detection, 문서 추천
**출력**: CoverageResult, Gap 목록, 추천 문서

| 컴포넌트 | 역할 | 주요 기능 |
|----------|------|-----------|
| `coverage/meter.py` | CoverageMeterService | Coverage 계산 (Phase 0) |
| `gap_detector.py` | GapDetector | Coverage 50% 미만 노드 감지 |
| `recommender.py` | DocumentRecommender | Gap 메우기 위한 문서 추천 (Phase 2) |

---

### 8. Monitoring (`apps/api/monitoring/`)

**책임**: 실시간 시스템 모니터링 및 Observability

**입력**: API 요청, 시스템 메트릭
**처리**: Prometheus 메트릭 수집, Sentry 에러 리포팅
**출력**: 메트릭 대시보드, 알림

| 컴포넌트 | 역할 | 주요 기능 |
|----------|------|-----------|
| `metrics.py` | MetricsCollector | Prometheus 메트릭 수집 (Latency, Throughput, Error Rate) |
| `health_check.py` | HealthChecker | DB/Redis/OpenAI API 상태 확인 |
| `sentry_reporter.py` | SentryReporter | 에러 추적 및 리포팅 |

**모니터링 메트릭**:
- **Request Metrics**: `http_requests_total`, `http_request_duration_seconds`
- **Database Metrics**: `db_connections_active`, `db_query_duration_seconds`
- **LLM Metrics**: `llm_api_calls_total`, `llm_tokens_used_total`

---

### 9. Orchestration (`apps/orchestration/`)

**책심**: LangGraph 7-Step RAG Pipeline 실행

**입력**: Query, Mode (search/answer/classify)
**처리**: 7-Step 파이프라인 실행 (Intent → Retrieve → Plan → Tools/Debate → Compose → Cite → Respond)
**출력**: Final Answer + Citations

| 컴포넌트 | 역할 | 주요 기능 |
|----------|------|-----------|
| `langgraph_pipeline.py` | PipelineOrchestrator | 7-Step 파이프라인 실행 |
| `src/bandit/` | Soft Q-learning Bandit | Adaptive Retrieval 전략 선택 (Phase 3.1) |
| `src/debate/` | Multi-Agent Debate | 2-agent debate 구조 (Phase 3.2) |
| `src/tools/` | MCP Tools | Tool Execution (calculator, websearch) (Phase 2B) |
| `src/casebank_dao.py` | CaseBankDAO | CaseBank CRUD (Memento Framework) |

**7-Step Pipeline**:
```
1. step1_intent: 의도 분류 (query → search/answer/classify)
2. step2_retrieve: 문서 검색 (BM25 + Vector)
   └─ IF FEATURE_SOFT_Q_BANDIT=true: RL Policy로 전략 선택 (bm25/vector/hybrid)
3. step3_plan: 메타 계획 생성 (IF FEATURE_META_PLANNER=true)
4. step4_tools_debate: 도구 실행 / Debate
   ├─ IF FEATURE_MCP_TOOLS=true: Tool Execution
   └─ IF FEATURE_DEBATE_MODE=true: Multi-Agent Debate (Affirmative vs Critical)
5. step5_compose: 답변 생성
6. step6_cite: 인용 추가
7. step7_respond: 최종 응답
```

---

### 10. Search (`apps/search/`)

**책임**: 하이브리드 검색 엔진 (BM25 + Vector)

**입력**: Query, Filters (taxonomy_node_ids, version), Top-K
**처리**: BM25 검색 + Vector 검색 → Score 정규화 → 재랭킹
**출력**: 검색 결과 (doc_id, chunk_id, content, score)

| 컴포넌트 | 역할 | 주요 기능 |
|----------|------|-----------|
| `hybrid_search.py` | HybridSearchEngine | BM25 + Vector 검색 결합 |
| `bm25.py` | BM25Searcher | PostgreSQL Full-text Search (to_tsvector) |
| `vector.py` | VectorSearcher | pgvector Cosine Similarity (IVFFlat 인덱스) |
| `reranker.py` | CrossEncoderReranker | 검색 결과 재랭킹 (Cross-Encoder 모델) |

**하이브리드 검색 알고리즘**:
```python
# SearchDAO.hybrid_search()
1. BM25 Search: PostgreSQL to_tsvector 쿼리 → BM25 Score 계산
2. Vector Search: pgvector Cosine Similarity (<=> 연산자) → Vector Score 계산
3. Score 정규화: Min-Max Normalization (0~1 범위)
4. 가중 평균: Final Score = 0.3 * BM25 + 0.7 * Vector
5. Top-K 추출 (default: 5)
6. 재랭킹 (Optional): Cross-Encoder로 재랭킹
```

---

### 11. Security (`apps/api/security/`)

**책임**: 인증/인가 및 보안 정책

**입력**: API 요청 (Header: `X-API-Key` 또는 `Authorization: Bearer`)
**처리**: API Key 검증, JWT 토큰 검증, OAuth 2.0
**출력**: 인증 성공 또는 401 Unauthorized

| 컴포넌트 | 역할 | 주요 기능 |
|----------|------|-----------|
| `api_key_auth.py` | API Key 검증 | `Depends(get_api_key)` 의존성 |
| `jwt_auth.py` | JWT 토큰 검증 | Bearer Token 검증 |
| `oauth_provider.py` | OAuth 2.0 Provider | Google, GitHub OAuth 통합 |

---

### 12. UI (`apps/ui/` - 레거시, `apps/frontend/` 사용 권장)

**책임**: (레거시) 간단한 웹 UI (현재는 `apps/frontend/` 사용 권장)

---

### 13. Frontend (`apps/frontend/`)

**책임**: 사용자 UI (Next.js 14 + TanStack Query)

**입력**: 사용자 인터랙션 (버튼 클릭, 폼 제출)
**처리**: API 호출 (TanStack Query) → 상태 관리 → 렌더링
**출력**: HTML UI (shadcn/ui 컴포넌트)

| 컴포넌트 | 역할 | 주요 기능 |
|----------|------|-----------|
| `app/` | Next.js App Router | Pages, Layouts |
| `components/` | React 컴포넌트 | shadcn/ui, Radix UI |
| `lib/` | 유틸리티 | API 클라이언트 (Axios), TanStack Query 설정 |

**기술 스택**:
- **Framework**: Next.js 14 (App Router)
- **UI Library**: shadcn/ui (Radix UI primitives)
- **State Management**: TanStack Query (서버 상태), useState (로컬 상태)
- **Styling**: Tailwind CSS 3.4
- **Validation**: Zod 4.1

---

### 14. Frontend Admin (`apps/frontend-admin/`)

**책임**: 관리자 대시보드 UI

**입력**: 관리자 인터랙션
**처리**: Agent 관리, Coverage 시각화, Monitoring Dashboard
**출력**: 관리자 UI

| 컴포넌트 | 역할 | 주요 기능 |
|----------|------|-----------|
| `dashboard/` | 관리자 대시보드 | 시스템 메트릭, 에러 로그 |
| `agents/` | Agent 관리 UI | Agent 생성, Coverage 시각화, Gap Detection |
| `monitoring/` | 모니터링 UI | Prometheus 메트릭, Sentry 에러 추적 |

---

## @DOC:INTEGRATION-001 외부 시스템 통합

### OpenAI API 연동

**용도**: GPT-4 (답변 생성), text-embedding-3-small (Embedding)

**인증 방식**: API Key (환경 변수 `OPENAI_API_KEY`)

**데이터 교환**:
```python
# GPT-4 호출
response = openai.ChatCompletion.create(
    model="gpt-4-turbo",
    messages=[{"role": "user", "content": query}],
    max_tokens=800,
    temperature=0.5
)

# Embedding 생성
embedding = openai.Embedding.create(
    model="text-embedding-3-small",
    input=document_text
)["data"][0]["embedding"]  # 1536-dim vector
```

**장애 시 대체**: Gemini API (Backup LLM)

**위험도**: **중간** (OpenAI API 장애 시 Gemini로 자동 Fallback)

---

### Gemini API 연동

**용도**: Backup LLM (OpenAI 장애 시 대체)

**인증 방식**: API Key (환경 변수 `GEMINI_API_KEY`)

**장애 시 대체**: 없음 (시스템 에러 반환)

**위험도**: **낮음** (Backup 목적으로만 사용)

---

### PostgreSQL + pgvector 연동

**용도**: 관계형 DB + 벡터 검색 통합

**인증 방식**: DATABASE_URL (asyncpg 커넥션 풀)

**데이터 교환**: 비동기 SQL 쿼리 (SQLAlchemy AsyncSession)

**성능 요구사항**:
- **Connection Pool**: 최소 10개, 최대 20개
- **Query Timeout**: 5초
- **벡터 검색 응답 시간**: < 100ms (IVFFlat 인덱스 사용 시)

---

### Redis 연동

**용도**: Background Task Queue + API Rate Limiting + Caching

**인증 방식**: REDIS_URL (redis://localhost:6379)

**데이터 교환**:
```python
# Background Task Enqueue
await redis.lpush("agent:queue:medium", json.dumps(task))

# Rate Limiting
key = f"rate_limit:{api_key}:{minute}"
count = await redis.incr(key)
await redis.expire(key, 60)
```

**장애 시 대체**: In-Memory Fallback (딕셔너리 기반)

**위험도**: **낮음** (Redis 장애 시 Fallback 동작)

---

### Sentry 연동

**용도**: 에러 추적 및 리포팅

**인증 방식**: SENTRY_DSN (환경 변수)

**데이터 교환**: 비동기 HTTP POST (에러 이벤트 전송)

**장애 시 대체**: 로컬 로그로 Fallback

**위험도**: **낮음** (모니터링 목적, 핵심 기능 아님)

---

### LangFuse 연동

**용도**: LLM Observability (Token Usage, Latency, Cost 추적)

**인증 방식**: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY

**데이터 교환**: 비동기 HTTP POST (LLM 호출 메타데이터 전송)

**장애 시 대체**: 로컬 로그로 Fallback

**위험도**: **낮음** (모니터링 목적)

---

## @DOC:TRACEABILITY-001 추적성 전략

### TAG 체계 적용

**TDD 완벽 정렬**: SPEC → 테스트 → 구현 → 문서
- `@SPEC:ID` (.moai/specs/) → `@TEST:ID` (tests/) → `@CODE:ID` (apps/) → `@DOC:ID` (README.md, .moai/project/)

**구현 세부사항**: @CODE:ID 내부 주석 레벨

- `@CODE:ID:API` - REST API 엔드포인트 (apps/api/routers/)
- `@CODE:ID:UI` - React 컴포넌트 (apps/frontend/components/)
- `@CODE:ID:DATA` - ORM 모델 (apps/api/models/, database.py)
- `@CODE:ID:DOMAIN` - 비즈니스 로직 (agent_system/, orchestration/, classification/)
- `@CODE:ID:INFRA` - 인프라 (database.py, db_session.py, docker-compose.yml)

### TAG 추적성 관리 (코드 스캔 방식)

- **검증 방법**: `/alfred:3-sync` 실행 시 `rg '@(SPEC|TEST|CODE|DOC):' -n`으로 코드 전체 스캔
- **추적 범위**: 프로젝트 전체 소스코드 (.moai/specs/, tests/, apps/, README.md)
- **유지 주기**: 코드 변경 시점마다 실시간 검증
- **CODE-FIRST 원칙**: TAG의 진실은 코드 자체에만 존재 (문서는 코드에서 추출)

**예시 TAG 체인**:
```
SPEC-AGENT-GROWTH-001
  └─ @TEST:AGENT-GROWTH-001:UNIT: tests/unit/test_coverage_meter.py
  └─ @CODE:AGENT-GROWTH-001:DOMAIN: apps/knowledge_builder/coverage/meter.py
  └─ @CODE:AGENT-GROWTH-001:DATA: apps/api/database.py (Agent ORM)
  └─ @DOC:AGENT-GROWTH-001: README.md (Agent Growth Platform 섹션)
```

---

## Legacy Context

### 기존 시스템 현황

**프로젝트 구조**: Fullstack Monorepo (단일 Git 저장소)

```
dt-rag/
├── apps/                          # 모든 애플리케이션 코드
│   ├── api/                       # FastAPI Backend (12개 하위 모듈)
│   ├── agent_system/              # Agent Growth Platform
│   ├── classification/            # ML 기반 문서 분류
│   ├── core/                      # 공통 인프라
│   ├── evaluation/                # RAGAS 평가
│   ├── ingestion/                 # 문서 업로드 파이프라인
│   ├── knowledge_builder/         # Coverage 관리
│   ├── monitoring/                # 시스템 모니터링
│   ├── orchestration/             # LangGraph 파이프라인
│   ├── search/                    # 하이브리드 검색
│   ├── security/                  # 인증/인가
│   ├── ui/                        # (레거시) 웹 UI
│   ├── frontend/                  # Next.js 사용자 UI
│   └── frontend-admin/            # Next.js 관리자 UI
│
├── tests/                         # 테스트 코드
│   ├── unit/                      # 단위 테스트 (pytest)
│   ├── integration/               # 통합 테스트
│   └── performance/               # 성능 테스트
│
├── alembic/                       # DB 마이그레이션 (Alembic)
│   └── versions/                  # 마이그레이션 스크립트 (000X_*.py)
│
├── .moai/                         # MoAI 메타데이터
│   ├── specs/                     # SPEC 문서
│   ├── reports/                   # 구현 리포트
│   ├── memory/                    # 개발 가이드
│   └── project/                   # 프로젝트 문서 (product.md, structure.md, tech.md)
│
├── docker-compose.yml             # 개발/프로덕션 Docker 구성
├── pyproject.toml                 # Python 패키지 설정
├── README.md                      # 프로젝트 개요
└── CLAUDE.md                      # AI 코딩 에이전트 지침
```

### 마이그레이션 고려사항

**Phase 0 → Phase 1 (현재 상태)**:
1. ✅ Mock 데이터 제거 → 실제 PostgreSQL + pgvector 사용
2. ✅ Fallback 모드 제거 → 프로덕션 환경 전용
3. ✅ 7-Step LangGraph Pipeline 구현 완료
4. ✅ Memento Framework 통합 완료 (CaseBank, ExecutionLog, Consolidation)
5. ✅ Agent Growth Platform Phase 0-1 완료 (agents 테이블, REST API 6개)

**Phase 1 → Phase 2 (향후 계획)**:
1. **Agent XP/Leveling 시스템** - 게임화 완성 (2주)
2. **Frontend UI 개발** - Agent 관리, Coverage 시각화 (3주)
3. **Background Task 최적화** - Redis Queue 성능 튜닝 (1주)

**Phase 2 → Phase 3 (장기 계획)**:
1. **Multimodal 지원** - PDF, 이미지 OCR (3주)
2. **Streaming Response** - SSE 기반 실시간 답변 (2주)
3. **HITL UI** - 전문가 검토 인터페이스 (2주)

---

## TODO:STRUCTURE-001 구조 개선 계획

### 단기 (1개월 이내)

1. **모듈 간 인터페이스 정의** - Pydantic 모델로 모듈 간 계약 명확화 (apps/api/schemas/ 확장)
2. **의존성 관리 전략** - Poetry로 전환 고려 (현재 pip + pyproject.toml)
3. **확장성 확보 방안** - DB Connection Pool 확대 (10→20→50개)

### 중기 (2~3개월)

4. **Frontend Monorepo 최적화** - Turborepo 도입 고려 (apps/frontend, apps/frontend-admin 공통 코드 공유)
5. **API Versioning** - /api/v2 도입 준비 (Breaking Changes 대응)
6. **Microservice 분리 검토** - Agent Growth Platform을 별도 서비스로 분리 고려 (트래픽 증가 시)

### 장기 (4개월 이상)

7. **Kubernetes 배포** - Docker Compose → Kubernetes Helm Chart
8. **Multi-Tenant 지원** - 조직별 Namespace 분리
9. **GraphQL API** - RESTful API 외 GraphQL 엔드포인트 추가

---

## EARS 아키텍처 요구사항 작성법

### 구조 설계에서의 EARS 활용

아키텍처와 모듈 설계 시 EARS 구문을 활용하여 명확한 요구사항을 정의하세요:

#### 시스템 아키텍처 EARS 예시

```markdown
### Ubiquitous Requirements (아키텍처 기본 요구사항)
- 시스템은 Fullstack Monorepo 구조를 채택해야 한다
- 시스템은 모듈 간 느슨한 결합을 유지해야 한다 (DAO 패턴, Dependency Injection)
- 시스템은 비동기 I/O를 지원해야 한다 (FastAPI AsyncSession, Next.js Server Components)

### Event-driven Requirements (이벤트 기반 구조)
- WHEN OpenAI API 호출이 실패하면, 시스템은 Gemini API로 자동 Fallback해야 한다
- WHEN DB Connection Pool이 고갈되면, 시스템은 503 Service Unavailable을 반환해야 한다
- WHEN Background Task가 실패하면, 시스템은 Retry Queue에 재등록해야 한다 (3회 재시도)

### State-driven Requirements (상태 기반 구조)
- WHILE 시스템이 개발 모드일 때, Hot Reload가 활성화되어야 한다
- WHILE 시스템이 프로덕션 모드일 때, DEBUG=false로 동작해야 한다
- WHILE Redis가 장애 상태일 때, In-Memory Fallback으로 동작해야 한다

### Optional Features (선택적 구조)
- WHERE Docker 환경이면, 시스템은 Docker Compose로 배포할 수 있다
- WHERE Kubernetes 환경이면, 시스템은 Helm Chart로 배포할 수 있다
- WHERE Prometheus가 설정되면, 시스템은 메트릭을 수집할 수 있다

### Constraints (구조적 제약사항)
- IF 보안 레벨이 높으면, 시스템은 모든 API 요청에 API Key 검증을 수행해야 한다
- 각 모듈의 Cyclomatic Complexity는 15를 초과하지 않아야 한다
- DB Connection Pool은 최소 10개, 최대 20개를 유지해야 한다
- API 응답 시간은 p95 기준 4초를 초과하지 않아야 한다
```

---

_이 구조는 `/alfred:2-build` 실행 시 TDD 구현의 가이드라인이 됩니다._
