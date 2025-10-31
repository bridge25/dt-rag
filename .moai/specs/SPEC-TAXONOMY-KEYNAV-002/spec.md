---
id: TAXONOMY-KEYNAV-002
version: 0.0.1
status: draft
created: 2025-11-01
updated: 2025-11-01
author: @sonheungmin
priority: high
category: feature
labels:
  - accessibility
  - keyboard-navigation
  - a11y
  - wcag
  - frontend
depends_on:
  - TAXONOMY-VIZ-001
related_specs:
  - TAXONOMY-VIZ-001
scope:
  packages:
    - frontend/src/components/taxonomy
  files:
    - TaxonomyVisualization.tsx
    - TaxonomyFlowCanvas.tsx
    - TaxonomyNode.tsx
---

# SPEC-TAXONOMY-KEYNAV-002: Taxonomy 시각화를 위한 완전한 키보드 네비게이션 구현

## HISTORY

### v0.0.1 (2025-11-01)
- **STATUS**: 초안 작성 (draft)
- **AUTHOR**: @sonheungmin
- **PURPOSE**: SPEC-TAXONOMY-VIZ-001의 접근성 개선 - 키보드 전용 사용자를 위한 완전한 네비게이션 구현
- **SCOPE**: Tab/Arrow/Enter/Space/Escape 키 지원, Focus trap, WCAG 2.1 AA 준수
- **DEPENDENCIES**: SPEC-TAXONOMY-VIZ-001 (v1.0.0) 구현 완료 상태

---

## @SPEC:TAXONOMY-KEYNAV-002 개요

### 목적
SPEC-TAXONOMY-VIZ-001에서 구현된 Taxonomy 시각화 컴포넌트에 완전한 키보드 네비게이션 기능을 추가하여, 마우스 없이도 모든 기능에 접근 가능하도록 WCAG 2.1 Level AA 접근성 기준을 충족한다.

### 범위
- **Tab 키 네비게이션**: 노드, 컨트롤, 패널 간 논리적 순서로 포커스 이동
- **Arrow 키 네비게이션**: 노드 간 상/하/좌/우 방향 탐색
- **Enter/Space 키 액션**: 노드 선택, 확장/축소, 버튼 활성화
- **Escape 키**: 패널 닫기, 포커스 초기화
- **Focus Trap**: 모달/패널 열린 상태에서 포커스 제한
- **키보드 단축키**: 검색 포커스 (`/`), 줌 인/아웃 (`+`/`-`), 레이아웃 전환 (`L`)

### 제외 사항
- **스크린 리더 최적화**: 별도 SPEC-TAXONOMY-SCREENREADER-003으로 분리
- **터치 제스처**: 모바일 접근성은 SPEC-MOBILE-ACCESSIBLE-004에서 처리
- **음성 인식**: 향후 SPEC-VOICE-CONTROL-005로 확장

---

## Environment (환경)

### 기술 스택
- **프론트엔드**: React 19.1.1, TypeScript 5.9.3
- **시각화 라이브러리**: React Flow (SPEC-TAXONOMY-VIZ-001에서 설정됨)
- **접근성 라이브러리**:
  - `react-focus-trap` (최신 stable 버전)
  - `react-hotkeys-hook` v4.5.1 (키보드 단축키 관리)
- **상태 관리**: Zustand 5.0.8 (포커스 상태 추가)
- **테스트**:
  - Vitest (단위 테스트)
  - Playwright (E2E 키보드 인터랙션 테스트)

### 브라우저 호환성
- **Chrome 90+**: Keyboard API 완전 지원
- **Firefox 88+**: Keyboard API 완전 지원
- **Safari 14+**: Keyboard API 기본 지원
- **Edge 90+**: Chrome 동일

### WCAG 2.1 Level AA 준수 항목
- **2.1.1 Keyboard**: 모든 기능을 키보드로 조작 가능
- **2.1.2 No Keyboard Trap**: 포커스 트랩에서 Escape로 탈출 가능
- **2.4.3 Focus Order**: 논리적 포커스 순서 유지
- **2.4.7 Focus Visible**: 포커스 상태 시각적으로 명확히 표시

---

## Assumptions (가정)

### 사용자 환경 가정
1. **키보드 사용자**: 마우스 없이 키보드만으로 시스템을 조작하는 사용자가 존재한다.
2. **표준 키보드 레이아웃**: QWERTY 키보드 또는 동등한 키 배열 사용 (다국어 키보드 고려).
3. **최신 브라우저**: 사용자는 Keyboard API를 지원하는 최신 브라우저를 사용한다.

### 기술적 가정
1. **React Flow 키보드 이벤트 지원**: React Flow가 키보드 이벤트를 기본적으로 전달한다 (커스텀 핸들러 필요 시 우회 가능).
2. **포커스 관리 라이브러리 호환**: `react-focus-trap`과 React 19가 충돌 없이 작동한다.
3. **기존 SPEC 완료**: SPEC-TAXONOMY-VIZ-001의 모든 컴포넌트가 구현되어 있으며, 이를 확장한다.

### 의존성 가정
1. **SPEC-TAXONOMY-VIZ-001 완료**: 노드, 엣지, 컨트롤, 패널 등 모든 UI 요소가 이미 구현되어 있다.
2. **Zustand 상태 확장 가능**: 기존 Zustand 스토어에 포커스 관련 상태를 추가할 수 있다.
3. **테스트 환경**: Playwright를 사용하여 키보드 이벤트를 시뮬레이션할 수 있다.

---

## Requirements (요구사항)

### Ubiquitous Requirements (기본 요구사항)
- **REQ-KEYNAV-U001**: 시스템은 모든 인터랙티브 요소(노드, 버튼, 입력 필드)에 키보드로 접근 가능해야 한다.
- **REQ-KEYNAV-U002**: 시스템은 포커스된 요소를 명확히 시각적으로 표시해야 한다 (2px 파란색 outline, 색상 대비 4.5:1 이상).
- **REQ-KEYNAV-U003**: 시스템은 논리적 포커스 순서(검색 → 컨트롤 → 노드 → 패널)를 유지해야 한다.
- **REQ-KEYNAV-U004**: 시스템은 키보드 단축키를 제공하고, 단축키 목록을 `?` 키로 표시해야 한다.

### Event-driven Requirements (이벤트 기반 요구사항)
- **REQ-KEYNAV-E001**: WHEN 사용자가 Tab 키를 누르면, 시스템은 다음 인터랙티브 요소로 포커스를 이동해야 한다.
- **REQ-KEYNAV-E002**: WHEN 사용자가 노드에 포커스된 상태에서 Arrow 키를 누르면, 시스템은 인접한 노드로 포커스를 이동해야 한다 (상/하/좌/우 방향).
- **REQ-KEYNAV-E003**: WHEN 사용자가 노드에 포커스된 상태에서 Enter 또는 Space 키를 누르면, 시스템은 해당 노드를 선택하고 상세 패널을 열어야 한다.
- **REQ-KEYNAV-E004**: WHEN 사용자가 상세 패널이 열린 상태에서 Escape 키를 누르면, 시스템은 패널을 닫고 이전 포커스로 복귀해야 한다.
- **REQ-KEYNAV-E005**: WHEN 사용자가 `/` 키를 누르면, 시스템은 검색 입력 필드로 포커스를 이동해야 한다.
- **REQ-KEYNAV-E006**: WHEN 사용자가 `?` 키를 누르면, 시스템은 키보드 단축키 도움말 모달을 표시해야 한다.

### State-driven Requirements (상태 기반 요구사항)
- **REQ-KEYNAV-S001**: WHILE 상세 패널이 열려 있으면, 시스템은 패널 내부로 포커스를 제한해야 한다 (Focus Trap).
- **REQ-KEYNAV-S002**: WHILE 노드에 포커스가 있으면, 시스템은 해당 노드를 화면 중앙으로 스크롤해야 한다 (viewport 밖일 경우).
- **REQ-KEYNAV-S003**: WHILE 검색 입력 필드에 포커스가 있으면, 시스템은 Arrow 키 네비게이션을 비활성화해야 한다 (텍스트 편집 우선).

### Optional Features (선택 기능)
- **REQ-KEYNAV-O001**: WHERE 사용자가 `+`/`-` 키를 누르면, 시스템은 캔버스를 줌 인/아웃할 수 있다.
- **REQ-KEYNAV-O002**: WHERE 사용자가 `L` 키를 누르면, 시스템은 레이아웃을 전환(트리 ↔ 방사형)할 수 있다.
- **REQ-KEYNAV-O003**: WHERE 사용자가 `Home` 키를 누르면, 시스템은 첫 번째 노드로 포커스를 이동할 수 있다.

### Constraints (제약사항)
- **REQ-KEYNAV-C001**: 시스템은 브라우저 기본 키보드 단축키(Ctrl+F, Ctrl+R 등)와 충돌하지 않아야 한다.
- **REQ-KEYNAV-C002**: 시스템은 키보드 이벤트 처리 시 100ms 이내 반응해야 한다 (딜레이 없음).
- **REQ-KEYNAV-C003**: 시스템은 포커스 인디케이터를 항상 표시해야 하며, `outline: none` 사용을 금지한다.
- **REQ-KEYNAV-C004**: 시스템은 최대 20개의 키보드 단축키를 등록할 수 있다 (충돌 방지).

---

## Specifications (상세 설계)

### 포커스 관리 전략

#### 1. 포커스 순서 (Tab Order)
```typescript
// 논리적 포커스 순서
1. SearchFilter Input
2. Layout Toggle Button
3. Zoom In Button
4. Zoom Out Button
5. MiniMap
6. Taxonomy Nodes (트리 구조 순서)
7. Detail Panel (열려 있을 경우)
   7.1. Close Button
   7.2. Expand/Collapse Button
   7.3. Action Buttons
```

#### 2. Zustand 상태 확장
```typescript
// 기존 TaxonomyState 확장
interface TaxonomyState {
  // ... 기존 필드
  focusedNodeId: string | null;
  focusHistory: string[]; // Escape 시 복귀용
  keyboardMode: 'navigation' | 'search' | 'panel';
  setFocusedNode: (id: string | null) => void;
  pushFocusHistory: (id: string) => void;
  popFocusHistory: () => string | null;
  setKeyboardMode: (mode: 'navigation' | 'search' | 'panel') => void;
}
```

#### 3. Arrow 키 네비게이션 로직
```typescript
// 인접 노드 찾기 알고리즘
function findAdjacentNode(
  currentNodeId: string,
  direction: 'up' | 'down' | 'left' | 'right',
  nodes: FlowNode[],
  edges: Edge[]
): string | null {
  const currentNode = nodes.find(n => n.id === currentNodeId);
  if (!currentNode) return null;

  // 방향별 노드 필터링
  const candidates = nodes.filter(node => {
    const dx = node.position.x - currentNode.position.x;
    const dy = node.position.y - currentNode.position.y;

    switch (direction) {
      case 'up': return dy < -50; // 위쪽 노드
      case 'down': return dy > 50; // 아래쪽 노드
      case 'left': return dx < -50; // 왼쪽 노드
      case 'right': return dx > 50; // 오른쪽 노드
    }
  });

  // 가장 가까운 노드 선택 (유클리드 거리)
  return candidates.sort((a, b) => {
    const distA = Math.hypot(
      a.position.x - currentNode.position.x,
      a.position.y - currentNode.position.y
    );
    const distB = Math.hypot(
      b.position.x - currentNode.position.x,
      b.position.y - currentNode.position.y
    );
    return distA - distB;
  })[0]?.id || null;
}
```

### 키보드 이벤트 핸들러

#### 1. 전역 키보드 단축키
```typescript
import { useHotkeys } from 'react-hotkeys-hook';

export function TaxonomyVisualization() {
  const { keyboardMode, setKeyboardMode } = useTaxonomyStore();

  // 검색 포커스
  useHotkeys('/', (e) => {
    e.preventDefault();
    setKeyboardMode('search');
    document.getElementById('taxonomy-search')?.focus();
  }, { enableOnFormTags: false });

  // 줌 인/아웃
  useHotkeys('+', () => zoomIn(), { enableOnFormTags: false });
  useHotkeys('-', () => zoomOut(), { enableOnFormTags: false });

  // 레이아웃 전환
  useHotkeys('l', () => toggleLayout(), { enableOnFormTags: false });

  // 도움말
  useHotkeys('?', () => setHelpModalOpen(true), { enableOnFormTags: false });

  // 첫 노드로 이동
  useHotkeys('home', () => focusFirstNode(), { enableOnFormTags: false });

  // ...
}
```

#### 2. 노드별 키보드 핸들러
```typescript
export function TaxonomyNode({ data, id }: NodeProps) {
  const { setFocusedNode, setSelectedNode } = useTaxonomyStore();

  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'Enter':
      case ' ': // Space
        e.preventDefault();
        setSelectedNode(id);
        break;
      case 'ArrowUp':
        e.preventDefault();
        moveFocus('up');
        break;
      case 'ArrowDown':
        e.preventDefault();
        moveFocus('down');
        break;
      case 'ArrowLeft':
        e.preventDefault();
        moveFocus('left');
        break;
      case 'ArrowRight':
        e.preventDefault();
        moveFocus('right');
        break;
      case 'Escape':
        e.preventDefault();
        setSelectedNode(null);
        break;
    }
  };

  return (
    <div
      tabIndex={0}
      role="button"
      aria-label={`노드: ${data.label}`}
      onKeyDown={handleKeyDown}
      onFocus={() => setFocusedNode(id)}
      className="focus:outline-blue-500 focus:outline-2"
    >
      {/* 노드 내용 */}
    </div>
  );
}
```

### Focus Trap 구현

#### 1. 상세 패널 Focus Trap
```typescript
import FocusTrap from 'react-focus-trap';

export function TaxonomyDetailPanel({ nodeId, onClose }: Props) {
  const { pushFocusHistory } = useTaxonomyStore();

  useEffect(() => {
    pushFocusHistory(document.activeElement?.id || '');
  }, []);

  const handleEscape = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
      restoreFocus();
    }
  };

  return (
    <FocusTrap active={true}>
      <div
        role="dialog"
        aria-modal="true"
        onKeyDown={handleEscape}
        className="taxonomy-detail-panel"
      >
        <button onClick={onClose} aria-label="패널 닫기">
          ✕
        </button>
        {/* 패널 내용 */}
      </div>
    </FocusTrap>
  );
}
```

### 포커스 인디케이터 스타일링

#### 1. Tailwind CSS 커스텀 포커스 스타일
```css
/* globals.css */
:focus-visible {
  outline: 2px solid #3b82f6; /* blue-500 */
  outline-offset: 2px;
}

.taxonomy-node:focus-visible {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.5);
}

/* 포커스 인디케이터 비활성화 금지 */
* {
  outline: revert !important;
}
```

### 키보드 단축키 도움말

#### 1. 도움말 모달
```typescript
export function KeyboardShortcutsModal({ isOpen, onClose }: Props) {
  const shortcuts = [
    { key: 'Tab', description: '다음 요소로 이동' },
    { key: 'Shift + Tab', description: '이전 요소로 이동' },
    { key: 'Arrow Keys', description: '인접 노드로 이동' },
    { key: 'Enter / Space', description: '노드 선택' },
    { key: 'Escape', description: '패널 닫기 / 포커스 해제' },
    { key: '/', description: '검색 포커스' },
    { key: '+', description: '줌 인' },
    { key: '-', description: '줌 아웃' },
    { key: 'L', description: '레이아웃 전환' },
    { key: 'Home', description: '첫 노드로 이동' },
    { key: '?', description: '단축키 도움말' },
  ];

  return (
    <FocusTrap active={isOpen}>
      <div role="dialog" aria-labelledby="shortcuts-title">
        <h2 id="shortcuts-title">키보드 단축키</h2>
        <table>
          <thead>
            <tr>
              <th>키</th>
              <th>기능</th>
            </tr>
          </thead>
          <tbody>
            {shortcuts.map(s => (
              <tr key={s.key}>
                <td><kbd>{s.key}</kbd></td>
                <td>{s.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <button onClick={onClose}>닫기</button>
      </div>
    </FocusTrap>
  );
}
```

---

## Traceability (추적성)

### TAG 체인
- **@SPEC:TAXONOMY-KEYNAV-002** → 키보드 네비게이션 요구사항 정의
- **@TEST:TAXONOMY-KEYNAV-002** → E2E 키보드 인터랙션 테스트, 접근성 자동화 테스트
- **@CODE:TAXONOMY-KEYNAV-002** → 키보드 핸들러, Focus Trap, 단축키 관리
- **@DOC:TAXONOMY-KEYNAV-002** → 키보드 단축키 가이드, 접근성 문서

### 의존성
- **depends_on**:
  - SPEC-TAXONOMY-VIZ-001 (v1.0.0) - 모든 UI 컴포넌트 구현 완료 필요

### 관련 SPEC
- **related_specs**:
  - SPEC-TAXONOMY-VIZ-001 - 기본 시각화 컴포넌트
  - SPEC-TAXONOMY-SCREENREADER-003 (예정) - 스크린 리더 최적화
  - SPEC-MOBILE-ACCESSIBLE-004 (예정) - 모바일 접근성

---

## 품질 기준

### 기능 완성도
- ✅ 모든 Ubiquitous, Event-driven, State-driven 요구사항 구현
- ✅ 최소 2개 이상의 Optional Features 구현 (줌, 레이아웃 전환 권장)
- ✅ 모든 Constraints 준수 (브라우저 충돌 방지, 100ms 반응 시간)

### WCAG 2.1 Level AA 검증
- **2.1.1 Keyboard**: axe-core 자동화 테스트 통과
- **2.1.2 No Keyboard Trap**: Escape 키로 모든 Focus Trap 탈출 가능
- **2.4.3 Focus Order**: 논리적 Tab 순서 유지 확인
- **2.4.7 Focus Visible**: 모든 포커스 상태 2px outline 표시

### 테스트 커버리지
- **단위 테스트**: 키보드 핸들러, 포커스 관리 유틸리티 (Coverage ≥ 90%)
- **통합 테스트**: Zustand 상태와 키보드 이벤트 연동
- **E2E 테스트**: Playwright를 사용한 실제 키보드 시뮬레이션
  - Tab 네비게이션 시나리오
  - Arrow 키 노드 탐색
  - Enter/Space 노드 선택
  - Escape 패널 닫기
  - 단축키 동작 확인

### 성능 기준
- 키보드 이벤트 처리 < 100ms
- 포커스 이동 애니메이션 < 200ms
- 도움말 모달 로드 < 50ms

### 접근성 자동화 테스트
```typescript
// axe-core 통합
import { axe } from 'jest-axe';

test('Taxonomy visualization passes accessibility audit', async () => {
  const { container } = render(<TaxonomyVisualization />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

---

## 리스크 및 완화 전략

### 기술 리스크
1. **React Flow 키보드 이벤트 충돌**
   - **완화**: React Flow의 기본 키보드 핸들러 비활성화, 커스텀 핸들러 우선 적용
2. **Focus Trap 라이브러리 호환성**
   - **완화**: `react-focus-trap` 대신 네이티브 `inert` 속성 사용 고려
3. **브라우저 단축키 충돌**
   - **완화**: `preventDefault()` 신중하게 사용, 브라우저 기본 동작 존중

### 사용자 경험 리스크
1. **키보드 단축키 학습 곡선**
   - **완화**: `?` 키로 언제든 도움말 접근, 툴팁으로 힌트 제공
2. **대규모 트리에서 Arrow 키 탐색 어려움**
   - **완화**: `Home` 키로 처음으로 이동, 검색 필터 활용 안내

### 접근성 리스크
1. **WCAG 자동화 테스트 한계**
   - **완화**: 수동 테스트 병행, 실제 키보드 사용자 피드백 수집
2. **색맹 사용자를 위한 포커스 인디케이터**
   - **완화**: 색상 외에 테두리 두께, 그림자로 추가 시각적 단서 제공

---

## 참고 자료
- [WCAG 2.1 Keyboard Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/keyboard)
- [React Focus Trap](https://github.com/focus-trap/focus-trap-react)
- [react-hotkeys-hook Documentation](https://react-hotkeys-hook.vercel.app/)
- [axe-core Accessibility Testing](https://github.com/dequelabs/axe-core)
- [React Flow Keyboard Accessibility](https://reactflow.dev/learn/accessibility)
