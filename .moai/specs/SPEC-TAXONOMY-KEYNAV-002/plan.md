# SPEC-TAXONOMY-KEYNAV-002 구현 계획

> **@PLAN:TAXONOMY-KEYNAV-002**
>
> SPEC-TAXONOMY-VIZ-001에 완전한 키보드 네비게이션 구현

---

## 개요

### 목표
마우스 없이 키보드만으로 Taxonomy 시각화의 모든 기능을 사용할 수 있도록 접근성을 개선하고, WCAG 2.1 Level AA 기준을 충족한다.

### 범위
- Tab/Arrow/Enter/Space/Escape 키 네비게이션
- 키보드 단축키 시스템
- Focus Trap (모달/패널)
- 포커스 인디케이터 스타일링
- 접근성 자동화 테스트

---

## 구현 우선순위

### 1차 목표 (핵심 기능)
**목표**: 모든 Ubiquitous 및 Event-driven 요구사항 구현

1. **포커스 관리 시스템 구축**
   - Zustand 상태 확장 (`focusedNodeId`, `focusHistory`, `keyboardMode`)
   - 포커스 이동 유틸리티 함수 (`setFocusedNode`, `pushFocusHistory`, `popFocusHistory`)

2. **Tab 키 네비게이션**
   - 논리적 Tab 순서 설정 (검색 → 컨트롤 → 노드 → 패널)
   - `tabIndex` 속성 자동 관리
   - `focus-visible` CSS 스타일 적용

3. **Arrow 키 노드 탐색**
   - 인접 노드 찾기 알고리즘 구현
   - 상/하/좌/우 방향 네비게이션
   - 화면 밖 노드 자동 스크롤

4. **Enter/Space 키 액션**
   - 노드 선택 핸들러
   - 상세 패널 열기
   - 확장/축소 토글

5. **Escape 키 동작**
   - 패널 닫기
   - 포커스 히스토리 복원
   - 선택 해제

**완료 기준**:
- 모든 인터랙티브 요소에 키보드 접근 가능
- REQ-KEYNAV-U001 ~ REQ-KEYNAV-U004 충족
- REQ-KEYNAV-E001 ~ REQ-KEYNAV-E006 충족

---

### 2차 목표 (상태 관리 및 Focus Trap)
**목표**: State-driven 요구사항 및 포커스 제한 구현

1. **Focus Trap 구현**
   - `react-focus-trap` 라이브러리 통합
   - 상세 패널에 Focus Trap 적용
   - 키보드 단축키 도움말 모달에 Focus Trap 적용

2. **자동 스크롤 로직**
   - 포커스된 노드를 viewport 중앙으로 이동
   - React Flow `fitView()` API 활용

3. **키보드 모드 전환**
   - `navigation` 모드: Arrow 키로 노드 탐색
   - `search` 모드: 검색 입력 중 Arrow 키 비활성화
   - `panel` 모드: 패널 내부 포커스 제한

**완료 기준**:
- REQ-KEYNAV-S001 ~ REQ-KEYNAV-S003 충족
- 패널 열릴 때 포커스 트랩 동작
- Escape 키로 트랩 탈출 가능

---

### 3차 목표 (키보드 단축키 시스템)
**목표**: Optional Features 및 사용자 편의성 향상

1. **전역 단축키 구현**
   - `/`: 검색 포커스
   - `+`/`-`: 줌 인/아웃
   - `L`: 레이아웃 전환
   - `Home`: 첫 노드로 이동
   - `?`: 도움말 모달

2. **react-hotkeys-hook 통합**
   - 단축키 충돌 방지 로직
   - `enableOnFormTags: false` 설정 (입력 필드 제외)

3. **키보드 단축키 도움말 모달**
   - 단축키 목록 테이블
   - `?` 키 또는 버튼으로 열기
   - Focus Trap 적용

**완료 기준**:
- REQ-KEYNAV-O001 ~ REQ-KEYNAV-O003 충족
- 최소 2개 이상의 Optional Features 구현
- 도움말 모달로 사용자 학습 지원

---

### 4차 목표 (접근성 검증 및 최적화)
**목표**: WCAG 2.1 Level AA 준수 확인

1. **포커스 인디케이터 스타일링**
   - 2px 파란색 outline (색상 대비 4.5:1 이상)
   - `outline: none` 사용 금지
   - Tailwind CSS `:focus-visible` 커스텀 스타일

2. **ARIA 속성 보완**
   - `role="button"` (노드)
   - `aria-label` (모든 인터랙티브 요소)
   - `aria-modal="true"` (모달/패널)

3. **접근성 자동화 테스트**
   - axe-core 통합
   - Vitest 단위 테스트에서 접근성 규칙 검증
   - WCAG 2.1.1, 2.1.2, 2.4.3, 2.4.7 자동 체크

**완료 기준**:
- axe-core 테스트 통과 (위반 사항 0개)
- 모든 Constraints 충족 (REQ-KEYNAV-C001 ~ C004)
- 포커스 인디케이터 항상 표시

---

## 기술 접근 방식

### 아키텍처 설계

#### 1. Zustand 상태 확장
```typescript
// stores/useTaxonomyStore.ts
interface TaxonomyState {
  // 기존 필드
  nodes: FlowNode[];
  edges: Edge[];
  selectedNodeId: string | null;
  layout: 'tree' | 'radial';

  // 새로 추가
  focusedNodeId: string | null;
  focusHistory: string[];
  keyboardMode: 'navigation' | 'search' | 'panel';

  // 액션
  setFocusedNode: (id: string | null) => void;
  pushFocusHistory: (id: string) => void;
  popFocusHistory: () => string | null;
  setKeyboardMode: (mode: 'navigation' | 'search' | 'panel') => void;
}
```

#### 2. 컴포넌트 구조
```
TaxonomyVisualization
├─ useKeyboardShortcuts() // 전역 단축키
├─ TaxonomyFlowCanvas
│  ├─ TaxonomyNode (키보드 핸들러)
│  └─ useFocusNavigation() // Arrow 키 로직
├─ TaxonomyDetailPanel (Focus Trap)
├─ KeyboardShortcutsModal (도움말)
└─ FocusIndicator (시각적 피드백)
```

#### 3. 커스텀 훅
```typescript
// hooks/useKeyboardNavigation.ts
export function useKeyboardNavigation() {
  const { focusedNodeId, setFocusedNode, nodes, edges } = useTaxonomyStore();

  const moveFocus = (direction: 'up' | 'down' | 'left' | 'right') => {
    if (!focusedNodeId) return;
    const nextNodeId = findAdjacentNode(focusedNodeId, direction, nodes, edges);
    if (nextNodeId) {
      setFocusedNode(nextNodeId);
      scrollNodeIntoView(nextNodeId);
    }
  };

  return { moveFocus };
}

// hooks/useFocusTrap.ts
export function useFocusTrap(isActive: boolean) {
  const previousFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isActive) {
      previousFocus.current = document.activeElement as HTMLElement;
    } else {
      previousFocus.current?.focus();
    }
  }, [isActive]);
}
```

---

## 구현 단계별 체크리스트

### Phase 1: 포커스 관리 시스템
- [ ] Zustand 상태에 `focusedNodeId`, `focusHistory`, `keyboardMode` 추가
- [ ] `setFocusedNode`, `pushFocusHistory`, `popFocusHistory` 액션 구현
- [ ] 모든 인터랙티브 요소에 `tabIndex` 설정
- [ ] 포커스 인디케이터 CSS 스타일 적용 (`:focus-visible`)

### Phase 2: 키보드 이벤트 핸들러
- [ ] TaxonomyNode에 `onKeyDown` 핸들러 추가
  - [ ] Enter/Space: 노드 선택
  - [ ] Arrow Keys: 인접 노드 탐색
  - [ ] Escape: 선택 해제
- [ ] `findAdjacentNode()` 유틸리티 함수 구현
- [ ] `scrollNodeIntoView()` 자동 스크롤 로직 구현

### Phase 3: Focus Trap
- [ ] `react-focus-trap` 라이브러리 설치
- [ ] TaxonomyDetailPanel에 Focus Trap 적용
- [ ] Escape 키로 트랩 탈출 및 포커스 복원
- [ ] KeyboardShortcutsModal에 Focus Trap 적용

### Phase 4: 전역 단축키
- [ ] `react-hotkeys-hook` 라이브러리 설치
- [ ] 단축키 등록:
  - [ ] `/`: 검색 포커스
  - [ ] `+`/`-`: 줌 인/아웃
  - [ ] `L`: 레이아웃 전환
  - [ ] `Home`: 첫 노드로 이동
  - [ ] `?`: 도움말 모달
- [ ] 브라우저 기본 단축키 충돌 방지 로직

### Phase 5: 접근성 검증
- [ ] axe-core 설치 및 Vitest 통합
- [ ] 모든 컴포넌트에 ARIA 속성 추가
  - [ ] `role="button"` (노드)
  - [ ] `aria-label` (버튼, 입력 필드)
  - [ ] `aria-modal="true"` (모달)
- [ ] WCAG 2.1 자동화 테스트 작성
- [ ] 수동 키보드 네비게이션 테스트

### Phase 6: E2E 테스트
- [ ] Playwright 테스트 작성:
  - [ ] Tab 네비게이션 시나리오
  - [ ] Arrow 키 노드 탐색
  - [ ] Enter/Space 노드 선택
  - [ ] Escape 패널 닫기
  - [ ] 단축키 동작 확인
- [ ] 모든 시나리오 통과 확인

---

## 리스크 관리

### 기술 리스크

#### 1. React Flow 키보드 이벤트 충돌
**영향도**: 높음
**발생 가능성**: 중간
**완화 전략**:
- React Flow의 기본 키보드 핸들러 비활성화 옵션 확인
- 커스텀 핸들러를 우선 적용하여 이벤트 전파 차단 (`e.stopPropagation()`)
- React Flow 공식 문서의 접근성 가이드 참조

#### 2. Focus Trap 라이브러리 호환성
**영향도**: 중간
**발생 가능성**: 낮음
**완화 전략**:
- `react-focus-trap` 대신 네이티브 `inert` 속성 사용 고려
- 브라우저 호환성 확인 (Chrome 102+, Firefox 112+ 지원)
- Polyfill 추가 (`wicg-inert`)

#### 3. 대규모 트리에서 성능 저하
**영향도**: 중간
**발생 가능성**: 중간
**완화 전략**:
- `findAdjacentNode()` 알고리즘 최적화 (O(n) → O(log n) via spatial indexing)
- 키보드 이벤트 디바운싱 (100ms)
- 가상화된 노드에서는 Arrow 키 동작 제한

---

### 일정 리스크

#### 1. axe-core 통합 시간 예측 불가
**영향도**: 낮음
**발생 가능성**: 중간
**완화 전략**:
- axe-core 공식 예제를 먼저 테스트하여 통합 가능성 확인
- Vitest 환경에서 초기 POC 완료 후 본격 통합

#### 2. 키보드 단축키 학습 곡선
**영향도**: 낮음
**발생 가능성**: 높음
**완화 전략**:
- `?` 키로 도움말 모달을 언제든 접근 가능하도록 구현
- 주요 버튼에 툴팁으로 단축키 힌트 표시

---

## 테스트 전략

### 단위 테스트 (Vitest)
```typescript
// __tests__/useKeyboardNavigation.test.tsx
describe('useKeyboardNavigation', () => {
  test('Arrow Up moves focus to parent node', () => {
    const { result } = renderHook(() => useKeyboardNavigation());
    act(() => {
      useTaxonomyStore.getState().setFocusedNode('node-2');
      result.current.moveFocus('up');
    });
    expect(useTaxonomyStore.getState().focusedNodeId).toBe('node-1');
  });
});

// __tests__/accessibility.test.tsx
import { axe } from 'jest-axe';

test('TaxonomyVisualization has no accessibility violations', async () => {
  const { container } = render(<TaxonomyVisualization />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### 통합 테스트
```typescript
// __tests__/integration/keyboard-flow.test.tsx
test('Tab → Arrow → Enter flow', async () => {
  render(<TaxonomyVisualization />);

  // Tab to first node
  userEvent.tab();
  expect(document.activeElement).toHaveAttribute('data-nodeid', 'node-1');

  // Arrow Down to next node
  await userEvent.keyboard('{ArrowDown}');
  expect(document.activeElement).toHaveAttribute('data-nodeid', 'node-2');

  // Enter to select
  await userEvent.keyboard('{Enter}');
  expect(screen.getByRole('dialog')).toBeInTheDocument();
});
```

### E2E 테스트 (Playwright)
```typescript
// e2e/keyboard-navigation.spec.ts
test('Keyboard navigation workflow', async ({ page }) => {
  await page.goto('/taxonomy');

  // Tab navigation
  await page.keyboard.press('Tab');
  await expect(page.locator('[data-nodeid="node-1"]')).toBeFocused();

  // Arrow key navigation
  await page.keyboard.press('ArrowDown');
  await expect(page.locator('[data-nodeid="node-2"]')).toBeFocused();

  // Enter to open panel
  await page.keyboard.press('Enter');
  await expect(page.locator('role=dialog')).toBeVisible();

  // Escape to close
  await page.keyboard.press('Escape');
  await expect(page.locator('role=dialog')).not.toBeVisible();
});
```

---

## 의존성 및 관계

### 의존 SPEC
- **SPEC-TAXONOMY-VIZ-001** (v1.0.0): 모든 UI 컴포넌트 구현 완료 필요

### 후속 SPEC (예정)
- **SPEC-TAXONOMY-SCREENREADER-003**: 스크린 리더 최적화 (ARIA live regions, 음성 안내)
- **SPEC-MOBILE-ACCESSIBLE-004**: 모바일 접근성 (터치 제스처, 음성 입력)

### 관련 문서
- `.moai/specs/SPEC-TAXONOMY-VIZ-001/spec.md`: 시각화 기본 구조
- `.moai/specs/SPEC-TAXONOMY-VIZ-001/acceptance.md`: 기존 테스트 시나리오

---

## 품질 게이트

### Definition of Done
- ✅ 모든 Ubiquitous, Event-driven, State-driven 요구사항 구현
- ✅ 최소 2개 이상의 Optional Features 구현
- ✅ 모든 Constraints 준수
- ✅ WCAG 2.1 Level AA 자동화 테스트 통과 (axe-core)
- ✅ Playwright E2E 테스트 6개 시나리오 통과
- ✅ 단위 테스트 커버리지 ≥ 90%
- ✅ 키보드 이벤트 처리 < 100ms
- ✅ 코드 리뷰 완료
- ✅ 문서 업데이트 (키보드 단축키 가이드)

### 검증 체크리스트
- [ ] 모든 인터랙티브 요소에 키보드 접근 가능
- [ ] Tab 순서가 논리적 흐름 유지
- [ ] Arrow 키로 모든 노드 탐색 가능
- [ ] Enter/Space로 노드 선택 및 패널 열기
- [ ] Escape로 패널 닫기 및 포커스 복원
- [ ] Focus Trap에서 Escape로 탈출 가능
- [ ] 포커스 인디케이터가 항상 표시됨 (outline 제거 금지)
- [ ] 키보드 단축키 도움말 모달 접근 가능 (`?` 키)
- [ ] axe-core 위반 사항 0개
- [ ] 브라우저 기본 단축키와 충돌 없음

---

## 참고 자료 및 도구

### 라이브러리
- [react-focus-trap](https://github.com/focus-trap/focus-trap-react) - Focus Trap 구현
- [react-hotkeys-hook](https://react-hotkeys-hook.vercel.app/) - 키보드 단축키 관리
- [axe-core](https://github.com/dequelabs/axe-core) - 접근성 자동화 테스트
- [jest-axe](https://github.com/nickcolley/jest-axe) - Vitest 통합

### WCAG 가이드라인
- [2.1.1 Keyboard](https://www.w3.org/WAI/WCAG21/Understanding/keyboard)
- [2.1.2 No Keyboard Trap](https://www.w3.org/WAI/WCAG21/Understanding/no-keyboard-trap)
- [2.4.3 Focus Order](https://www.w3.org/WAI/WCAG21/Understanding/focus-order)
- [2.4.7 Focus Visible](https://www.w3.org/WAI/WCAG21/Understanding/focus-visible)

### React Flow 문서
- [React Flow Accessibility](https://reactflow.dev/learn/accessibility) - 공식 접근성 가이드

### 개발 도구
- Chrome DevTools Accessibility Inspector
- Firefox Accessibility Inspector
- WAVE Browser Extension
- Lighthouse Accessibility Audit

---

**Last Updated**: 2025-11-01
**Author**: @sonheungmin
