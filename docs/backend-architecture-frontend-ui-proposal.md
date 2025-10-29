# DT-RAG 백엔드 아키텍처 및 프론트엔드 UI 설계 제안서

> **작성일**: 2025-10-29
> **버전**: v1.8.1
> **목적**: 백엔드 모듈 구조 파악 및 프론트엔드 인터페이스 배치 설계

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [백엔드 아키텍처 분석](#2-백엔드-아키텍처-분석)
3. [API 엔드포인트 맵](#3-api-엔드포인트-맵)
4. [프론트엔드 UI 설계 제안](#4-프론트엔드-ui-설계-제안)
5. [구현 우선순위](#5-구현-우선순위)

---

## 1. 프로젝트 개요

### 1.1 시스템 이름
**Dynamic Taxonomy RAG (Retrieval-Augmented Generation) System v1.8.1**

### 1.2 핵심 기능
- **Taxonomy Management**: 계층적 분류 체계 관리 및 버전 관리
- **Hybrid Search**: BM25 + Vector 하이브리드 검색 및 의미적 재순위화
- **Document Classification**: ML 기반 문서 분류 (Human-in-the-Loop 지원)
- **RAG Orchestration**: LangGraph 기반 7단계 RAG 파이프라인
- **Agent Factory**: 동적 에이전트 생성 및 관리
- **Monitoring & Observability**: 실시간 시스템 모니터링 및 분석

### 1.3 기술 스택
- **Backend**: FastAPI + Python 3.9+
- **Database**: PostgreSQL + pgvector
- **Caching**: Redis
- **Vector Search**: Sentence Transformers (768-dim)
- **ML Framework**: LangGraph + LangChain
- **Monitoring**: Prometheus + Sentry + Langfuse

---

## 2. 백엔드 아키텍처 분석

### 2.1 전체 모듈 구조

```
apps/
├── agent_system/         # 동적 에이전트 시스템
├── api/                  # FastAPI 메인 애플리케이션
├── classification/       # 문서 분류 파이프라인
├── core/                 # 공통 유틸리티 및 설정
├── evaluation/           # RAGAS 기반 품질 평가
├── ingestion/            # 문서 수집 및 처리
├── knowledge_builder/    # 지식베이스 구축
├── monitoring/           # 모니터링 및 메트릭스
├── orchestration/        # RAG 파이프라인 오케스트레이션
├── search/               # 하이브리드 검색 엔진
└── security/             # 인증 및 보안
```

### 2.2 상세 모듈 분석

#### 2.2.1 **Core API Module** (`apps/api/`)
- **역할**: FastAPI 메인 애플리케이션 및 라우터 관리
- **주요 컴포넌트**:
  - `main.py`: 애플리케이션 진입점 및 미들웨어 설정
  - `routers/`: 15개 REST API 라우터
    - `taxonomy_router.py`: 분류 체계 관리
    - `search_router.py`: 하이브리드 검색
    - `classification_router.py`: 문서 분류
    - `orchestration_router.py`: RAG 파이프라인
    - `agent_factory_router.py`: 에이전트 생성
    - `monitoring_router.py`: 모니터링
    - `embedding_router.py`: 임베딩 생성
    - `evaluation.py`: 품질 평가
    - `ingestion.py`: 문서 수집
    - `batch_search.py`: 배치 검색
    - `admin/api_keys.py`: API 키 관리
  - `middleware/`: Rate Limiting, CORS, Logging
  - `models/`: Pydantic 스키마 정의
  - `background/`: 백그라운드 작업 큐

**API 특징**:
- OpenAPI 3.0.3 스펙 준수
- JWT Bearer + API Key 인증
- Rate Limiting (Redis 기반)
- RFC 7807 Problem Details 에러 형식

#### 2.2.2 **Taxonomy Management** (`apps/core/taxonomy/`)
- **역할**: 계층적 분류 체계 관리 (DAG 구조)
- **주요 기능**:
  - 버전 관리 (Semantic Versioning)
  - 트리 구조 조회 및 탐색
  - 노드 CRUD 작업
  - 분류 경로 유효성 검증
  - 마이그레이션 및 롤백

**데이터 구조**:
```python
TaxonomyNode {
  id: UUID
  name: str
  path: List[str]  # 계층 경로
  parent_id: Optional[UUID]
  version: str
  metadata: Dict[str, Any]
}
```

#### 2.2.3 **Hybrid Search Engine** (`apps/search/`)
- **역할**: BM25 + Vector 하이브리드 검색 및 재순위화
- **주요 컴포넌트**:
  - `bm25_search.py`: 키워드 기반 검색
  - `vector_search.py`: 의미적 유사도 검색
  - `hybrid_search.py`: 결과 통합 및 재순위화
  - `reranker.py`: Cross-encoder 기반 재순위화
  - `search_cache.py`: Redis 캐싱

**검색 파라미터**:
- `query`: 검색 쿼리
- `top_k`: 반환 결과 수 (기본: 10)
- `bm25_weight`: BM25 가중치 (기본: 0.5)
- `vector_weight`: Vector 가중치 (기본: 0.5)
- `taxonomy_filter`: 분류 필터링
- `rerank`: 재순위화 활성화

#### 2.2.4 **Classification Pipeline** (`apps/classification/`)
- **역할**: ML 기반 문서 자동 분류
- **주요 컴포넌트**:
  - `hybrid_classifier.py`: Rule-based + ML 분류
  - `semantic_classifier.py`: 의미적 분류
  - `hitl_queue.py`: Human-in-the-Loop 큐
  - `confidence_scorer.py`: 신뢰도 점수 계산

**분류 워크플로우**:
```
문서 입력 → 전처리 → 분류 실행 → 신뢰도 평가
  → (낮은 신뢰도) → HITL 큐 → 인간 검증
  → (높은 신뢰도) → 자동 승인
```

#### 2.2.5 **RAG Orchestration** (`apps/orchestration/`)
- **역할**: LangGraph 기반 7단계 RAG 파이프라인
- **7단계 파이프라인**:
  1. **Query Analysis**: 쿼리 분석 및 의도 파악
  2. **Taxonomy Routing**: 적절한 분류 경로 선택
  3. **Hybrid Retrieval**: BM25 + Vector 검색
  4. **Reranking**: Cross-encoder 재순위화
  5. **Context Composition**: 컨텍스트 구성
  6. **Generation**: LLM 응답 생성
  7. **Quality Check**: 응답 품질 검증

**주요 컴포넌트**:
- `langgraph_pipeline.py`: LangGraph 오케스트레이션
- `meta_planner.py`: 쿼리 계획 수립
- `pipeline_resilience.py`: 재시도 및 메모리 모니터링
- `bandit/policy.py`: Soft Q-learning 정책

#### 2.2.6 **Agent Factory** (`apps/agent_system/`)
- **역할**: 동적 에이전트 생성 및 관리
- **주요 기능**:
  - 분류 카테고리 기반 에이전트 생성
  - 에이전트 라이프사이클 관리 (생성/활성화/비활성화/삭제)
  - 에이전트 성능 모니터링
  - 에이전트 설정 커스터마이징

**에이전트 구조**:
```python
Agent {
  id: UUID
  name: str
  status: "active" | "inactive"
  capabilities: List[str]
  taxonomy_categories: List[str]
  retrieval_config: RetrievalConfig
  features: FeaturesConfig
  performance_metrics: Dict[str, float]
}
```

#### 2.2.7 **Document Ingestion** (`apps/ingestion/`)
- **역할**: 문서 수집 및 전처리 파이프라인
- **지원 형식**: PDF, DOCX, TXT, HTML, URL
- **주요 기능**:
  - 문서 업로드 (파일/URL)
  - OCR (이미지 기반 PDF)
  - 텍스트 추출 및 청킹
  - PII 필터링
  - 메타데이터 추출

**처리 파이프라인**:
```
업로드 → 형식 감지 → 텍스트 추출 → PII 필터링
  → 청킹 → 임베딩 생성 → 저장 (PostgreSQL + pgvector)
```

#### 2.2.8 **Evaluation System** (`apps/evaluation/`)
- **역할**: RAGAS 기반 RAG 품질 평가
- **RAGAS 메트릭**:
  - **Faithfulness**: 응답의 근거성 (0~1)
  - **Answer Relevancy**: 답변 관련성 (0~1)
  - **Context Precision**: 검색 정확도 (0~1)
  - **Context Recall**: 검색 커버리지 (0~1)

**주요 컴포넌트**:
- `ragas_engine.py`: RAGAS 평가 엔진
- `experiment_tracker.py`: 실험 추적
- `golden_dataset.py`: 골든 데이터셋 관리
- `integration.py`: 자동 평가 통합

#### 2.2.9 **Monitoring & Observability** (`apps/monitoring/`)
- **역할**: 실시간 시스템 모니터링 및 메트릭스 수집
- **주요 컴포넌트**:
  - `metrics.py`: Prometheus 메트릭스
  - `health_check.py`: 헬스 체크
  - `dashboard.py`: 모니터링 대시보드
  - `sentry_reporter.py`: 에러 리포팅
  - `langfuse_client.py`: LLM 추적

**모니터링 메트릭**:
- Request 메트릭: 요청 수, 응답 시간, 에러율
- Search 메트릭: 검색 지연시간, 결과 수, 캐시 히트율
- RAG 메트릭: RAGAS 점수, 파이프라인 단계별 시간
- System 메트릭: CPU, 메모리, 디스크, 네트워크

#### 2.2.10 **Vector Embeddings** (`apps/api/embedding_service.py`)
- **역할**: 문서 및 쿼리 벡터 임베딩 생성
- **모델**: Sentence Transformers (768-dim)
- **주요 기능**:
  - 텍스트 → 벡터 변환
  - 배치 임베딩 생성
  - 임베딩 캐싱
  - 문서 임베딩 업데이트

#### 2.2.11 **Security & Authentication** (`apps/security/`)
- **역할**: 인증, 인가 및 보안
- **주요 기능**:
  - JWT Bearer 토큰 인증
  - API 키 관리
  - Rate Limiting
  - CORS 설정
  - PII 필터링
  - 감사 로깅

#### 2.2.12 **Background Processing** (`apps/api/background/`)
- **역할**: 비동기 백그라운드 작업 처리
- **주요 컴포넌트**:
  - `agent_task_queue.py`: 에이전트 작업 큐
  - `agent_task_worker.py`: 작업 워커
  - `webhook_service.py`: 웹훅 처리

#### 2.2.13 **Knowledge Builder** (`apps/knowledge_builder/`)
- **역할**: 지식베이스 구축 및 관리
- **주요 기능**:
  - 문서 그래프 구축
  - 엔티티 추출
  - 관계 추출
  - 커버리지 측정

#### 2.2.14 **Core Utilities** (`apps/core/`)
- **역할**: 공통 유틸리티 및 설정
- **주요 컴포넌트**:
  - `config.py`: 설정 관리
  - `database.py`: DB 연결 관리
  - `env_manager.py`: 환경 관리
  - `cache/`: 캐싱 유틸리티

---

## 3. API 엔드포인트 맵

### 3.1 Core Endpoints

#### Health & System
```
GET  /health                    # 기본 헬스 체크
GET  /api/v1/monitoring/health  # 상세 헬스 체크
GET  /api/versions              # API 버전 정보
GET  /api/v1/rate-limits        # Rate Limit 정보
```

#### Documentation
```
GET  /docs                      # Swagger UI
GET  /redoc                     # ReDoc
GET  /api/v1/openapi.json       # OpenAPI 스펙
```

### 3.2 Taxonomy Management
```
GET    /api/v1/taxonomy/versions                      # 버전 목록
GET    /api/v1/taxonomy/{version}/tree                # 트리 구조 조회
GET    /api/v1/taxonomy/{version}/node/{node_id}      # 노드 상세
POST   /api/v1/taxonomy/{version}/node                # 노드 생성
PUT    /api/v1/taxonomy/{version}/node/{node_id}      # 노드 수정
DELETE /api/v1/taxonomy/{version}/node/{node_id}      # 노드 삭제
POST   /api/v1/taxonomy/{version}/publish             # 버전 퍼블리시
GET    /api/v1/taxonomy/{version}/statistics          # 통계
POST   /api/v1/taxonomy/{version}/validate            # 유효성 검증
GET    /api/v1/taxonomy/compare/{base}/{target}       # 버전 비교
```

### 3.3 Search
```
POST /api/v1/search                 # 하이브리드 검색
POST /api/v1/search/batch           # 배치 검색
GET  /api/v1/search/history         # 검색 히스토리
GET  /api/v1/search/suggestions     # 검색 제안
```

### 3.4 Classification
```
POST   /api/v1/classify                          # 문서 분류
POST   /api/v1/classify/batch                    # 배치 분류
GET    /api/v1/classify/queue                    # HITL 큐 조회
POST   /api/v1/classify/queue/{task_id}/approve  # 분류 승인
POST   /api/v1/classify/queue/{task_id}/reject   # 분류 거부
GET    /api/v1/classify/confidence/{task_id}     # 신뢰도 조회
```

### 3.5 RAG Orchestration
```
POST /api/v1/pipeline/execute           # RAG 파이프라인 실행
GET  /api/v1/pipeline/status/{task_id}  # 파이프라인 상태
POST /api/v1/pipeline/cancel/{task_id}  # 파이프라인 취소
GET  /api/v1/pipeline/metrics           # 파이프라인 메트릭스
```

### 3.6 Agent Factory
```
POST   /api/v1/agents/from-category     # 카테고리 기반 에이전트 생성
GET    /api/v1/agents/                  # 에이전트 목록
GET    /api/v1/agents/{agent_id}        # 에이전트 상세
PUT    /api/v1/agents/{agent_id}        # 에이전트 수정
DELETE /api/v1/agents/{agent_id}        # 에이전트 삭제
POST   /api/v1/agents/{agent_id}/activate    # 에이전트 활성화
POST   /api/v1/agents/{agent_id}/deactivate  # 에이전트 비활성화
GET    /api/v1/agents/{agent_id}/metrics     # 에이전트 메트릭스
GET    /api/v1/agents/factory/status         # Factory 상태
```

### 3.7 Document Ingestion
```
POST /ingestion/upload           # 파일 업로드
POST /ingestion/urls             # URL 수집
GET  /ingestion/status/{job_id}  # 작업 상태
POST /ingestion/cancel/{job_id}  # 작업 취소
```

### 3.8 Vector Embeddings
```
GET  /api/v1/embeddings/health                 # 임베딩 서비스 상태
POST /api/v1/embeddings/generate               # 임베딩 생성
POST /api/v1/embeddings/documents/update       # 문서 임베딩 업데이트
POST /api/v1/embeddings/documents/batch        # 배치 임베딩 생성
GET  /api/v1/embeddings/cache/stats            # 캐시 통계
```

### 3.9 Evaluation
```
POST /api/v1/evaluation/ragas                  # RAGAS 평가 실행
GET  /api/v1/evaluation/metrics                # 평가 메트릭스 조회
GET  /api/v1/evaluation/golden-dataset        # 골든 데이터셋 조회
POST /api/v1/evaluation/golden-dataset/add    # 골든 데이터 추가
GET  /api/v1/evaluation/experiments           # 실험 목록
```

### 3.10 Admin & Management
```
POST   /api/v1/admin/api-keys              # API 키 생성
GET    /api/v1/admin/api-keys              # API 키 목록
DELETE /api/v1/admin/api-keys/{key_id}     # API 키 삭제
PUT    /api/v1/admin/api-keys/{key_id}     # API 키 수정
```

---

## 4. 프론트엔드 UI 설계 제안

### 4.1 UI 설계 원칙 (2025 RAG 시스템 베스트 프랙티스 기반)

#### 4.1.1 핵심 원칙
1. **Transparency & Explainability**: RAG 검색 과정의 투명성
2. **Visual Hierarchy**: 정보의 명확한 계층 구조
3. **Immediate Feedback**: 모든 작업에 대한 즉각적 피드백 (500ms 이내)
4. **Citation Tracing**: 답변의 근거를 추적 가능한 인용
5. **Accessibility**: WCAG 2.1 AA 준수

#### 4.1.2 RAG 특화 디자인 패턴
- **Chunk Visualization**: 텍스트 청크의 시각적 표현
- **Taxonomy Navigation**: 계층적 분류 체계 네비게이션
- **Confidence Indicators**: 신뢰도 시각화 (색상 코드, 진행 바)
- **Real-time Metrics**: 실시간 성능 지표 표시
- **Human-in-the-Loop UI**: HITL 작업 큐 및 검증 인터페이스

### 4.2 레이아웃 구조

```
┌─────────────────────────────────────────────────────────────────┐
│ Header (Navigation)                                              │
│ - Logo                                                           │
│ - Search Bar (Global)                                            │
│ - User Menu (Profile, Settings, Logout)                          │
│ - Notifications                                                   │
└─────────────────────────────────────────────────────────────────┘
┌────────────┬─────────────────────────────────────────────────────┐
│            │                                                      │
│ Sidebar    │  Main Content Area                                  │
│            │                                                      │
│ - Dashboard│  (Dynamic based on current view)                    │
│ - Search   │                                                      │
│ - Taxonomy │                                                      │
│ - Documents│                                                      │
│ - Agents   │                                                      │
│ - HITL     │                                                      │
│ - Monitor  │                                                      │
│ - Settings │                                                      │
│            │                                                      │
└────────────┴─────────────────────────────────────────────────────┘
```

### 4.3 페이지별 상세 설계

#### 4.3.1 Dashboard (홈 페이지)
**목적**: 시스템 전체 상태 및 핵심 메트릭스 한눈에 파악

**구성 요소**:
```
┌─────────────────────────────────────────────────────────────┐
│ System Status Cards (4-Grid Layout)                         │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐│
│ │ Search      │ │ Classification│ │ Documents   │ │ Agents  ││
│ │ Queries: 1.2K│ │ Accuracy: 94% │ │ Total: 5.3K │ │ Active:8││
│ │ Avg: 1.89s  │ │ HITL: 23     │ │ New: 127    │ │ Idle: 4 ││
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘│
│                                                               │
│ RAGAS Quality Metrics (Line Chart - Last 7 Days)            │
│ ┌───────────────────────────────────────────────────────────┐│
│ │ Faithfulness: ─────────────────────────── 0.89          ││
│ │ Relevancy:    ─────────────────────────── 0.91          ││
│ │ Precision:    ─────────────────────────── 0.87          ││
│ │ Recall:       ─────────────────────────── 0.85          ││
│ └───────────────────────────────────────────────────────────┘│
│                                                               │
│ Recent Activity Feed                                          │
│ ┌───────────────────────────────────────────────────────────┐│
│ │ 🔍 Search: "How to implement RAG?" - 2 min ago           ││
│ │ 📁 Classification: 5 documents → Tech/AI - 5 min ago     ││
│ │ 🤖 Agent Created: Agent-Science-Biology - 10 min ago     ││
│ │ ✅ HITL Task Approved: Document #1234 - 15 min ago       ││
│ └───────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**API 연동**:
- `GET /api/v1/monitoring/health`: 시스템 상태
- `GET /api/v1/evaluation/metrics`: RAGAS 메트릭스
- `GET /api/v1/search/history`: 최근 검색
- `GET /api/v1/classify/queue`: HITL 큐

#### 4.3.2 Search Interface (검색 페이지)
**목적**: 하이브리드 검색 및 결과 탐색

**구성 요소**:
```
┌─────────────────────────────────────────────────────────────┐
│ Search Bar                                                   │
│ ┌───────────────────────────────────────────────────────────┐│
│ │ 🔍 Search... [Advanced Filters ▼] [Search]              ││
│ └───────────────────────────────────────────────────────────┘│
│                                                               │
│ Advanced Filters (Collapsible)                               │
│ ┌───────────────────────────────────────────────────────────┐│
│ │ Top K: [10▼]  BM25 Weight: [━━━━━●─] 0.5                ││
│ │ Taxonomy Filter: [Technology > AI > RAG]                 ││
│ │ Date Range: [2024-01-01] to [2025-10-29]                 ││
│ │ Rerank: [✓] Enabled                                      ││
│ └───────────────────────────────────────────────────────────┘│
│                                                               │
│ Search Results (10 results, 0.89s)                           │
│ ┌───────────────────────────────────────────────────────────┐│
│ │ 📄 Document #1: "Introduction to RAG Systems"            ││
│ │    Technology > AI > RAG | Relevance: 0.94 | BM25: 0.87 ││
│ │    "RAG systems combine retrieval with generation..."    ││
│ │    [View Full] [Cite] [Related: 3]                       ││
│ ├───────────────────────────────────────────────────────────┤│
│ │ 📄 Document #2: "Building Production RAG"                ││
│ │    Technology > AI > RAG | Relevance: 0.91 | Vector: 0.9││
│ │    "Production RAG requires careful consideration..."    ││
│ │    [View Full] [Cite] [Related: 5]                       ││
│ └───────────────────────────────────────────────────────────┘│
│                                                               │
│ Search Analytics (Right Panel)                               │
│ ┌───────────────────────────────────────────────────────────┐│
│ │ Query Analysis:                                           ││
│ │ - Intent: Informational                                   ││
│ │ - Complexity: Medium                                      ││
│ │ - Taxonomy Match: Technology > AI > RAG                   ││
│ │                                                           ││
│ │ Retrieved Chunks: 25 → Reranked: 10 → Displayed: 10     ││
│ │ Pipeline: 7 steps, 890ms total                           ││
│ └───────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**UI 패턴**:
- **Search-as-you-type**: 자동완성 제안
- **Loading State**: 검색 진행 중 단계별 표시
  - "Analyzing query..." (Step 1/7)
  - "Retrieving documents..." (Step 3/7)
  - "Reranking results..." (Step 4/7)
- **Result Cards**: 문서 미리보기 카드
- **Citation Highlighting**: 인용 구간 하이라이트
- **Related Documents**: 관련 문서 추천

**API 연동**:
- `POST /api/v1/search`: 검색 실행
- `GET /api/v1/search/suggestions`: 검색 제안
- `GET /api/v1/search/history`: 검색 히스토리

#### 4.3.3 Taxonomy Management (분류 체계 관리)
**목적**: 계층적 분류 체계 시각화 및 관리

**구성 요소**:
```
┌─────────────────────────────────────────────────────────────┐
│ Taxonomy Version Selector                                    │
│ Current: [v1.2.0 ▼] | [Create New Version] [Compare]        │
│                                                               │
│ ┌────────────────────┬─────────────────────────────────────┐│
│ │ Tree View          │ Node Details                         ││
│ │                    │                                      ││
│ │ 📁 Technology      │ 📁 Artificial Intelligence           ││
│ │   ├─ 📁 AI        │ ID: AI-001                          ││
│ │   │  ├─ 📄 RAG    │ Path: Technology > AI                ││
│ │   │  ├─ 📄 LLM    │ Created: 2025-01-15                  ││
│ │   │  └─ 📄 ML     │ Documents: 1,234                     ││
│ │   └─ 📁 Web       │ Children: 3 (RAG, LLM, ML)          ││
│ │ 📁 Science        │                                      ││
│ │   ├─ 📁 Biology   │ Description:                         ││
│ │   └─ 📁 Physics   │ Artificial Intelligence encompasses ││
│ │                    │ machine learning, deep learning...   ││
│ │                    │                                      ││
│ │                    │ [Edit] [Delete] [Add Child]          ││
│ └────────────────────┴─────────────────────────────────────┘│
│                                                               │
│ Actions                                                       │
│ [+ Add Root Node] [Import JSON] [Export JSON] [Validate]     │
│ [Publish Version]                                             │
└─────────────────────────────────────────────────────────────┘
```

**UI 패턴**:
- **Interactive Tree**: 드래그 앤 드롭으로 노드 이동
- **Contextual Menu**: 우클릭 메뉴 (Add Child, Edit, Delete)
- **Search in Tree**: 트리 내 노드 검색
- **Breadcrumbs**: 현재 선택된 노드의 경로 표시
- **Version Compare**: 두 버전 간 차이점 시각화

**API 연동**:
- `GET /api/v1/taxonomy/versions`: 버전 목록
- `GET /api/v1/taxonomy/{version}/tree`: 트리 구조
- `POST /api/v1/taxonomy/{version}/node`: 노드 생성
- `PUT /api/v1/taxonomy/{version}/node/{node_id}`: 노드 수정
- `DELETE /api/v1/taxonomy/{version}/node/{node_id}`: 노드 삭제

#### 4.3.4 Document Ingestion (문서 수집)
**목적**: 문서 업로드 및 처리 상태 모니터링

**구성 요소**:
```
┌─────────────────────────────────────────────────────────────┐
│ Upload Methods                                               │
│ ┌──────────────────┐ ┌──────────────────┐                   │
│ │ 📁 File Upload   │ │ 🌐 URL Import   │                   │
│ │ Drag & Drop      │ │ Enter URL       │                   │
│ │ or Click to      │ │ ┌──────────────┐│                   │
│ │ Browse           │ │ │https://...   ││                   │
│ │                  │ │ └──────────────┘│                   │
│ │ [Browse Files]   │ │ [Import URL]    │                   │
│ └──────────────────┘ └──────────────────┘                   │
│                                                               │
│ Supported Formats: PDF, DOCX, TXT, HTML, Markdown            │
│                                                               │
│ Processing Queue (3 jobs)                                     │
│ ┌───────────────────────────────────────────────────────────┐│
│ │ Job #12345: "whitepaper.pdf"                              ││
│ │ [████████████────────────] 60% - Extracting text...      ││
│ │ Status: Processing | Started: 2 min ago | ETA: 1 min     ││
│ │ [Cancel] [Details]                                        ││
│ ├───────────────────────────────────────────────────────────┤│
│ │ Job #12344: "https://example.com/article"                ││
│ │ [████████████████████] 100% - Complete!                  ││
│ │ Status: Success | Documents: 15 | Chunks: 234            ││
│ │ [View Documents] [Download Report]                        ││
│ ├───────────────────────────────────────────────────────────┤│
│ │ Job #12343: "research-paper.pdf"                          ││
│ │ [████────────────────────] 20% - PII filtering...        ││
│ │ Status: Processing | Started: 5 min ago | ETA: 3 min     ││
│ │ [Cancel] [Details]                                        ││
│ └───────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**UI 패턴**:
- **Drag & Drop Area**: 파일 드래그 앤 드롭 영역
- **Upload Progress**: 실시간 업로드 진행률
- **Job Queue**: 처리 중인 작업 목록
- **Stage Indicators**: 파이프라인 단계별 표시
  - 📤 Uploading
  - 📄 Extracting
  - 🔒 PII Filtering
  - ✂️ Chunking
  - 🧮 Embedding
  - 💾 Storing
- **Error Handling**: 실패 시 명확한 에러 메시지 및 재시도 옵션

**API 연동**:
- `POST /ingestion/upload`: 파일 업로드
- `POST /ingestion/urls`: URL 수집
- `GET /ingestion/status/{job_id}`: 작업 상태
- `POST /ingestion/cancel/{job_id}`: 작업 취소

#### 4.3.5 HITL Queue (Human-in-the-Loop)
**목적**: 낮은 신뢰도 분류 작업 검증

**구성 요소**:
```
┌─────────────────────────────────────────────────────────────┐
│ HITL Queue (23 pending tasks)                               │
│ Filters: [All ▼] [Confidence: <0.7] [Sort by: Priority ▼]   │
│                                                               │
│ ┌───────────────────────────────────────────────────────────┐│
│ │ Task #5678 | Priority: High | Confidence: 0.62           ││
│ │                                                           ││
│ │ Document: "Quantum Computing Applications"               ││
│ │ Original Text: "Quantum computing leverages quantum..."  ││
│ │                                                           ││
│ │ ML Predicted Categories (Top 3):                         ││
│ │ 1. Technology > Quantum Computing  [●●●●●○] 0.62        ││
│ │ 2. Science > Physics              [●●●●○○] 0.51        ││
│ │ 3. Technology > Computing         [●●●○○○] 0.45        ││
│ │                                                           ││
│ │ Select Correct Category:                                  ││
│ │ [Taxonomy Tree Selector]                                  ││
│ │ Selected: Technology > Quantum Computing                  ││
│ │                                                           ││
│ │ [✓ Approve] [✗ Reject] [Skip] [Add to Training Set]     ││
│ └───────────────────────────────────────────────────────────┘│
│                                                               │
│ Statistics                                                    │
│ ┌───────────────────────────────────────────────────────────┐│
│ │ Today: 15 approved, 3 rejected, 5 skipped                ││
│ │ Avg Time: 1m 23s per task                                ││
│ │ Accuracy Improvement: +2.3% (after HITL feedback)        ││
│ └───────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**UI 패턴**:
- **Task Cards**: 검증 대기 작업 카드
- **Confidence Visualization**: 신뢰도 막대 그래프
- **Quick Actions**: 빠른 승인/거부 버튼
- **Bulk Actions**: 여러 작업 일괄 처리
- **Training Feedback**: "Add to Training Set" 옵션
- **Keyboard Shortcuts**: 빠른 작업을 위한 단축키
  - `A`: Approve
  - `R`: Reject
  - `S`: Skip
  - `T`: Add to Training

**API 연동**:
- `GET /api/v1/classify/queue`: HITL 큐 조회
- `POST /api/v1/classify/queue/{task_id}/approve`: 승인
- `POST /api/v1/classify/queue/{task_id}/reject`: 거부
- `GET /api/v1/classify/confidence/{task_id}`: 신뢰도 조회

#### 4.3.6 Agent Factory (에이전트 관리)
**목적**: 동적 에이전트 생성 및 모니터링

**구성 요소**:
```
┌─────────────────────────────────────────────────────────────┐
│ Agents (12 total, 8 active)                                 │
│ [+ Create from Category] [+ Create Custom] [Factory Status]  │
│                                                               │
│ ┌───────────────────────────────────────────────────────────┐│
│ │ Agent List                                                ││
│ │ ┌───────────────────────────────────────────────────────┐││
│ │ │ 🤖 Agent-Technology-AI                                │││
│ │ │ Status: 🟢 Active | Created: 2025-01-15              │││
│ │ │ Categories: Technology > AI                           │││
│ │ │ Metrics: 245 requests | 94% success | 1.89s avg      │││
│ │ │ [Details] [Edit] [Deactivate] [Delete]               │││
│ │ ├───────────────────────────────────────────────────────┤││
│ │ │ 🤖 Agent-Science-Biology                              │││
│ │ │ Status: ⚪ Inactive | Created: 2024-12-20            │││
│ │ │ Categories: Science > Biology                         │││
│ │ │ Metrics: 67 requests | 91% success | 2.15s avg       │││
│ │ │ [Details] [Edit] [Activate] [Delete]                 │││
│ │ └───────────────────────────────────────────────────────┘││
│ └───────────────────────────────────────────────────────────┘│
│                                                               │
│ Agent Details (Agent-Technology-AI)                          │
│ ┌───────────────────────────────────────────────────────────┐│
│ │ Configuration                                             ││
│ │ - Retrieval: Hybrid (BM25: 0.5, Vector: 0.5)            ││
│ │ - Top K: 10                                              ││
│ │ - Reranking: Enabled                                     ││
│ │ - Context Window: 4096 tokens                            ││
│ │                                                           ││
│ │ Performance (Last 7 Days)                                ││
│ │ [Line Chart: Requests, Avg Response Time, Success Rate]  ││
│ │                                                           ││
│ │ Recent Requests                                          ││
│ │ - Query: "Explain RAG" | Response: 1.5s | Status: ✓     ││
│ │ - Query: "LLM architectures" | Response: 2.1s | Status: ✓││
│ └───────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**UI 패턴**:
- **Agent Cards**: 에이전트 상태 카드
- **Status Indicators**: 시각적 상태 표시 (🟢 Active, ⚪ Inactive)
- **Performance Charts**: 성능 메트릭스 차트
- **Configuration Panel**: 에이전트 설정 편집
- **Quick Actions**: 빠른 활성화/비활성화
- **Create Wizard**: 에이전트 생성 마법사

**API 연동**:
- `GET /api/v1/agents/`: 에이전트 목록
- `POST /api/v1/agents/from-category`: 카테고리 기반 생성
- `GET /api/v1/agents/{agent_id}`: 에이전트 상세
- `PUT /api/v1/agents/{agent_id}`: 에이전트 수정
- `POST /api/v1/agents/{agent_id}/activate`: 활성화
- `POST /api/v1/agents/{agent_id}/deactivate`: 비활성화
- `DELETE /api/v1/agents/{agent_id}`: 삭제
- `GET /api/v1/agents/{agent_id}/metrics`: 메트릭스

#### 4.3.7 Monitoring Dashboard (모니터링)
**목적**: 실시간 시스템 모니터링 및 메트릭스 분석

**구성 요소**:
```
┌─────────────────────────────────────────────────────────────┐
│ System Health                                                │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│ │ API      │ │ Database │ │ Redis    │ │ Embeddings│       │
│ │ 🟢 Healthy│ │ 🟢 Online│ │ 🟢 Online│ │ 🟢 Online │       │
│ │ 99.9% up │ │ 5ms ping │ │ 2ms ping │ │ Available │       │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                               │
│ Real-time Metrics (Auto-refresh: 10s)                        │
│ ┌───────────────────────────────────────────────────────────┐│
│ │ Requests/sec: [Line Chart]      🔴 Live                   ││
│ │ Current: 125 req/s | Peak: 340 req/s (10:45 AM)          ││
│ ├───────────────────────────────────────────────────────────┤│
│ │ Response Time: [Histogram]                                ││
│ │ P50: 0.89s | P95: 2.34s | P99: 4.12s                     ││
│ ├───────────────────────────────────────────────────────────┤│
│ │ Error Rate: [Area Chart]                                  ││
│ │ Current: 0.3% | 24h Avg: 0.5%                            ││
│ └───────────────────────────────────────────────────────────┘│
│                                                               │
│ RAGAS Quality Metrics (Last 24 Hours)                        │
│ ┌───────────────────────────────────────────────────────────┐│
│ │ Faithfulness:     [●●●●●●●●●○] 0.89 (Target: 0.85 ✓)    ││
│ │ Answer Relevancy: [●●●●●●●●●○] 0.91 (Target: 0.85 ✓)    ││
│ │ Precision:        [●●●●●●●●○○] 0.87 (Target: 0.85 ✓)    ││
│ │ Recall:           [●●●●●●●●○○] 0.85 (Target: 0.85 ✓)    ││
│ └───────────────────────────────────────────────────────────┘│
│                                                               │
│ Alerts & Warnings                                            │
│ ┌───────────────────────────────────────────────────────────┐│
│ │ ⚠️ High Memory Usage: 87% (Threshold: 90%)               ││
│ │ ℹ️ 3 HITL tasks pending > 24h                            ││
│ │ ✅ All quality gates passing                              ││
│ └───────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**UI 패턴**:
- **Health Status Cards**: 서비스별 헬스 카드
- **Real-time Charts**: 실시간 메트릭스 차트
- **Quality Gates**: 품질 게이트 시각화 (목표 대비 현재 값)
- **Alert Panel**: 알림 및 경고 패널
- **Drill-down**: 차트 클릭 시 상세 데이터 조회
- **Time Range Selector**: 시간 범위 선택 (1h, 24h, 7d, 30d)

**API 연동**:
- `GET /api/v1/monitoring/health`: 헬스 체크
- `GET /api/v1/evaluation/metrics`: RAGAS 메트릭스
- `GET /api/v1/pipeline/metrics`: 파이프라인 메트릭스
- `GET /api/v1/search/history`: 검색 히스토리

### 4.4 UI 컴포넌트 라이브러리 추천

#### 4.4.1 추천 프레임워크
1. **React + TypeScript** (권장)
   - Component Library: **shadcn/ui** (Tailwind CSS 기반)
   - State Management: **Zustand** 또는 **Jotai**
   - Data Fetching: **TanStack Query** (React Query)
   - Routing: **React Router v6**
   - Charts: **Recharts** 또는 **Apache ECharts**

2. **Vue 3 + TypeScript** (대안)
   - Component Library: **Naive UI** 또는 **Ant Design Vue**
   - State Management: **Pinia**
   - Data Fetching: **TanStack Query Vue**

#### 4.4.2 핵심 컴포넌트
```typescript
// Reusable Components
- SearchBar
- TaxonomyTree
- DocumentCard
- AgentCard
- MetricCard
- ChartContainer
- LoadingStates
- ErrorBoundary
- ConfidenceIndicator
- CitationPopover
- HITLTaskCard
- PipelineStageIndicator
```

### 4.5 색상 팔레트 (다크/라이트 모드 지원)

#### Light Mode
```css
--primary: #3B82F6      /* Blue - Primary actions */
--secondary: #10B981    /* Green - Success states */
--accent: #F59E0B       /* Amber - Warnings */
--danger: #EF4444       /* Red - Errors/Delete */
--background: #FFFFFF   /* White */
--surface: #F9FAFB      /* Light Gray */
--text-primary: #111827 /* Almost Black */
--text-secondary: #6B7280 /* Gray */
--border: #E5E7EB       /* Light Gray */
```

#### Dark Mode
```css
--primary: #60A5FA      /* Light Blue */
--secondary: #34D399    /* Light Green */
--accent: #FBBF24       /* Light Amber */
--danger: #F87171       /* Light Red */
--background: #111827   /* Dark */
--surface: #1F2937      /* Dark Gray */
--text-primary: #F9FAFB /* Off-white */
--text-secondary: #9CA3AF /* Gray */
--border: #374151       /* Dark Gray */
```

### 4.6 반응형 디자인 브레이크포인트

```css
/* Mobile First Approach */
--mobile: 320px   /* sm */
--tablet: 768px   /* md */
--desktop: 1024px /* lg */
--wide: 1280px    /* xl */
--ultra: 1536px   /* 2xl */
```

**레이아웃 변화**:
- **Mobile (<768px)**: Single column, collapsible sidebar
- **Tablet (768-1024px)**: Sidebar + main content
- **Desktop (>1024px)**: Full layout with right panel

### 4.7 접근성 (Accessibility) 체크리스트

- ✅ **Keyboard Navigation**: 모든 기능 키보드 접근 가능
- ✅ **Screen Reader**: ARIA labels 및 roles 적용
- ✅ **Color Contrast**: WCAG 2.1 AA 준수 (4.5:1 텍스트, 3:1 UI)
- ✅ **Focus Indicators**: 명확한 포커스 표시
- ✅ **Skip Links**: 메인 콘텐츠로 건너뛰기 링크
- ✅ **Alt Text**: 모든 이미지 대체 텍스트
- ✅ **Form Labels**: 모든 입력 필드 라벨
- ✅ **Error Messages**: 명확하고 구체적인 에러 메시지

---

## 5. 구현 우선순위

### Phase 1: MVP (Minimum Viable Product)
**목표**: 핵심 기능 프로토타입

**우선순위 1 (Week 1-2)**:
1. ✅ Dashboard (기본 메트릭스)
2. ✅ Search Interface (하이브리드 검색)
3. ✅ Document Ingestion (파일 업로드)

**우선순위 2 (Week 3-4)**:
4. ✅ Taxonomy Management (트리 뷰어)
5. ✅ HITL Queue (기본 검증)
6. ✅ Monitoring (헬스 체크)

### Phase 2: Enhanced Features
**목표**: 고급 기능 및 UX 개선

**우선순위 3 (Week 5-6)**:
7. ✅ Agent Factory (에이전트 관리)
8. ✅ Advanced Search Filters
9. ✅ Real-time Notifications

**우선순위 4 (Week 7-8)**:
10. ✅ Interactive Charts
11. ✅ Batch Operations
12. ✅ Export/Import

### Phase 3: Production Ready
**목표**: 프로덕션 배포 준비

**우선순위 5 (Week 9-10)**:
13. ✅ Performance Optimization
14. ✅ Comprehensive Testing
15. ✅ Documentation
16. ✅ User Onboarding

**우선순위 6 (Week 11-12)**:
17. ✅ Advanced Analytics
18. ✅ Custom Dashboards
19. ✅ API Playground
20. ✅ Mobile Responsive

---

## 6. 기술 스택 추천

### 6.1 Frontend Stack
```yaml
Framework: React 18 + TypeScript 5
Build Tool: Vite 5
UI Library: shadcn/ui + Tailwind CSS 3
State: Zustand 4
Data: TanStack Query 5
Routing: React Router 6
Charts: Recharts 2
Forms: React Hook Form + Zod
Icons: Lucide React
Testing: Vitest + Testing Library
E2E: Playwright
```

### 6.2 Development Tools
```yaml
Package Manager: pnpm
Code Quality: ESLint + Prettier + Biome
Type Checking: TypeScript strict mode
Git Hooks: Husky + lint-staged
Documentation: Storybook
```

### 6.3 Deployment
```yaml
Hosting: Vercel / Netlify
CDN: Cloudflare
Monitoring: Sentry (Frontend Errors)
Analytics: PostHog (Product Analytics)
```

---

## 7. 참고 자료

### 7.1 디자인 시스템 참고
- **Vercel Design System**: https://vercel.com/design
- **Radix UI**: https://www.radix-ui.com/
- **shadcn/ui**: https://ui.shadcn.com/

### 7.2 RAG UI 참고 사례
- **RAGFlow**: https://github.com/infiniflow/ragflow
- **Open WebUI**: https://docs.openwebui.com/
- **LangChain Hub**: https://smith.langchain.com/

### 7.3 2025 UI/UX 트렌드
- **2025 UI Design Principles**: https://www.lyssna.com/blog/ui-design-principles/
- **RAG Best Practices**: https://humanloop.com/blog/rag-architectures

---

## 8. 결론

### 8.1 핵심 요약

본 보고서는 **Dynamic Taxonomy RAG System v1.8.1**의 백엔드 아키텍처를 14개 모듈로 분석하고, 최신 RAG UI/UX 베스트 프랙티스를 반영한 프론트엔드 인터페이스 설계를 제안했습니다.

**주요 특징**:
- 📊 **7개 핵심 화면**: Dashboard, Search, Taxonomy, Ingestion, HITL, Agents, Monitoring
- 🎨 **2025 RAG UI 패턴**: Transparency, Citation Tracing, Confidence Visualization
- 🚀 **최신 기술 스택**: React 18 + TypeScript + shadcn/ui + TanStack Query
- ♿ **접근성 우선**: WCAG 2.1 AA 준수
- 📱 **반응형 디자인**: Mobile-first approach

### 8.2 다음 단계

1. **프로토타입 개발** (Week 1-2)
   - Dashboard + Search Interface 구현
   - API 연동 테스트

2. **사용자 테스트** (Week 3)
   - 내부 팀 피드백 수집
   - UI/UX 개선

3. **MVP 출시** (Week 4)
   - 핵심 기능 배포
   - 모니터링 시작

4. **점진적 개선** (Week 5+)
   - 사용자 피드백 반영
   - 고급 기능 추가

---

**작성자**: Claude (Anthropic AI)
**검토자**: [프로젝트 리드]
**최종 수정**: 2025-10-29
