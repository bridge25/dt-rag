📊 DT-RAG 시스템 기능별 모듈 요약

  🎯 전체 시스템 아키텍처 개요

  ┌─────────────────────────────────────────────────────────────┐
  │                   Frontend Layer (React)                     │
  │          (Dashboard, Search, Taxonomy, HITL, Agents)         │
  └──────────────────────────┬──────────────────────────────────┘
                             │ REST API (FastAPI)
  ┌──────────────────────────┴──────────────────────────────────┐
  │                    Backend Modules (14개)                    │
  │  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
  │  │ Search   │Classify  │ RAG      │ Agent    │Monitoring│  │
  │  │          │          │Orchestr. │ Factory  │          │  │
  │  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
  └─────────────────────────┬───────────────────────────────────┘
                            │
  ┌─────────────────────────┴───────────────────────────────────┐
  │           Data Layer (PostgreSQL + pgvector + Redis)        │
  └─────────────────────────────────────────────────────────────┘

  ---
  📦 1. 핵심 기능 모듈 (Core Features)

  1️⃣ 검색 시스템 (Search System)

  📂 모듈: apps/search/, apps/api/routers/search.py

  🎯 핵심 기능:
  - 하이브리드 검색: BM25 키워드 검색 + Vector 의미적 검색 조합
  - 재순위화 (Reranking): Cross-encoder 기반 정확도 향상
  - 검색 캐싱: Redis 기반 성능 최적화
  - 배치 검색: 여러 쿼리 동시 처리

  🔌 API 엔드포인트:
  POST /api/v1/search               # 단일 검색
  POST /api/v1/search/batch         # 배치 검색
  GET  /api/v1/search/history       # 검색 히스토리
  GET  /api/v1/search/suggestions   # 자동완성 제안

  🎨 프론트엔드 컴포넌트 매핑:
  - SearchBar - 검색 입력 및 필터
  - SearchResultCard - 검색 결과 카드
  - RelevanceIndicator - 관련도 표시
  - SearchAnalytics - 검색 분석 패널

  📊 주요 파라미터:
  {
    query: string,
    top_k: number,           // 반환 개수 (기본: 10)
    bm25_weight: float,      // BM25 가중치 (0~1)
    vector_weight: float,    // Vector 가중치 (0~1)
    taxonomy_filter: string[], // 분류 필터
    rerank: boolean          // 재순위화 활성화
  }

  ---
  2️⃣ 분류 시스템 (Classification System)

  📂 모듈: apps/classification/, apps/api/routers/classification_router.py

  🎯 핵심 기능:
  - 하이브리드 분류: Rule-based + ML 분류 조합
  - 신뢰도 평가: 분류 결과 신뢰도 점수 계산
  - HITL 큐: 낮은 신뢰도 작업 인간 검증 대기열
  - 배치 분류: 대량 문서 자동 분류

  🔌 API 엔드포인트:
  POST /api/v1/classify                      # 단일 문서 분류
  POST /api/v1/classify/batch                # 배치 분류
  GET  /api/v1/classify/queue                # HITL 큐 조회
  POST /api/v1/classify/queue/{id}/approve   # 분류 승인
  POST /api/v1/classify/queue/{id}/reject    # 분류 거부
  GET  /api/v1/classify/confidence/{id}      # 신뢰도 조회

  🎨 프론트엔드 컴포넌트 매핑:
  - HITLQueueCard - HITL 작업 카드
  - ConfidenceIndicator - 신뢰도 시각화 (진행 바)
  - CategorySelector - 분류 선택 트리
  - QuickActionButtons - 승인/거부/스킵 버튼

  📊 워크플로우:
  문서 입력 → ML 분류 → 신뢰도 평가
    ├─ (신뢰도 > 0.7) → 자동 승인
    └─ (신뢰도 < 0.7) → HITL 큐 → 인간 검증

  ---
  3️⃣ 분류 체계 관리 (Taxonomy Management)

  📂 모듈: apps/core/taxonomy/, apps/api/routers/taxonomy_router.py

  🎯 핵심 기능:
  - 계층 구조 관리: DAG 기반 트리 구조
  - 버전 관리: Semantic Versioning (v1.0.0, v1.1.0...)
  - 노드 CRUD: 생성/수정/삭제/이동
  - 경로 검증: 분류 경로 유효성 확인

  🔌 API 엔드포인트:
  GET    /api/v1/taxonomy/versions              # 버전 목록
  GET    /api/v1/taxonomy/{ver}/tree            # 트리 조회
  GET    /api/v1/taxonomy/{ver}/node/{id}       # 노드 상세
  POST   /api/v1/taxonomy/{ver}/node            # 노드 생성
  PUT    /api/v1/taxonomy/{ver}/node/{id}       # 노드 수정
  DELETE /api/v1/taxonomy/{ver}/node/{id}       # 노드 삭제
  POST   /api/v1/taxonomy/{ver}/publish         # 버전 퍼블리시

  🎨 프론트엔드 컴포넌트 매핑:
  - TaxonomyTreeView - 대화형 트리 뷰
  - NodeDetailsPanel - 노드 상세 정보
  - VersionSelector - 버전 선택 드롭다운
  - ContextMenu - 우클릭 메뉴 (추가/수정/삭제)

  📊 데이터 구조:
  {
    id: UUID,
    name: string,
    path: string[],        // ["Technology", "AI", "RAG"]
    parent_id: UUID | null,
    version: string,       // "v1.2.0"
    metadata: object,
    children_count: number
  }

  ---
  4️⃣ RAG 오케스트레이션 (RAG Pipeline)

  📂 모듈: apps/orchestration/, apps/api/routers/orchestration_router.py

  🎯 핵심 기능:
  - LangGraph 파이프라인: 7단계 RAG 워크플로우
  - Multi-Agent Debate: 여러 에이전트의 토론 기반 응답
  - Reflection Engine: 응답 품질 자체 검증
  - Case-Based Reasoning: 과거 사례 기반 추론
  - Soft Q-Learning: 강화학습 기반 정책 최적화

  🔌 API 엔드포인트:
  POST /api/v1/pipeline/execute         # 파이프라인 실행
  GET  /api/v1/pipeline/status/{id}     # 상태 조회
  POST /api/v1/pipeline/cancel/{id}     # 취소
  GET  /api/v1/pipeline/metrics         # 메트릭스

  🎨 프론트엔드 컴포넌트 매핑:
  - PipelineStageIndicator - 7단계 진행 표시
  - DebateVisualization - 에이전트 토론 시각화
  - QualityScoreCard - 품질 점수 표시
  - PipelineMetrics - 단계별 성능 차트

  📊 7단계 파이프라인:
  1. Query Analysis     → 쿼리 분석 (의도, 복잡도)
  2. Taxonomy Routing   → 분류 경로 선택
  3. Hybrid Retrieval   → BM25 + Vector 검색
  4. Reranking         → Cross-encoder 재순위화
  5. Context Composition → 컨텍스트 구성
  6. Generation        → LLM 응답 생성
  7. Quality Check     → 품질 검증 (Faithfulness, Relevancy)

  ---
  5️⃣ 에이전트 팩토리 (Agent Factory)

  📂 모듈: apps/agent_system/, apps/api/routers/agent_factory_router.py

  🎯 핵심 기능:
  - 카테고리 기반 생성: 분류 체계 기반 자동 에이전트 생성
  - 동적 설정: 검색 전략, Top-K, Reranking 등 커스터마이징
  - 라이프사이클 관리: 활성화/비활성화/삭제
  - 성능 모니터링: 에이전트별 메트릭스 추적

  🔌 API 엔드포인트:
  POST   /api/v1/agents/from-category      # 카테고리 기반 생성
  GET    /api/v1/agents/                   # 에이전트 목록
  GET    /api/v1/agents/{id}               # 상세 조회
  PUT    /api/v1/agents/{id}               # 수정
  DELETE /api/v1/agents/{id}               # 삭제
  POST   /api/v1/agents/{id}/activate      # 활성화
  POST   /api/v1/agents/{id}/deactivate    # 비활성화
  GET    /api/v1/agents/{id}/metrics       # 메트릭스

  🎨 프론트엔드 컴포넌트 매핑:
  - AgentCard - 에이전트 카드 (상태, 메트릭스)
  - AgentCreateWizard - 생성 마법사
  - AgentConfigPanel - 설정 편집
  - PerformanceChart - 성능 추이 차트

  📊 에이전트 구조:
  {
    id: UUID,
    name: string,
    status: "active" | "inactive",
    taxonomy_categories: string[],
    retrieval_config: {
      bm25_weight: float,
      vector_weight: float,
      top_k: number,
      rerank: boolean
    },
    metrics: {
      requests: number,
      success_rate: float,
      avg_response_time: float
    }
  }

  ---
  📦 2. 지원 기능 모듈 (Supporting Features)

  6️⃣ 문서 수집 (Document Ingestion)

  📂 모듈: apps/ingestion/, apps/api/routers/ingestion.py

  🎯 핵심 기능:
  - 다형식 지원: PDF, DOCX, TXT, HTML, URL
  - OCR: 이미지 기반 PDF 텍스트 추출
  - PII 필터링: 개인정보 자동 제거
  - 청킹: 텍스트 분할 및 임베딩 생성

  🔌 API 엔드포인트:
  POST /ingestion/upload         # 파일 업로드
  POST /ingestion/urls           # URL 수집
  GET  /ingestion/status/{id}    # 작업 상태
  POST /ingestion/cancel/{id}    # 작업 취소

  🎨 프론트엔드 컴포넌트 매핑:
  - FileUploadDropzone - 드래그 앤 드롭 영역
  - IngestionJobCard - 작업 진행 카드
  - ProgressIndicator - 단계별 진행률
  - ErrorMessage - 에러 처리

  ---
  7️⃣ 벡터 임베딩 (Vector Embeddings)

  📂 모듈: apps/api/embedding_service.py, apps/api/routers/embedding_router.py

  🎯 핵심 기능:
  - 임베딩 생성: Sentence Transformers (768-dim)
  - 배치 처리: 대량 문서 임베딩
  - 캐싱: 중복 임베딩 방지
  - 업데이트: 문서 임베딩 재생성

  🔌 API 엔드포인트:
  GET  /api/v1/embeddings/health                # 서비스 상태
  POST /api/v1/embeddings/generate              # 임베딩 생성
  POST /api/v1/embeddings/documents/update      # 문서 업데이트
  POST /api/v1/embeddings/documents/batch       # 배치 생성
  GET  /api/v1/embeddings/cache/stats           # 캐시 통계

  ---
  8️⃣ 품질 평가 (Evaluation)

  📂 모듈: apps/evaluation/, apps/api/routers/evaluation.py

  🎯 핵심 기능:
  - RAGAS 메트릭스: Faithfulness, Relevancy, Precision, Recall
  - 실험 추적: A/B 테스트 및 버전 비교
  - 골든 데이터셋: 기준 데이터셋 관리
  - 자동 평가: 파이프라인 통합 품질 검증

  🔌 API 엔드포인트:
  POST /api/v1/evaluation/ragas              # RAGAS 평가
  GET  /api/v1/evaluation/metrics            # 메트릭스 조회
  GET  /api/v1/evaluation/golden-dataset     # 골든 데이터
  POST /api/v1/evaluation/golden-dataset/add # 데이터 추가
  GET  /api/v1/evaluation/experiments        # 실험 목록

  📊 RAGAS 메트릭스:
  - Faithfulness (0~1):     응답의 근거성
  - Answer Relevancy (0~1): 답변 관련성
  - Context Precision (0~1): 검색 정확도
  - Context Recall (0~1):    검색 커버리지

  ---
  9️⃣ 모니터링 (Monitoring & Observability)

  📂 모듈: apps/monitoring/, apps/api/routers/monitoring_router.py

  🎯 핵심 기능:
  - 헬스 체크: 시스템 상태 모니터링
  - 메트릭스 수집: Prometheus 기반 메트릭스
  - 에러 추적: Sentry 통합
  - LLM 추적: Langfuse 기반 LLM 호출 추적

  🔌 API 엔드포인트:
  GET /health                        # 기본 헬스 체크
  GET /api/v1/monitoring/health      # 상세 헬스 체크
  GET /api/v1/monitoring/metrics     # 메트릭스
  GET /api/v1/rate-limits            # Rate Limit 정보

  📊 모니터링 메트릭스:
  - Request: 요청 수, 응답 시간, 에러율
  - Search: 검색 지연시간, 결과 수, 캐시 히트율
  - RAG: RAGAS 점수, 파이프라인 단계별 시간
  - System: CPU, 메모리, 디스크

  ---
  🔟 보안 & 인증 (Security)

  📂 모듈: apps/security/, apps/api/routers/admin/api_keys.py

  🎯 핵심 기능:
  - API 키 관리: 생성/삭제/갱신
  - Rate Limiting: Redis 기반 요청 제한
  - JWT 인증: Bearer 토큰 인증
  - 감사 로깅: 모든 API 호출 기록

  🔌 API 엔드포인트:
  POST   /api/v1/admin/api-keys        # API 키 생성
  GET    /api/v1/admin/api-keys        # API 키 목록
  DELETE /api/v1/admin/api-keys/{id}   # API 키 삭제
  PUT    /api/v1/admin/api-keys/{id}   # API 키 수정

  ---
  🎨 프론트엔드 페이지 매핑

  | 페이지            | 주요 기능 모듈                   | 핵심 컴포넌트                                   |
  |----------------|----------------------------|-------------------------------------------|
  | Dashboard      | Monitoring, Search History | MetricCard, ActivityFeed, QualityChart    |
  | Search         | Search, Taxonomy Filter    | SearchBar, ResultCard, AnalyticsPanel     |
  | Taxonomy       | Taxonomy Management        | TreeView, NodeDetails, VersionSelector    |
  | Documents      | Ingestion                  | FileUpload, JobQueue, StatusIndicator     |
  | Classification | Classification, HITL       | HITLCard, ConfidenceBar, QuickActions     |
  | Agents         | Agent Factory              | AgentCard, CreateWizard, PerformanceChart |
  | Monitoring     | Monitoring, Evaluation     | HealthCard, RealTimeChart, AlertPanel     |
  | Settings       | Security, Admin            | APIKeyManager, RateLimitConfig            |

  ---
  🔗 모듈 간 의존성 관계

                      ┌─────────────┐
                      │ Orchestration│
                      │  (RAG 파이프라인)│
                      └──────┬──────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
      ┌────▼────┐       ┌────▼────┐      ┌────▼────┐
      │ Search  │       │Classify │      │  Agent  │
      │ Engine  │       │ System  │      │ Factory │
      └────┬────┘       └────┬────┘      └────┬────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             │
                        ┌────▼────┐
                        │Taxonomy │
                        │ Manager │
                        └────┬────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
      ┌────▼────┐       ┌────▼────┐      ┌────▼────┐
      │Embedding│       │Database │      │ Cache   │
      │ Service │       │(pgvector)│      │ (Redis) │
      └─────────┘       └─────────┘      └─────────┘

  ---
  ★ Insight ─────────────────────────────────────

  1. 계층적 설계: 프로젝트는 명확한 3계층 구조를 따릅니다
  - API Layer: FastAPI 라우터 (사용자 인터페이스)
  - Service Layer: 비즈니스 로직 모듈 (검색, 분류, 오케스트레이션)
  - Data Layer: PostgreSQL + pgvector + Redis (데이터 저장 및 캐싱)

  2. 모듈 간 의존성: 각 모듈은 독립적이면서도 협력적입니다
  - Taxonomy는 모든 모듈의 기반 (분류 체계)
  - Search, Classify, Agent는 Taxonomy를 참조
  - Orchestration은 모든 모듈을 조율하는 중앙 허브

  3. 프론트엔드 설계 시 고려사항:
  - 실시간성: WebSocket 또는 Server-Sent Events로 작업 상태 실시간 업데이트
  - 캐싱: TanStack Query로 API 응답 캐싱하여 UX 향상
  - 오류 처리: 각 모듈별 명확한 에러 메시지 및 재시도 로직 필요

  ─────────────────────────────────────────────────

● 📋 빠른 참조: 우선 구현 순서

  프론트엔드 설계 시 권장하는 구현 순서입니다:

  Phase 1: 핵심 기능 (Week 1-2)

  1. Dashboard - 시스템 상태 모니터링
  2. Search Interface - 하이브리드 검색 및 결과 표시
  3. Document Upload - 파일 업로드 및 처리 상태

  Phase 2: 관리 기능 (Week 3-4)

  4. Taxonomy Management - 분류 체계 트리 뷰어
  5. HITL Queue - 분류 검증 인터페이스
  6. Basic Monitoring - 헬스 체크 및 메트릭스

  Phase 3: 고급 기능 (Week 5-6)

  7. Agent Factory - 에이전트 생성 및 관리
  8. Advanced Analytics - 상세 메트릭스 및 차트
  9. Admin Panel - API 키 관리 및 설정

  ---
  🛠️ 기술 스택 권장사항

  Frontend:
    Framework: React 18 + TypeScript
    UI Library: shadcn/ui + Tailwind CSS
    State: Zustand or Jotai
    Data Fetching: TanStack Query
    Charts: Recharts
    Tree View: react-arborist (대화형 트리)

  Key Libraries:
    - react-dropzone (파일 업로드)
    - react-hook-form + zod (폼 관리)
    - lucide-react (아이콘)
    - date-fns (날짜 처리)

  ---