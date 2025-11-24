# Research Agent Backend Context

> 새 세션에서 백엔드 SPEC 생성 시 이 파일을 참조하세요.

## 선행 작업 완료

### SPEC-FRONTEND-UX-001 (완료)
프론트엔드 Research Agent UI가 Mock 기반으로 완성됨.

**커밋 이력:**
- `47fffff3` - Phase 1: 기본 레이아웃 (ChatZone, ProgressZone, researchStore)
- `6d5209bb` - Phase 2: 문서 미리보기/선택 (DocumentPreview, ConfirmationDialog)
- `f85eb629` - Phase 3: 접근성 (ARIA, 키보드 네비게이션)

---

## 프론트엔드가 정의한 API 계약 (Contract)

### 타입 정의 위치
```
apps/frontend/types/research.ts
```

### 핵심 타입

```typescript
// 리서치 단계 (상태 머신)
export type ResearchStage =
  | 'idle'
  | 'analyzing'
  | 'searching'
  | 'collecting'
  | 'organizing'
  | 'confirming'
  | 'completed'
  | 'error';

// 리서치 세션
export interface ResearchSession {
  id: string;
  query: string;
  stage: ResearchStage;
  progress: number;          // 0-100
  metrics: ResearchMetrics;
  config: ResearchConfig;
  documents: DiscoveredDocument[];
  timeline: StageInfo[];
  startedAt: Date;
  completedAt?: Date;
  error?: string;
}

// 메트릭
export interface ResearchMetrics {
  sourcesSearched: number;
  documentsFound: number;
  qualityScore: number;      // 0-1
  estimatedTimeRemaining?: number;  // seconds
}

// 발견된 문서
export interface DiscoveredDocument {
  id: string;
  title: string;
  source: SourceInfo;
  snippet: string;
  relevanceScore: number;    // 0-1
  collectedAt: Date;
  categories?: string[];
}

// 소스 정보
export interface SourceInfo {
  id: string;
  name: string;
  type: 'web' | 'pdf' | 'api' | 'database';
  url?: string;
  reliability: 'high' | 'medium' | 'low';
}
```

---

## 필요한 API 엔드포인트

### REST API

```
POST /api/v1/research/start
  Request:  { query: string, config?: ResearchConfig }
  Response: { sessionId: string, estimatedDuration: number }

GET  /api/v1/research/{sessionId}/status
  Response: { session: ResearchSession }

POST /api/v1/research/{sessionId}/confirm
  Request:  { selectedDocumentIds: string[], taxonomyId?: string }
  Response: { success: boolean, documentsImported: number, taxonomyUpdated: boolean }

POST /api/v1/research/{sessionId}/cancel
  Response: { success: boolean }
```

### WebSocket

```
WS /ws/research/{sessionId}

Events (Server → Client):
- progress:       { progress: number, currentSource?: string }
- stage_change:   { previousStage, newStage }
- document_found: { document: DiscoveredDocument, totalCount: number }
- metrics_update: { metrics: ResearchMetrics }
- error:          { message: string, recoverable: boolean }
- completed:      { totalDocuments: number, suggestedCategories: string[], qualityScore: number }
```

---

## 백엔드 구현 요구사항

### 1. 리서치 서비스 (`apps/api/services/research_service.py`)
- 쿼리 분석 및 키워드 추출
- 다중 소스 검색 (웹, PDF, API, DB)
- 문서 수집 및 품질 평가
- 카테고리 자동 분류

### 2. WebSocket 핸들러 (`apps/api/routers/research_ws.py`)
- 세션별 실시간 진행률 브로드캐스트
- 단계 전환 알림
- 문서 발견 이벤트

### 3. 저장소 연동
- 세션 상태 저장 (Redis 또는 DB)
- 수집된 문서 임시 저장
- 확정 시 지식 베이스로 이동

### 4. LLM 연동 (선택)
- 쿼리 분석
- 문서 요약
- 품질 평가

---

## 프로젝트 구조 참고

```
apps/
├── frontend/              # ✅ 완료 (Mock 기반)
│   ├── app/research/
│   ├── components/research/
│   ├── stores/researchStore.ts
│   └── types/research.ts   # 📌 API 계약
│
└── api/                   # 🔨 구현 필요
    ├── routers/
    │   ├── research_router.py     # REST API
    │   └── research_ws.py         # WebSocket
    ├── services/
    │   └── research_service.py    # 비즈니스 로직
    └── schemas/
        └── research.py            # Pydantic 스키마
```

---

## 새 세션 시작 명령어

```bash
# SPEC 생성
/alfred:1-plan "Research Agent Backend API - WebSocket 기반 실시간 리서치 엔진"

# 또는 직접 지시
cat .moai/context/CONTEXT-RESEARCH-BACKEND.md
# 이 컨텍스트를 기반으로 SPEC-RESEARCH-BACKEND-001을 생성해줘
```

---

## 참고 파일

| 파일 | 설명 |
|------|------|
| `apps/frontend/types/research.ts` | API 계약 (타입 정의) |
| `apps/frontend/stores/researchStore.ts` | 프론트엔드 상태 관리 |
| `apps/frontend/app/research/page.tsx` | Mock 시뮬레이션 로직 |
| `.moai/specs/SPEC-FRONTEND-UX-001/` | 프론트엔드 SPEC 문서 |
