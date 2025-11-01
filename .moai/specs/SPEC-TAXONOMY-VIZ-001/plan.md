# SPEC-TAXONOMY-VIZ-001 구현 계획

## @PLAN:TAXONOMY-VIZ-001

---

## 개요

Dynamic Taxonomy RAG 시스템의 Taxonomy 구조를 React Flow 기반으로 시각화하는 인터랙티브 컴포넌트를 구현합니다. 사용자는 노드 탐색, 확장/축소, 검색 필터를 통해 Taxonomy 구조를 직관적으로 이해할 수 있습니다.

---

## 우선순위별 마일스톤

### Primary Goals (필수 목표)
1. **React Flow 기본 설정 및 통합**
   - React Flow 라이브러리 설치 및 Vite 설정
   - 기본 캔버스 컴포넌트 구성
   - Zustand 상태 관리 스토어 구축

2. **Taxonomy API 연동**
   - TanStack Query 훅 구현 (`useTaxonomyTree`)
   - API 응답 데이터를 React Flow 노드/엣지로 변환
   - 로딩/에러 상태 처리

3. **커스텀 노드/엣지 컴포넌트**
   - TaxonomyNode 컴포넌트 (레이블, 레벨, 문서 개수 표시)
   - TaxonomyEdge 컴포넌트 (부모-자식 관계 표시)
   - 노드 선택 시 하이라이트 효과

4. **인터랙션 기능**
   - 노드 클릭 → 상세 정보 패널 표시
   - 노드 확장/축소 토글 기능
   - 줌/팬 컨트롤

5. **테스트 작성**
   - 컴포넌트 단위 테스트 (React Testing Library)
   - 훅 테스트 (useTaxonomyTree, Zustand store)
   - E2E 시나리오 테스트 (노드 클릭, 확장/축소)

### Secondary Goals (추가 목표)
1. **미니맵 및 검색 필터**
   - React Flow MiniMap 컴포넌트 통합
   - 검색 필터 UI 및 노드 하이라이트 로직

2. **레이아웃 전환 기능**
   - 트리 레이아웃 (Dagre) 구현
   - 방사형 레이아웃 (D3 force) 구현 (선택)
   - 레이아웃 전환 버튼 UI

3. **성능 최적화**
   - React.memo를 통한 노드/엣지 메모이제이션
   - 500개 이상 노드 시 가상화 적용
   - 디바운싱 및 스로틀링 적용

### Final Goals (최종 목표)
1. **접근성 개선**
   - 키보드 네비게이션 (Tab, Arrow keys)
   - ARIA 레이블 및 스크린 리더 지원
   - 색상 대비 비율 검증 (WCAG 2.1 AA)

2. **문서화**
   - 컴포넌트 사용 가이드 (Storybook 또는 README)
   - API 연동 명세 문서
   - @DOC:TAXONOMY-VIZ-001 태그 추가

---

## 기술 접근

### 아키텍처 설계

#### 디렉토리 구조
```
frontend/src/
├─ components/
│  └─ TaxonomyVisualization/
│     ├─ TaxonomyVisualization.tsx      # 메인 컨테이너 컴포넌트
│     ├─ TaxonomyFlowCanvas.tsx         # React Flow 캔버스
│     ├─ TaxonomyNode.tsx               # 커스텀 노드
│     ├─ TaxonomyEdge.tsx               # 커스텀 엣지
│     ├─ TaxonomyControls.tsx           # 줌, 레이아웃 컨트롤
│     ├─ TaxonomyMiniMap.tsx            # 미니맵
│     ├─ TaxonomyDetailPanel.tsx        # 노드 상세 정보 패널
│     ├─ TaxonomySearchFilter.tsx       # 검색 필터
│     └─ index.ts                       # Barrel export
├─ hooks/
│  └─ useTaxonomyTree.ts                # Taxonomy API 연동 훅
├─ store/
│  └─ taxonomyStore.ts                  # Zustand 상태 관리
├─ utils/
│  ├─ taxonomyTransform.ts              # 데이터 변환 유틸
│  └─ taxonomyLayout.ts                 # 레이아웃 알고리즘
└─ types/
   └─ taxonomy.ts                       # Taxonomy 타입 정의
```

#### 데이터 흐름
1. **초기 로드**: `useTaxonomyTree` 훅 → API 호출 → 응답 데이터를 FlowNode/Edge로 변환
2. **상태 저장**: Zustand `taxonomyStore`에 노드/엣지 저장
3. **렌더링**: React Flow 캔버스에 노드/엣지 표시
4. **인터랙션**: 사용자 클릭 → `setSelectedNode` → 상태 업데이트 → 상세 패널 렌더링

### 기술 스택 상세

#### 핵심 라이브러리
- **React Flow**: `npm install reactflow` (최신 stable 버전)
- **Zustand**: 이미 설치됨 (5.0.8)
- **TanStack Query**: 이미 설치됨 (5.90.5)
- **Tailwind CSS**: 이미 설치됨 (4.1.16)

#### 추가 라이브러리 (선택)
- **Dagre**: `npm install dagre @types/dagre` (트리 레이아웃)
- **D3 Force**: `npm install d3-force @types/d3-force` (방사형 레이아웃)

#### 개발 도구
- **Vite**: 기존 설정 활용 (HMR)
- **Vitest**: 단위/통합 테스트
- **React Testing Library**: 컴포넌트 테스트
- **TypeScript**: 타입 안전성 보장

### 구현 순서

#### Phase 1: 기본 설정 (Primary Goal 1)
1. React Flow 설치 및 Vite 플러그인 설정
2. `TaxonomyVisualization.tsx` 컨테이너 컴포넌트 작성
3. `taxonomyStore.ts` Zustand 스토어 생성
4. 기본 노드/엣지 Mock 데이터로 렌더링 확인

#### Phase 2: API 연동 (Primary Goal 2)
1. `useTaxonomyTree.ts` 훅 구현
2. `taxonomyTransform.ts` 유틸 함수 작성 (API 응답 → FlowNode/Edge)
3. 로딩 스피너 및 에러 메시지 컴포넌트 추가
4. TanStack Query DevTools로 데이터 흐름 검증

#### Phase 3: 커스텀 노드/엣지 (Primary Goal 3)
1. `TaxonomyNode.tsx` 작성 (레이블, 레벨, 문서 개수, 확장 버튼)
2. `TaxonomyEdge.tsx` 작성 (부모-자식 화살표)
3. 노드 선택 시 CSS 클래스 변경으로 하이라이트
4. Tailwind 스타일 적용 (색상, 폰트, 간격)

#### Phase 4: 인터랙션 (Primary Goal 4)
1. 노드 클릭 이벤트 핸들러 구현 (`onNodeClick`)
2. `TaxonomyDetailPanel.tsx` 작성 (선택된 노드 정보 표시)
3. 노드 확장/축소 토글 로직 구현 (`toggleNodeExpansion`)
4. React Flow 줌/팬 컨트롤 활성화 (`<Controls />`)

#### Phase 5: 테스트 (Primary Goal 5)
1. `TaxonomyNode.test.tsx` - 노드 렌더링 및 클릭 이벤트
2. `useTaxonomyTree.test.ts` - API 호출 및 에러 처리
3. `taxonomyStore.test.ts` - 상태 업데이트 로직
4. E2E 테스트 시나리오: 노드 클릭 → 상세 패널 표시

#### Phase 6: 추가 기능 (Secondary Goals)
1. `TaxonomyMiniMap.tsx` 및 `TaxonomySearchFilter.tsx` 구현
2. 레이아웃 전환 버튼 및 `taxonomyLayout.ts` 알고리즘 작성
3. React.memo 및 디바운싱 적용

#### Phase 7: 최종 정리 (Final Goals)
1. 키보드 네비게이션 및 ARIA 레이블 추가
2. WCAG 색상 대비 검증 (Chrome DevTools Lighthouse)
3. 컴포넌트 문서 작성 (JSDoc 주석 + README)

---

## 파일 구조

### 주요 파일 목록

#### 컴포넌트 (8개)
- `TaxonomyVisualization.tsx` - 메인 컨테이너
- `TaxonomyFlowCanvas.tsx` - React Flow 캔버스 래퍼
- `TaxonomyNode.tsx` - 커스텀 노드
- `TaxonomyEdge.tsx` - 커스텀 엣지
- `TaxonomyControls.tsx` - 줌, 레이아웃 컨트롤
- `TaxonomyMiniMap.tsx` - 미니맵
- `TaxonomyDetailPanel.tsx` - 상세 정보 패널
- `TaxonomySearchFilter.tsx` - 검색 필터

#### 훅 (1개)
- `useTaxonomyTree.ts` - Taxonomy API 연동

#### 스토어 (1개)
- `taxonomyStore.ts` - Zustand 상태 관리

#### 유틸리티 (2개)
- `taxonomyTransform.ts` - 데이터 변환
- `taxonomyLayout.ts` - 레이아웃 알고리즘

#### 타입 (1개)
- `taxonomy.ts` - TypeScript 타입 정의

#### 테스트 (5개)
- `TaxonomyVisualization.test.tsx`
- `TaxonomyNode.test.tsx`
- `useTaxonomyTree.test.ts`
- `taxonomyStore.test.ts`
- `TaxonomyE2E.test.tsx`

---

## 의존성 관리

### 기존 의존성 활용
- React 19.1.1
- TypeScript 5.9.3
- Zustand 5.0.8
- TanStack Query 5.90.5
- Axios 1.13.1
- Tailwind CSS 4.1.16

### 신규 설치 (필수)
```bash
npm install reactflow
```

### 신규 설치 (선택 - 레이아웃 알고리즘)
```bash
npm install dagre @types/dagre
npm install d3-force @types/d3-force
```

---

## 리스크 및 완화 전략

### 기술 리스크
1. **React 19와 React Flow 호환성 문제**
   - **완화**: 설치 전 공식 문서 및 GitHub Issues 확인
   - **대안**: React Flow 버전 조정 또는 React 18로 다운그레이드

2. **대규모 Taxonomy 성능 저하**
   - **완화**: 초기 버전은 100개 노드로 제한, 이후 가상화 적용
   - **측정**: Chrome DevTools Performance 프로파일링

3. **레이아웃 알고리즘 복잡도**
   - **완화**: 1차 목표는 기본 트리 레이아웃만 구현, 방사형은 선택 기능

### 일정 리스크
1. **React Flow 학습 곡선**
   - **완화**: 공식 예제 코드 참조, 1일 POC 완료 후 본격 개발
   - **지표**: POC에서 기본 노드 렌더링 성공 시 진행

2. **API 응답 지연**
   - **완화**: Mock 데이터로 프론트엔드 우선 개발
   - **병렬 작업**: 백엔드 API 준비와 독립적으로 진행

---

## 테스트 전략

### 단위 테스트
- **컴포넌트**: 각 컴포넌트의 렌더링 및 이벤트 핸들러 검증
- **훅**: `useTaxonomyTree` API 호출 및 에러 처리
- **스토어**: Zustand 상태 업데이트 로직
- **유틸**: 데이터 변환 함수의 입출력 검증

### 통합 테스트
- React Flow 캔버스와 Zustand 상태 간 연동
- 노드 클릭 → 상태 업데이트 → 상세 패널 렌더링

### E2E 테스트
- 전체 시나리오: 페이지 로드 → Taxonomy 로드 → 노드 클릭 → 상세 정보 확인
- 에러 시나리오: API 실패 → 재시도 버튼 클릭 → 성공

### 성능 테스트
- Lighthouse 성능 점수 (목표: 90 이상)
- 초기 렌더링 시간 측정 (100개 노드 기준 < 2초)
- 메모리 사용량 모니터링 (< 200MB)

---

## 품질 기준

### 코드 품질
- **TypeScript**: Strict mode 활성화, 타입 에러 0건
- **ESLint**: 모든 린트 규칙 통과
- **Prettier**: 코드 포맷 자동 정리

### 테스트 커버리지
- **목표**: 85% 이상
- **측정 도구**: Vitest Coverage (c8)

### 접근성
- **키보드**: Tab, Arrow keys로 노드 탐색 가능
- **ARIA**: 노드, 버튼에 적절한 레이블
- **색상 대비**: WCAG 2.1 AA 준수 (Chrome Lighthouse 검증)

### 성능
- **초기 로드**: < 2초 (100개 노드)
- **노드 클릭 반응**: < 100ms
- **메모리 사용**: < 200MB

---

## 다음 단계 권장

1. **Phase 1 완료 후**: `/alfred:3-sync`로 문서 동기화
2. **Phase 5 완료 후**: Pull Request 생성 및 코드 리뷰
3. **최종 완료 후**: SPEC-AGENT-CREATE-FORM-001로 진행 (Taxonomy 선택 UI 활용)

---

**작성자**: @spec-builder
**작성일**: 2025-10-31
