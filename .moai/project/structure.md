---
id: STRUCTURE-001
version: 2.0.1
status: active
created: 2025-10-01
updated: 2025-11-10
author: @architect
priority: medium
---

# dt-rag Structure Design

## HISTORY

### v2.0.1 (2025-11-10)
- **MERGE**: 백업 파일 병합 완료 (MoAI-ADK 0.22.5 업데이트 후 자동 최적화)
- **AUTHOR**: @Alfred
- **BACKUP_SOURCE**: .moai-backups/backup/ (2025-10-27)
- **REASON**: moai-adk 재초기화 후 사용자 커스터마이징 복원

### v2.0.0 (2025-10-13)
- **MAJOR**: DT-RAG 풀스택 아키텍처 완성
- **AUTHOR**: @architect, @code-builder, @Alfred
- **SECTIONS**: 12개 모듈 구조 정의 (API, Agent System, Classification, Document Ingestion, Embedding, Hybrid Search, LLM Integration, Monitoring, Agent DAG, Vector DB, PostgreSQL Integration, Tag Management)
- **INTEGRATIONS**: OpenAI, PostgreSQL, Redis, Sentry
- **TRACEABILITY**: @TAG 체계 전면 적용 (SPEC→TEST→CODE→DOC)

### v0.1.1 (2025-10-17)
- **UPDATED**: Template version synced (v0.3.8)
- **AUTHOR**: @Alfred
- **SECTIONS**: Metadata standardization (single `author` field, added `priority`)

### v0.1.0 (2025-10-01)
- **INITIAL**: Authored the structure design document
- **AUTHOR**: @architect
- **SECTIONS**: Architecture, Modules, Integration, Traceability

---

## @DOC:ARCHITECTURE-001 System Architecture

### Architectural Strategy

**DT-RAG는 Dynamic Taxonomy RAG 시스템으로, FastAPI 백엔드와 Next.js 프론트엔드의 풀스택 하이브리드 아키텍처를 채택합니다.**

```
DT-RAG Fullstack Architecture
┌─────────────────────────────────────────────────────────────────────┐
│ Frontend Layer (Next.js 14 + TypeScript)                            │
│ - Server Components & RSC                                           │
│ - shadcn/ui + Tailwind CSS                                          │
│ - React Query for state management                                  │
└─────────────────────────────────────────────────────────────────────┘
                               ↓ REST API
┌─────────────────────────────────────────────────────────────────────┐
│ API Layer (FastAPI)                                                 │
│ - /api/v1/search, /api/v1/answer, /api/v1/ingestion/*             │
│ - API Key Authentication                                            │
│ - Rate Limiting & CORS                                              │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Agent Orchestration Layer (LangGraph)                               │
│ - Multi-Agent Debate (MAD) orchestration                            │
│ - Adaptive Retrieval with confidence scoring                        │
│ - Classification pipeline (hybrid rules + LLM)                      │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Core RAG Layer                                                      │
│ - Hybrid Search (BM25 + Vector Similarity)                          │
│ - Cross-encoder Reranking                                           │
│ - Dynamic Taxonomy filtering                                        │
│ - Intelligent chunking & embedding                                  │
└─────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Data Layer                                                          │
│ - PostgreSQL + pgvector (metadata, taxonomy, chunks)                │
│ - Redis (caching, rate limiting)                                    │
│ - MinIO/S3 (document storage)                                       │
└─────────────────────────────────────────────────────────────────────┘
```

**Rationale**:
- **Separation of Concerns**: Frontend/Backend 분리로 독립적 확장 가능
- **Agent-first Design**: LangGraph 기반 멀티 에이전트 오케스트레이션
- **Hybrid Search**: BM25(키워드) + Vector(의미론적) 검색으로 정확도 극대화
- **Dynamic Taxonomy**: 계층적 분류 체계로 도메인 특화 검색 지원
- **Observable**: Langfuse 통합으로 전체 RAG 파이프라인 추적 가능

---

## @DOC:MODULES-001 Module Responsibilities

### 1. API Layer (`apps/api/`)

- **Responsibilities**: REST API 제공, 인증/인가, 요청 라우팅
- **Inputs**: HTTP 요청 (JSON), API Key 헤더
- **Processing**:
  - Router에서 요청 검증 및 파싱
  - Service Layer 호출
  - 응답 직렬화 및 반환
- **Outputs**: JSON 응답, HTTP 상태 코드

| Component                  | Role             | Key Capabilities                     |
| -------------------------- | ---------------- | ------------------------------------ |
| `main.py`                  | FastAPI 앱 진입점 | CORS, 미들웨어, 라우터 등록               |
| `routers/search_router.py` | 검색 API 엔드포인트 | /search, /answer 라우팅                |
| `routers/ingestion_router.py` | 문서 업로드 API | 파일 업로드, 메타데이터 추출                |
| `routers/agent_router.py`  | 에이전트 관리 API | 에이전트 CRUD, 구성 관리                  |
| `auth.py`                  | API Key 인증     | API Key 검증, 401 응답                  |

### 2. Agent System (`apps/api/agent_system/`)

- **Responsibilities**: LangGraph 기반 멀티 에이전트 오케스트레이션
- **Inputs**: 사용자 쿼리, 검색 모드, 하이퍼파라미터
- **Processing**:
  - Classification (쿼리 의도 분류)
  - Adaptive Retrieval (신뢰도 기반 반복 검색)
  - Multi-Agent Debate (다수결 합의)
  - Answer Generation (최종 응답 생성)
- **Outputs**: 답변 텍스트, 신뢰도 점수, 에이전트 로그

| Component             | Role                    | Key Capabilities                            |
| --------------------- | ----------------------- | ------------------------------------------- |
| `agent_orchestrator.py` | LangGraph 워크플로우 관리 | StateGraph 구성, 노드/엣지 정의               |
| `nodes/classify.py`   | 쿼리 분류 노드           | hybrid classification (rules + LLM)         |
| `nodes/retrieve.py`   | 검색 노드               | Adaptive Retrieval, 신뢰도 평가               |
| `nodes/debate.py`     | MAD 노드                | 다중 LLM 응답 생성, 다수결 합의                 |
| `nodes/answer.py`     | 답변 생성 노드           | 최종 응답 합성, 인용 추가                       |

### 3. Classification System (`apps/api/classification/`)

- **Responsibilities**: 쿼리 의도 분류 (Hybrid Rules + LLM)
- **Inputs**: 사용자 쿼리 문자열
- **Processing**:
  1. Rule-based classifier: 정규식, 키워드 매칭
  2. LLM classifier: OpenAI 기반 의도 분류
  3. Confidence scoring: 규칙 vs LLM 신뢰도 비교
  4. Human-in-the-loop: 낮은 신뢰도 시 사람 개입 요청
- **Outputs**: 분류 결과 (QA/SEARCH/CHAT), 신뢰도 점수

| Component                  | Role               | Key Capabilities                         |
| -------------------------- | ------------------ | ---------------------------------------- |
| `classification_service.py` | 분류 서비스 로직    | 규칙 + LLM 조합, 신뢰도 계산                |
| `rule_engine.py`           | 규칙 기반 분류      | 정규식 패턴 매칭, 키워드 검색                |
| `llm_classifier.py`        | LLM 기반 분류       | OpenAI prompt engineering, 구조화된 출력   |

### 4. Document Ingestion (`apps/api/ingestion/`)

- **Responsibilities**: 문서 업로드, 파싱, PII 필터링, 청킹, 임베딩
- **Inputs**: PDF/DOCX/TXT/Markdown 파일
- **Processing**:
  1. 파일 포맷 검증
  2. 텍스트 추출 (PDFPlumber, python-docx, unstructured)
  3. PII 필터링 (regex 기반 민감정보 제거)
  4. Intelligent chunking (RecursiveCharacterTextSplitter)
  5. 임베딩 생성 (OpenAI text-embedding-3-small)
  6. PostgreSQL 저장
- **Outputs**: Chunk 메타데이터, 임베딩 벡터, 문서 ID

| Component                 | Role                 | Key Capabilities                          |
| ------------------------- | -------------------- | ----------------------------------------- |
| `ingestion_service.py`    | 문서 처리 오케스트레이션 | 파일→청크→임베딩 파이프라인                 |
| `file_parser.py`          | 파일 파싱             | PDF/DOCX/TXT/Markdown 파싱                |
| `pii_filter.py`           | PII 필터링            | 주민번호, 카드번호, 이메일 마스킹             |
| `chunking_strategy.py`    | 청킹 전략             | RecursiveCharacterTextSplitter 구성       |

### 5. Embedding Service (`apps/api/embedding_service.py`)

- **Responsibilities**: 텍스트 → 벡터 변환
- **Inputs**: 텍스트 문자열 (쿼리 또는 청크)
- **Processing**: OpenAI Embeddings API 호출, 배치 처리
- **Outputs**: 1536차원 임베딩 벡터

| Component              | Role           | Key Capabilities                     |
| ---------------------- | -------------- | ------------------------------------ |
| `embedding_service.py` | 임베딩 생성    | OpenAI API 호출, 에러 핸들링, 재시도   |

### 6. Hybrid Search System (`apps/api/search/`)

- **Responsibilities**: BM25 + Vector Similarity 통합 검색
- **Inputs**: 쿼리 텍스트, 검색 모드, top-k, 필터 조건
- **Processing**:
  1. BM25 검색 (키워드 기반)
  2. Vector Similarity 검색 (코사인 유사도)
  3. Weighted fusion (α BM25 + (1-α) Vector)
  4. Cross-encoder Reranking (선택적)
  5. Taxonomy 기반 필터링
- **Outputs**: 정렬된 Chunk 리스트, 유사도 점수

| Component                 | Role                  | Key Capabilities                        |
| ------------------------- | --------------------- | --------------------------------------- |
| `hybrid_search.py`        | 통합 검색 서비스       | BM25 + Vector fusion, reranking          |
| `bm25_ranker.py`          | BM25 검색             | rank_bm25 라이브러리, TF-IDF 스코어링      |
| `vector_search.py`        | 벡터 검색             | pgvector 코사인 유사도 검색                |
| `cross_encoder_reranker.py` | Reranking           | sentence-transformers cross-encoder     |

### 7. LLM Integration (`apps/api/llm/`)

- **Responsibilities**: LLM API 호출, 프롬프트 관리, 응답 파싱
- **Inputs**: 시스템 프롬프트, 사용자 쿼리, 검색된 컨텍스트
- **Processing**:
  - OpenAI Chat Completions API 호출
  - Streaming 응답 처리 (선택적)
  - 구조화된 출력 파싱 (JSON mode)
- **Outputs**: LLM 생성 텍스트, 토큰 사용량

| Component           | Role               | Key Capabilities                       |
| ------------------- | ------------------ | -------------------------------------- |
| `llm_service.py`    | LLM 호출 서비스     | OpenAI API 통합, 에러 핸들링             |
| `prompt_templates.py` | 프롬프트 관리     | Jinja2 템플릿, 시스템 메시지 구성         |

### 8. Monitoring & Observability (`apps/api/monitoring/`)

- **Responsibilities**: Langfuse 통합, 메트릭 수집, 에러 트래킹
- **Inputs**: RAG 파이프라인 이벤트, LLM 호출 로그
- **Processing**:
  - Langfuse Trace/Span 생성
  - 커스텀 메트릭 전송
  - Sentry 에러 리포팅
- **Outputs**: Langfuse 대시보드, Sentry 이슈

| Component                | Role                | Key Capabilities                      |
| ------------------------ | ------------------- | ------------------------------------- |
| `langfuse_integration.py` | Langfuse 추적       | Trace/Span/Generation 로깅             |
| `sentry_integration.py`  | 에러 모니터링        | Sentry SDK 초기화, 에러 캡처            |

### 9. Agent DAG Management (`apps/api/agent_dag/`)

- **Responsibilities**: LangGraph StateGraph 동적 생성/관리
- **Inputs**: 에이전트 구성 JSON (노드, 엣지, 조건부 분기)
- **Processing**: StateGraph 빌더 패턴, 조건부 라우팅 로직
- **Outputs**: 컴파일된 LangGraph 앱

| Component            | Role                  | Key Capabilities                        |
| -------------------- | --------------------- | --------------------------------------- |
| `dag_builder.py`     | DAG 동적 생성          | add_node, add_edge, add_conditional_edges |
| `state_definitions.py` | State 스키마 정의    | TypedDict, 상태 전이 규칙                 |

### 10. Vector Database Layer (`apps/api/vector_db/`)

- **Responsibilities**: pgvector 연동, 벡터 인덱싱, 유사도 검색
- **Inputs**: 임베딩 벡터, 메타데이터
- **Processing**: PostgreSQL + pgvector 쿼리 실행
- **Outputs**: 유사도 검색 결과 (Chunk + 스코어)

| Component            | Role                  | Key Capabilities                        |
| -------------------- | --------------------- | --------------------------------------- |
| `vector_db.py`       | pgvector 인터페이스    | INSERT, SELECT with cosine distance     |

### 11. PostgreSQL Integration (`apps/api/db/`)

- **Responsibilities**: SQLAlchemy ORM, 마이그레이션, 트랜잭션 관리
- **Inputs**: ORM 모델, 쿼리 파라미터
- **Processing**: Alembic 마이그레이션, CRUD 작업
- **Outputs**: DB 레코드, 트랜잭션 결과

| Component            | Role                  | Key Capabilities                        |
| -------------------- | --------------------- | --------------------------------------- |
| `database.py`        | DB 세션 관리           | SQLAlchemy Engine, SessionLocal         |
| `models.py`          | ORM 모델 정의          | Document, Chunk, Taxonomy 모델           |
| `alembic/versions/*` | 마이그레이션 스크립트   | 스키마 버전 관리                          |

### 12. Tag Management (`apps/api/tag_management/`)

- **Responsibilities**: @TAG 체계 스캔, 검증, 인벤토리 생성
- **Inputs**: 소스 코드, SPEC 문서
- **Processing**:
  - ripgrep으로 @TAG 스캔
  - SPEC↔TEST↔CODE↔DOC 연결 검증
  - Orphan TAG 탐지
- **Outputs**: TAG 인벤토리 JSON, 검증 보고서

| Component            | Role                  | Key Capabilities                        |
| -------------------- | --------------------- | --------------------------------------- |
| `tag_scanner.py`     | TAG 스캔              | ripgrep 기반 @TAG 추출                   |
| `tag_validator.py`   | TAG 검증              | 체인 연결 확인, 순환 참조 탐지             |

---

## @DOC:INTEGRATION-001 External Integrations

### OpenAI Integration

- **Authentication**: API Key (환경 변수 `OPENAI_API_KEY`)
- **Data Exchange**:
  - Embeddings API: POST /v1/embeddings (JSON)
  - Chat Completions API: POST /v1/chat/completions (JSON)
- **Failure Handling**:
  - Exponential backoff retry (최대 3회)
  - 429 Rate Limit 시 대기 후 재시도
  - Fallback: 에러 시 기본 응답 반환
- **Risk Level**: **High** (서비스 가용성에 직접 영향)
  - Mitigation: 캐싱, 로컬 임베딩 모델 백업 계획

### PostgreSQL Integration

- **Authentication**: 유저명/비밀번호 (환경 변수 `DATABASE_URL`)
- **Data Exchange**:
  - SQLAlchemy ORM (Python ↔ SQL)
  - pgvector 확장 (벡터 연산)
- **Failure Handling**:
  - Connection pooling (최대 10개 커넥션)
  - Automatic reconnection
  - Transaction rollback on error
- **Risk Level**: **Critical** (데이터 손실 가능)
  - Mitigation: 자동 백업 (daily), WAL 아카이빙

### Redis Integration

- **Purpose**: 캐싱, Rate Limiting, Session 관리
- **Dependency Level**: **Medium** (없어도 동작, 성능 저하)
  - Alternatives: In-memory cache (development mode)
- **Performance Requirements**:
  - Latency: <10ms (p99)
  - Throughput: 10k ops/sec
- **Failure Handling**:
  - Cache miss 시 DB로 폴백
  - Rate limit 실패 시 요청 허용 (fail-open)

### Sentry Integration

- **Purpose**: 에러 트래킹, 성능 모니터링
- **Dependency Level**: **Low** (옵저버빌리티 전용)
  - Alternatives: 로컬 로그 파일
- **Performance Requirements**:
  - 샘플링 비율: 10% (운영 환경)
  - 버퍼 크기: 100 events
- **Failure Handling**:
  - Async 전송으로 블로킹 방지
  - 전송 실패 시 로컬 로그로 폴백

### Langfuse Integration

- **Purpose**: LLM 옵저버빌리티, Trace/Span 로깅
- **Authentication**: Public Key + Secret Key (환경 변수)
- **Data Exchange**:
  - REST API (POST /api/public/traces)
  - JSON 페이로드 (trace, span, generation)
- **Failure Handling**:
  - Async 전송, 큐 기반 버퍼링
  - 전송 실패 시 재시도 (최대 3회)
- **Risk Level**: **Low** (서비스 핵심 로직과 독립)
  - Mitigation: 로컬 로그 파일 병행 기록

---

## @DOC:TRACEABILITY-001 Traceability Strategy

### Applying the TAG Framework

**Full TDD Alignment**: SPEC → Tests → Implementation → Documentation
- `@SPEC:ID` (`.moai/specs/`) → `@TEST:ID` (`tests/`) → `@CODE:ID` (`apps/`) → `@DOC:ID` (`.moai/project/`)

**Implementation Detail Levels**: Annotation within `@CODE:ID`
- `@CODE:ID:API` – REST APIs, FastAPI routers
- `@CODE:ID:UI` – React components, Next.js pages
- `@CODE:ID:DATA` – SQLAlchemy models, Pydantic schemas
- `@CODE:ID:DOMAIN` – Business logic, service layer
- `@CODE:ID:INFRA` – Database, Redis, external integrations

### Managing TAG Traceability (Code-Scan Approach)

- **Verification**: Run `/alfred:3-sync`, which scans with `rg '@(SPEC|TEST|CODE|DOC):' -n`
- **Coverage**: Full project source (`.moai/specs/`, `tests/`, `apps/`, `.moai/project/`)
- **Cadence**: Validate whenever the code changes
- **Code-First Principle**: TAG truth lives in the source itself

**Example TAG Chain**:
```
@SPEC:HYBRID-SEARCH-001 (spec.md)
  ↓
@TEST:HYBRID-SEARCH-001 (test_hybrid_search.py:15)
  ↓
@CODE:HYBRID-SEARCH-001:DOMAIN (hybrid_search.py:42)
  ↓
@DOC:HYBRID-SEARCH-001 (structure.md:6)
```

### Orphan TAG Detection

- **Trigger**: `/alfred:3-sync` 실행 시 자동 스캔
- **Detection**:
  - SPEC TAG 없는 TEST/CODE/DOC (미승인 구현)
  - TEST TAG 없는 CODE (테스트 누락)
  - CODE TAG 없는 TEST (좀비 테스트)
- **Remediation**:
  - 경고 메시지 출력
  - TODO 생성 (`.moai/specs/SPEC-*/acceptance.md`)
  - 수동 연결 또는 삭제 유도

---

## Legacy Context

### Current System Snapshot

**DT-RAG v2.0.0은 MoAI-ADK 프레임워크로 완전히 재설계된 시스템입니다.**

```
DT-RAG v2.0.0/
├── apps/                        # Backend (FastAPI)
│   ├── api/                     # API Layer
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── routers/             # API routers (search, ingestion, agent)
│   │   ├── agent_system/        # LangGraph orchestration
│   │   ├── classification/      # Hybrid classification
│   │   ├── ingestion/           # Document processing
│   │   ├── search/              # Hybrid search (BM25 + Vector)
│   │   ├── llm/                 # LLM integration
│   │   ├── db/                  # SQLAlchemy ORM, Alembic
│   │   └── monitoring/          # Langfuse, Sentry
├── apps-frontend/               # Frontend (Next.js 14)
│   ├── app/                     # App Router
│   ├── components/              # shadcn/ui components
│   ├── lib/                     # API client, utilities
│   └── public/                  # Static assets
├── tests/                       # Test suites (pytest, Vitest)
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── e2e/                     # End-to-end tests
├── .moai/                       # MoAI-ADK metadata
│   ├── specs/                   # SPEC documents
│   ├── project/                 # Project docs (this file)
│   └── config.json              # MoAI configuration
└── docker-compose.yml           # PostgreSQL, Redis, MinIO
```

### Migration Considerations

1. **Legacy Code Cleanup** – 기존 v1.x 코드 완전 제거 완료 (v2.0.0에서 완료)
2. **Feature Flag Migration** – CaseBank Vector 활성화 예정 (SPEC-FEATURE-FLAG-001)
3. **Frontend Modernization** – Next.js 14 App Router 전면 적용 완료

---

## TODO:STRUCTURE-001 Structural Improvements

1. **Modularize agent_system** – LangGraph 노드를 독립 모듈로 분리
2. **API Gateway 도입** – Kong/Nginx로 rate limiting, 캐싱 강화
3. **Multi-tenancy 지원** – Tenant별 데이터 격리 (Row-Level Security)
4. **Real-time collaboration** – WebSocket 기반 실시간 검색 결과 업데이트

---

## EARS for Architectural Requirements

### Applying EARS to Architecture

Use EARS patterns to write clear architectural requirements:

#### Architectural EARS Example
```markdown
### Ubiquitous Requirements (Baseline Architecture)
- The system shall adopt a layered architecture separating API, Agent, Core RAG, and Data layers.
- The system shall maintain loose coupling across modules via dependency injection.
- The system shall use PostgreSQL + pgvector for vector storage.

### Event-driven Requirements
- WHEN an OpenAI API call fails, the system shall execute exponential backoff retry (max 3 attempts).
- WHEN a document ingestion completes, the system shall emit a webhook event to subscribers.
- WHEN a classification confidence score < 0.5, the system shall flag for human-in-the-loop review.

### State-driven Requirements
- WHILE in development mode, the system shall provide verbose debug logs.
- WHILE a LangGraph workflow is running, the system shall persist intermediate states to Redis.

### Optional Features
- WHERE high-performance search is required, the system may apply cross-encoder reranking.
- WHERE advanced analytics are needed, the system may export traces to Langfuse.

### Constraints
- IF the security level is elevated, the system shall enforce API Key + JWT authentication.
- Each API endpoint shall respond within 500ms (p95 latency).
- Test coverage shall be ≥85% for all production code.
```

---

_This structure informs the TDD implementation when `/alfred:2-run` runs._
