---
id: TAXONOMY-VIZ-001
version: 1.0.0
status: implemented
created: 2025-10-31
updated: 2025-10-31
author: @sonheungmin
priority: high
category: feature
labels:
  - frontend
  - react
  - typescript
  - visualization
  - taxonomy
implementation_status:
  core_features: completed
  optional_features: completed
  accessibility: in_progress
  documentation: completed
---

# SPEC-TAXONOMY-VIZ-001: Dynamic Taxonomy 시각화 with React Flow

## HISTORY

### v1.0.0 (2025-10-31)
- **STATUS**: 구현 완료 (implemented)
- **CORE FEATURES**: 모든 필수 기능 구현 완료
  - React Flow 기반 트리 시각화
  - 노드 클릭 → 상세 정보 패널
  - 노드 확장/축소 토글
  - 검색 필터 (디바운싱 300ms)
  - 미니맵 및 줌/팬 컨트롤
- **OPTIONAL FEATURES**: 레이아웃 전환 기능 구현 완료
  - 트리 레이아웃 (Dagre)
  - 방사형 레이아웃 (Radial)
- **ACCESSIBILITY**: 접근성 개선 진행 중
  - ARIA 레이블 및 role 속성 추가
  - Focus 관리 개선
  - WCAG 2.1 AA 준수 목표
- **TESTS**: 7개 테스트 파일, 8개 TEST TAG
- **DOCUMENTATION**: README 업데이트 완료

### v0.0.1 (2025-10-31)
- **INITIAL**: SPEC 초안 작성
- **AUTHOR**: @sonheungmin
- **SECTIONS**: 전체 EARS 요구사항 정의, React Flow 기반 Taxonomy 시각화 설계

---

## @SPEC:TAXONOMY-VIZ-001 개요

### 목적
Dynamic Taxonomy RAG 시스템의 핵심인 Taxonomy 구조를 사용자에게 직관적으로 시각화하고, 노드 간 관계 탐색 및 실시간 업데이트를 지원하는 인터랙티브 컴포넌트를 구현한다.

### 범위
- React Flow 기반 Taxonomy 트리/그래프 시각화
- 노드 클릭 시 상세 정보 표시 (분류 레벨, 연결된 문서 개수)
- 노드 확장/축소 (collapse/expand) 기능
- 실시간 Taxonomy 업데이트 반영
- 줌/팬 컨트롤 및 미니맵 지원

### 제외 사항
- Taxonomy 편집 기능 (향후 SPEC으로 분리)
- 문서 업로드 UI (별도 SPEC-DATA-UPLOAD-001)
- Agent 생성/관리 UI (별도 SPEC-AGENT-CREATE-FORM-001)

---

## Environment (환경)

### 기술 스택
- **프론트엔드**: React 19.1.1, TypeScript 5.9.3, Vite 7.1.7
- **시각화 라이브러리**: React Flow (최신 stable 버전 사용)
- **상태 관리**: Zustand 5.0.8 (Taxonomy 상태), TanStack Query 5.90.5 (서버 상태)
- **스타일링**: Tailwind CSS 4.1.16
- **HTTP 클라이언트**: Axios 1.13.1

### 백엔드 연동
- **API 엔드포인트**: `GET /api/taxonomy/tree` - Taxonomy 전체 구조 조회
- **응답 형식**: JSON (노드 ID, 레이블, 레벨, 자식 노드, 문서 카운트)
- **실시간 업데이트**: WebSocket 또는 Polling (설계 단계에서 결정)

### 개발 환경
- **Node.js**: v18+ (프로젝트 표준)
- **패키지 매니저**: npm
- **개발 서버**: Vite Dev Server (HMR 지원)

---

## Assumptions (가정)

### 백엔드 API 가정
1. **Taxonomy API 존재**: 백엔드에 Taxonomy 트리 구조를 제공하는 REST API가 이미 구현되어 있다.
2. **표준 JSON 형식**: 노드 구조는 `id`, `label`, `level`, `children[]`, `documentCount` 필드를 포함한다.
3. **인증**: API 호출 시 JWT 인증이 필요하며, 프론트엔드에 인증 토큰이 저장되어 있다.

### 사용자 환경 가정
1. **최신 브라우저**: Chrome 90+, Firefox 88+, Safari 14+ (ES2020 지원)
2. **화면 크기**: 최소 1024x768 해상도 (반응형은 SPEC-MOBILE-RESPONSIVE-001에서 처리)
3. **네트워크**: 안정적인 인터넷 연결 (초기 로드 시 Taxonomy 데이터 크기 < 1MB)

### 기술적 가정
1. **React Flow 호환성**: React 19와 React Flow의 최신 버전이 호환된다.
2. **성능**: 노드 수 < 500개 (대규모 Taxonomy는 가상화/페이징으로 처리)
3. **브라우저 Canvas 지원**: React Flow의 Canvas 렌더링을 모든 타겟 브라우저가 지원한다.

---

## Requirements (요구사항)

### Ubiquitous Requirements (기본 요구사항)
- **REQ-TAXVIZ-U001**: 시스템은 Taxonomy 트리 구조를 노드-엣지 그래프로 시각화해야 한다.
- **REQ-TAXVIZ-U002**: 시스템은 각 노드에 분류명, 레벨, 문서 개수를 표시해야 한다.
- **REQ-TAXVIZ-U003**: 시스템은 줌 인/아웃 및 팬(드래그) 기능을 제공해야 한다.
- **REQ-TAXVIZ-U004**: 시스템은 미니맵을 제공하여 전체 구조 탐색을 지원해야 한다.
- **REQ-TAXVIZ-U005**: 시스템은 로딩 상태와 에러 상태를 사용자에게 명확히 표시해야 한다.

### Event-driven Requirements (이벤트 기반 요구사항)
- **REQ-TAXVIZ-E001**: WHEN 사용자가 노드를 클릭하면, 시스템은 해당 노드의 상세 정보를 사이드 패널에 표시해야 한다.
- **REQ-TAXVIZ-E002**: WHEN 사용자가 확장 가능한 노드의 토글 버튼을 클릭하면, 시스템은 자식 노드를 표시하거나 숨겨야 한다.
- **REQ-TAXVIZ-E003**: WHEN Taxonomy 데이터가 업데이트되면, 시스템은 그래프를 자동으로 다시 렌더링해야 한다.
- **REQ-TAXVIZ-E004**: WHEN 초기 로드가 실패하면, 시스템은 재시도 버튼과 함께 에러 메시지를 표시해야 한다.
- **REQ-TAXVIZ-E005**: WHEN 사용자가 검색 필터를 입력하면, 시스템은 매칭되는 노드만 하이라이트해야 한다.

### State-driven Requirements (상태 기반 요구사항)
- **REQ-TAXVIZ-S001**: WHILE 데이터 로딩 중이면, 시스템은 스켈레톤 로더 또는 스피너를 표시해야 한다.
- **REQ-TAXVIZ-S002**: WHILE 노드가 선택된 상태이면, 시스템은 해당 노드를 시각적으로 강조해야 한다 (색상, 테두리 등).
- **REQ-TAXVIZ-S003**: WHILE 사용자가 드래그 중이면, 시스템은 마우스 커서를 그랩(grab) 아이콘으로 변경해야 한다.

### Optional Features (선택 기능)
- **REQ-TAXVIZ-O001**: WHERE 사용자가 레이아웃 옵션을 선택하면, 시스템은 트리 레이아웃 또는 방사형 레이아웃을 적용할 수 있다.
- **REQ-TAXVIZ-O002**: WHERE 노드 개수가 100개 이상이면, 시스템은 가상화를 통해 성능을 최적화할 수 있다.
- **REQ-TAXVIZ-O003**: WHERE 관리자 권한이 있으면, 시스템은 노드 편집 모드로 전환할 수 있다 (향후 확장).

### Constraints (제약사항)
- **REQ-TAXVIZ-C001**: IF Taxonomy API 응답 시간이 5초를 초과하면, 시스템은 타임아웃 에러를 표시해야 한다.
- **REQ-TAXVIZ-C002**: 시스템은 노드 레이블 길이를 최대 50자로 제한해야 한다 (초과 시 말줄임).
- **REQ-TAXVIZ-C003**: 시스템은 최대 500개의 노드를 동시에 렌더링할 수 있어야 한다 (초과 시 경고 표시).
- **REQ-TAXVIZ-C004**: 시스템은 브라우저 메모리 사용량을 200MB 이하로 유지해야 한다 (React Flow 캔버스 포함).

---

## Specifications (상세 설계)

### 컴포넌트 구조
```typescript
// 주요 컴포넌트 계층
<TaxonomyVisualization>
  ├─ <TaxonomyFlowCanvas>       // React Flow 메인 캔버스
  │   ├─ <TaxonomyNode>         // 커스텀 노드 컴포넌트
  │   └─ <TaxonomyEdge>         // 커스텀 엣지 컴포넌트
  ├─ <TaxonomyControls>         // 줌, 레이아웃 변경 컨트롤
  ├─ <TaxonomyMiniMap>          // 미니맵
  ├─ <TaxonomyDetailPanel>      // 선택된 노드 상세 정보
  └─ <TaxonomySearchFilter>     // 노드 검색 필터
```

### 데이터 모델
```typescript
// Taxonomy 노드 타입
interface TaxonomyNode {
  id: string;
  label: string;
  level: number;
  documentCount: number;
  children: TaxonomyNode[];
  parentId?: string;
}

// React Flow 노드 타입
interface FlowNode extends Node {
  data: {
    taxonomyNode: TaxonomyNode;
    isExpanded: boolean;
  };
}

// Zustand 상태
interface TaxonomyState {
  nodes: FlowNode[];
  edges: Edge[];
  selectedNodeId: string | null;
  layout: 'tree' | 'radial';
  setSelectedNode: (id: string | null) => void;
  toggleNodeExpansion: (id: string) => void;
  updateLayout: (layout: 'tree' | 'radial') => void;
}
```

### API 연동
```typescript
// TanStack Query 훅
export function useTaxonomyTree() {
  return useQuery({
    queryKey: ['taxonomy', 'tree'],
    queryFn: async () => {
      const response = await axios.get('/api/taxonomy/tree');
      return response.data as TaxonomyNode;
    },
    staleTime: 5 * 60 * 1000, // 5분
    retry: 3,
  });
}

// 실시간 업데이트 (선택 기능)
export function useTaxonomyUpdates() {
  const queryClient = useQueryClient();

  useEffect(() => {
    // WebSocket 또는 Polling 로직
    const interval = setInterval(() => {
      queryClient.invalidateQueries(['taxonomy', 'tree']);
    }, 30000); // 30초마다 갱신

    return () => clearInterval(interval);
  }, [queryClient]);
}
```

### 레이아웃 알고리즘
- **트리 레이아웃** (기본): Dagre 알고리즘 (상→하 방향)
- **방사형 레이아웃** (선택): D3 force-directed 레이아웃

### 성능 최적화
1. **Memoization**: 노드/엣지 렌더링 시 React.memo 적용
2. **가상화**: 500개 이상 노드 시 viewport culling
3. **디바운싱**: 검색 필터 입력 시 300ms debounce
4. **레이지 로딩**: 하위 노드는 expand 시 동적 로드 (선택)

---

## Traceability (추적성)

### TAG 체인
- **@SPEC:TAXONOMY-VIZ-001** → Taxonomy 시각화 요구사항 정의
- **@TEST:TAXONOMY-VIZ-001** → 컴포넌트 단위 테스트, E2E 테스트
- **@CODE:TAXONOMY-VIZ-001** → React 컴포넌트, 훅, 유틸리티 함수
- **@DOC:TAXONOMY-VIZ-001** → 사용자 가이드, API 문서

### 의존성
- **depends_on**:
  - SPEC-FRONTEND-INIT-001 (프론트엔드 초기 설정)
  - SPEC-FRONTEND-INTEGRATION-001 (백엔드 API 연동)
- **blocks**:
  - SPEC-AGENT-CREATE-FORM-001 (Taxonomy 선택 UI에 활용)

### 관련 SPEC
- **related_specs**:
  - SPEC-DATA-UPLOAD-001 (데이터 업로드 후 Taxonomy 업데이트)
  - SPEC-RESEARCH-AGENT-UI-001 (Agent와 Taxonomy 연동)

---

## 품질 기준

### 기능 완성도
- ✅ 모든 Ubiquitous, Event-driven, State-driven 요구사항 구현
- ✅ 최소 1개 이상의 Optional Feature 구현 (레이아웃 전환 권장)
- ✅ 모든 Constraints 준수

### 테스트 커버리지
- **단위 테스트**: 컴포넌트, 훅, 유틸리티 함수 (Coverage ≥ 85%)
- **통합 테스트**: React Flow 캔버스와 Zustand 상태 연동
- **E2E 테스트**: 노드 클릭 → 상세 정보 표시 시나리오

### 성능 기준
- 초기 렌더링 시간 < 2초 (100개 노드 기준)
- 노드 클릭 반응 시간 < 100ms
- 메모리 사용량 < 200MB (Chrome DevTools Memory Profiler)

### 접근성
- 키보드 네비게이션 지원 (Tab, Arrow keys)
- ARIA 레이블 적용 (노드, 컨트롤 버튼)
- 색상 대비 비율 WCAG 2.1 AA 준수

---

## 리스크 및 완화 전략

### 기술 리스크
1. **React 19 호환성 문제**
   - **완화**: React Flow 공식 문서 확인, 필요시 다운그레이드 또는 패치
2. **대규모 Taxonomy 성능 저하**
   - **완화**: 가상화 및 페이징 적용, 노드 수 제한
3. **실시간 업데이트 충돌**
   - **완화**: Optimistic update + 충돌 감지 로직

### 일정 리스크
1. **React Flow 학습 곡선**
   - **완화**: 공식 예제 참조, 2일 이내 POC 완료
2. **API 응답 지연**
   - **완화**: Mock 데이터 우선 개발, 병렬 작업

---

## 참고 자료
- [React Flow 공식 문서](https://reactflow.dev/)
- [TanStack Query 가이드](https://tanstack.com/query/latest)
- [Zustand 문서](https://zustand-demo.pmnd.rs/)
