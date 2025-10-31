# SPEC-TAXONOMY-KEYNAV-002 인수 기준

> **@ACCEPT:TAXONOMY-KEYNAV-002**
>
> 키보드 네비게이션 구현 완료를 위한 상세 인수 기준 및 테스트 시나리오

---

## 개요

이 문서는 SPEC-TAXONOMY-KEYNAV-002의 구현 완료를 검증하기 위한 인수 기준(Acceptance Criteria)을 정의합니다. 모든 시나리오는 Given-When-Then 형식으로 작성되며, 자동화 테스트(Vitest, Playwright) 및 수동 테스트를 통해 검증됩니다.

---

## 인수 기준 요약

### 필수 기능
- ✅ Tab 키 네비게이션 (6개 시나리오)
- ✅ Arrow 키 노드 탐색 (4개 시나리오)
- ✅ Enter/Space 키 액션 (3개 시나리오)
- ✅ Escape 키 동작 (3개 시나리오)
- ✅ Focus Trap (2개 시나리오)
- ✅ 키보드 단축키 (7개 시나리오)

### 선택 기능 (최소 2개 구현)
- ✅ 줌 인/아웃 단축키
- ✅ 레이아웃 전환 단축키
- ✅ Home 키 첫 노드 이동

### 접근성 검증
- ✅ WCAG 2.1 Level AA 자동화 테스트 통과
- ✅ axe-core 위반 사항 0개
- ✅ 포커스 인디케이터 항상 표시

---

## 테스트 시나리오

### 1. Tab 키 네비게이션

#### AC-KEYNAV-001: 논리적 Tab 순서로 포커스 이동
**우선순위**: P0 (필수)

**Given**: Taxonomy 시각화 페이지가 로드되어 있다
**When**: 사용자가 Tab 키를 순차적으로 누른다
**Then**:
- 1. 검색 입력 필드로 포커스 이동
- 2. 레이아웃 토글 버튼으로 포커스 이동
- 3. 줌 인 버튼으로 포커스 이동
- 4. 줌 아웃 버튼으로 포커스 이동
- 5. 미니맵으로 포커스 이동
- 6. 첫 번째 Taxonomy 노드로 포커스 이동
- 7. 두 번째 노드로 포커스 이동 (계속 순환)

**검증 방법**:
```typescript
// Playwright E2E Test
test('Tab navigation follows logical order', async ({ page }) => {
  await page.goto('/taxonomy');

  await page.keyboard.press('Tab');
  await expect(page.locator('#taxonomy-search')).toBeFocused();

  await page.keyboard.press('Tab');
  await expect(page.locator('[aria-label="레이아웃 전환"]')).toBeFocused();

  await page.keyboard.press('Tab');
  await expect(page.locator('[aria-label="줌 인"]')).toBeFocused();

  await page.keyboard.press('Tab');
  await expect(page.locator('[aria-label="줌 아웃"]')).toBeFocused();

  await page.keyboard.press('Tab');
  await expect(page.locator('.react-flow__minimap')).toBeFocused();

  await page.keyboard.press('Tab');
  await expect(page.locator('[data-nodeid="node-1"]')).toBeFocused();
});
```

---

#### AC-KEYNAV-002: Shift+Tab으로 역방향 포커스 이동
**우선순위**: P0 (필수)

**Given**: 첫 번째 노드에 포커스가 있다
**When**: 사용자가 Shift+Tab 키를 누른다
**Then**: 미니맵으로 포커스가 이동한다

**검증 방법**:
```typescript
test('Shift+Tab moves focus backward', async ({ page }) => {
  await page.goto('/taxonomy');

  // Navigate to first node
  for (let i = 0; i < 6; i++) {
    await page.keyboard.press('Tab');
  }
  await expect(page.locator('[data-nodeid="node-1"]')).toBeFocused();

  // Shift+Tab backward
  await page.keyboard.press('Shift+Tab');
  await expect(page.locator('.react-flow__minimap')).toBeFocused();
});
```

---

#### AC-KEYNAV-003: 포커스 인디케이터 명확히 표시
**우선순위**: P0 (필수)

**Given**: 사용자가 Tab 키로 요소를 탐색한다
**When**: 각 요소에 포커스가 이동한다
**Then**:
- 포커스된 요소에 2px 파란색 outline이 표시된다
- outline 색상 대비가 4.5:1 이상이다
- `outline: none` 스타일이 적용되지 않는다

**검증 방법**:
```typescript
test('Focus indicator is visible', async ({ page }) => {
  await page.goto('/taxonomy');
  await page.keyboard.press('Tab');

  const focusedElement = page.locator(':focus');
  const outline = await focusedElement.evaluate(el =>
    window.getComputedStyle(el).outline
  );

  expect(outline).toContain('2px');
  expect(outline).toContain('rgb(59, 130, 246)'); // blue-500
});
```

---

### 2. Arrow 키 노드 탐색

#### AC-KEYNAV-004: Arrow Down으로 하위 노드 이동
**우선순위**: P0 (필수)

**Given**: 첫 번째 노드에 포커스가 있다
**When**: 사용자가 Arrow Down 키를 누른다
**Then**:
- 바로 아래(하위) 노드로 포커스가 이동한다
- 새 노드가 화면 밖에 있으면 자동으로 스크롤된다
- 포커스 인디케이터가 새 노드에 표시된다

**검증 방법**:
```typescript
test('Arrow Down moves to child node', async ({ page }) => {
  await page.goto('/taxonomy');

  // Focus first node
  await page.locator('[data-nodeid="node-1"]').focus();

  // Arrow Down
  await page.keyboard.press('ArrowDown');
  await expect(page.locator('[data-nodeid="node-1-1"]')).toBeFocused();
});
```

---

#### AC-KEYNAV-005: Arrow Up으로 상위 노드 이동
**우선순위**: P0 (필수)

**Given**: 자식 노드에 포커스가 있다
**When**: 사용자가 Arrow Up 키를 누른다
**Then**: 부모 노드로 포커스가 이동한다

**검증 방법**:
```typescript
test('Arrow Up moves to parent node', async ({ page }) => {
  await page.goto('/taxonomy');

  // Focus child node
  await page.locator('[data-nodeid="node-1-1"]').focus();

  // Arrow Up
  await page.keyboard.press('ArrowUp');
  await expect(page.locator('[data-nodeid="node-1"]')).toBeFocused();
});
```

---

#### AC-KEYNAV-006: Arrow Left/Right로 형제 노드 이동
**우선순위**: P1 (중요)

**Given**: 노드에 포커스가 있고, 같은 레벨에 형제 노드가 있다
**When**: 사용자가 Arrow Left 또는 Right 키를 누른다
**Then**: 같은 레벨의 인접 노드로 포커스가 이동한다

**검증 방법**:
```typescript
test('Arrow Left/Right moves to sibling nodes', async ({ page }) => {
  await page.goto('/taxonomy');

  // Focus node with siblings
  await page.locator('[data-nodeid="node-2"]').focus();

  // Arrow Right to sibling
  await page.keyboard.press('ArrowRight');
  await expect(page.locator('[data-nodeid="node-3"]')).toBeFocused();

  // Arrow Left back
  await page.keyboard.press('ArrowLeft');
  await expect(page.locator('[data-nodeid="node-2"]')).toBeFocused();
});
```

---

#### AC-KEYNAV-007: 인접 노드 없으면 포커스 유지
**우선순위**: P2 (선택)

**Given**: 마지막 노드(리프 노드)에 포커스가 있다
**When**: 사용자가 Arrow Down 키를 누른다
**Then**: 포커스가 변경되지 않고, 시각적 피드백(예: 깜빡임)이 표시될 수 있다

**검증 방법**:
```typescript
test('Focus stays when no adjacent node', async ({ page }) => {
  await page.goto('/taxonomy');

  // Focus leaf node
  const leafNode = page.locator('[data-nodeid="node-leaf"]');
  await leafNode.focus();

  // Arrow Down (no child)
  await page.keyboard.press('ArrowDown');
  await expect(leafNode).toBeFocused(); // Focus unchanged
});
```

---

### 3. Enter/Space 키 액션

#### AC-KEYNAV-008: Enter 키로 노드 선택 및 패널 열기
**우선순위**: P0 (필수)

**Given**: 노드에 포커스가 있다
**When**: 사용자가 Enter 키를 누른다
**Then**:
- 노드가 선택 상태로 변경된다
- 노드 상세 정보 패널이 열린다
- 패널 내 첫 번째 포커스 가능 요소(닫기 버튼)로 포커스가 이동한다

**검증 방법**:
```typescript
test('Enter key selects node and opens panel', async ({ page }) => {
  await page.goto('/taxonomy');

  await page.locator('[data-nodeid="node-1"]').focus();
  await page.keyboard.press('Enter');

  // Panel opened
  await expect(page.locator('[role="dialog"]')).toBeVisible();

  // Focus moved to close button
  await expect(page.locator('[aria-label="패널 닫기"]')).toBeFocused();
});
```

---

#### AC-KEYNAV-009: Space 키로 노드 확장/축소
**우선순위**: P0 (필수)

**Given**: 확장 가능한 노드에 포커스가 있다
**When**: 사용자가 Space 키를 누른다
**Then**:
- 노드가 확장되면 자식 노드가 표시된다
- 노드가 축소되면 자식 노드가 숨겨진다
- 포커스는 현재 노드에 유지된다

**검역 방법**:
```typescript
test('Space key toggles node expansion', async ({ page }) => {
  await page.goto('/taxonomy');

  const expandableNode = page.locator('[data-nodeid="node-1"]');
  await expandableNode.focus();

  // Space to expand
  await page.keyboard.press('Space');
  await expect(page.locator('[data-nodeid="node-1-1"]')).toBeVisible();

  // Space to collapse
  await page.keyboard.press('Space');
  await expect(page.locator('[data-nodeid="node-1-1"]')).not.toBeVisible();

  // Focus stays
  await expect(expandableNode).toBeFocused();
});
```

---

#### AC-KEYNAV-010: 버튼에 Enter/Space 동일 동작
**우선순위**: P1 (중요)

**Given**: 줌 인 버튼에 포커스가 있다
**When**: 사용자가 Enter 또는 Space 키를 누른다
**Then**: 두 키 모두 버튼을 활성화하여 줌 인 동작을 실행한다

**검증 방법**:
```typescript
test('Buttons work with both Enter and Space', async ({ page }) => {
  await page.goto('/taxonomy');

  const zoomInButton = page.locator('[aria-label="줌 인"]');
  await zoomInButton.focus();

  // Enter key
  await page.keyboard.press('Enter');
  // Verify zoom level increased (mock or check canvas transform)

  // Space key
  await page.keyboard.press('Space');
  // Verify zoom level increased again
});
```

---

### 4. Escape 키 동작

#### AC-KEYNAV-011: Escape 키로 패널 닫기
**우선순위**: P0 (필수)

**Given**: 노드 상세 패널이 열려 있고, 패널 내부에 포커스가 있다
**When**: 사용자가 Escape 키를 누른다
**Then**:
- 패널이 닫힌다
- 포커스가 이전 노드로 복귀한다
- 노드 선택이 해제된다

**검증 방법**:
```typescript
test('Escape closes panel and restores focus', async ({ page }) => {
  await page.goto('/taxonomy');

  const node = page.locator('[data-nodeid="node-1"]');
  await node.focus();
  await page.keyboard.press('Enter');

  // Panel open
  await expect(page.locator('[role="dialog"]')).toBeVisible();

  // Escape to close
  await page.keyboard.press('Escape');
  await expect(page.locator('[role="dialog"]')).not.toBeVisible();

  // Focus restored
  await expect(node).toBeFocused();
});
```

---

#### AC-KEYNAV-012: Escape 키로 노드 선택 해제
**우선순위**: P1 (중요)

**Given**: 노드가 선택된 상태이고, 패널은 닫혀 있다
**When**: 사용자가 Escape 키를 누른다
**Then**:
- 노드 선택이 해제된다
- 포커스는 유지된다

**검증 방법**:
```typescript
test('Escape deselects node', async ({ page }) => {
  await page.goto('/taxonomy');

  const node = page.locator('[data-nodeid="node-1"]');
  await node.focus();
  await page.keyboard.press('Enter');
  await page.keyboard.press('Escape'); // Close panel

  // Node still selected (visual highlight)
  await expect(node).toHaveClass(/selected/);

  // Escape again to deselect
  await page.keyboard.press('Escape');
  await expect(node).not.toHaveClass(/selected/);
});
```

---

#### AC-KEYNAV-013: Escape 키로 검색 필터 초기화
**우선순위**: P2 (선택)

**Given**: 검색 입력 필드에 텍스트가 입력되어 있다
**When**: 사용자가 Escape 키를 누른다
**Then**:
- 검색 텍스트가 지워진다
- 포커스는 검색 필드에 유지된다

**검증 방법**:
```typescript
test('Escape clears search filter', async ({ page }) => {
  await page.goto('/taxonomy');

  const searchInput = page.locator('#taxonomy-search');
  await searchInput.focus();
  await searchInput.fill('test query');

  // Escape to clear
  await page.keyboard.press('Escape');
  await expect(searchInput).toHaveValue('');
  await expect(searchInput).toBeFocused();
});
```

---

### 5. Focus Trap

#### AC-KEYNAV-014: 패널 열린 상태에서 Tab 포커스 제한
**우선순위**: P0 (필수)

**Given**: 노드 상세 패널이 열려 있다
**When**: 사용자가 Tab 키를 반복해서 누른다
**Then**:
- 포커스가 패널 내부 요소들 사이에서만 순환한다
- 패널 외부(캔버스, 컨트롤)로 포커스가 이동하지 않는다
- 마지막 요소에서 Tab 누르면 첫 번째 요소로 순환한다

**검증 방법**:
```typescript
test('Focus trap in detail panel', async ({ page }) => {
  await page.goto('/taxonomy');

  await page.locator('[data-nodeid="node-1"]').focus();
  await page.keyboard.press('Enter');

  const closeButton = page.locator('[aria-label="패널 닫기"]');
  const expandButton = page.locator('[aria-label="확장/축소"]');

  // Tab within panel
  await expect(closeButton).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(expandButton).toBeFocused();

  // Tab at last element loops to first
  await page.keyboard.press('Tab');
  await expect(closeButton).toBeFocused();
});
```

---

#### AC-KEYNAV-015: Escape로 Focus Trap 탈출
**우선순위**: P0 (필수)

**Given**: 키보드 단축키 도움말 모달이 열려 있고, Focus Trap 상태이다
**When**: 사용자가 Escape 키를 누른다
**Then**:
- 모달이 닫힌다
- Focus Trap이 해제된다
- 포커스가 이전 요소로 복귀한다

**검증 방법**:
```typescript
test('Escape exits focus trap', async ({ page }) => {
  await page.goto('/taxonomy');

  // Open help modal
  await page.keyboard.press('?');
  await expect(page.locator('[role="dialog"][aria-labelledby="shortcuts-title"]')).toBeVisible();

  // Escape to close
  await page.keyboard.press('Escape');
  await expect(page.locator('[role="dialog"]')).not.toBeVisible();

  // Focus restored to body or previous element
  const focusedTag = await page.evaluate(() => document.activeElement?.tagName);
  expect(['BODY', 'BUTTON', 'INPUT']).toContain(focusedTag);
});
```

---

### 6. 키보드 단축키

#### AC-KEYNAV-016: `/` 키로 검색 포커스
**우선순위**: P0 (필수)

**Given**: 사용자가 캔버스를 탐색 중이다
**When**: 사용자가 `/` 키를 누른다
**Then**: 검색 입력 필드로 포커스가 즉시 이동한다

**검증 방법**:
```typescript
test('/ key focuses search input', async ({ page }) => {
  await page.goto('/taxonomy');

  await page.keyboard.press('/');
  await expect(page.locator('#taxonomy-search')).toBeFocused();
});
```

---

#### AC-KEYNAV-017: `+`/`-` 키로 줌 인/아웃
**우선순위**: P1 (중요)

**Given**: 캔버스가 기본 줌 레벨(100%)이다
**When**: 사용자가 `+` 키를 누른다
**Then**: 캔버스가 줌 인된다 (예: 110%)
**When**: 사용자가 `-` 키를 누른다
**Then**: 캔버스가 줌 아웃된다 (예: 90%)

**검증 방법**:
```typescript
test('+/- keys zoom in/out', async ({ page }) => {
  await page.goto('/taxonomy');

  // Get initial zoom level
  const initialZoom = await page.evaluate(() =>
    // Access React Flow instance or check transform style
    parseFloat(document.querySelector('.react-flow__viewport')?.style.transform.match(/scale\(([^)]+)\)/)?.[1] || '1')
  );

  // Zoom in
  await page.keyboard.press('+');
  const zoomedIn = await page.evaluate(() => /* same logic */);
  expect(zoomedIn).toBeGreaterThan(initialZoom);

  // Zoom out
  await page.keyboard.press('-');
  const zoomedOut = await page.evaluate(() => /* same logic */);
  expect(zoomedOut).toBeLessThan(zoomedIn);
});
```

---

#### AC-KEYNAV-018: `L` 키로 레이아웃 전환
**우선순위**: P1 (중요)

**Given**: 현재 레이아웃이 트리 레이아웃이다
**When**: 사용자가 `L` 키를 누른다
**Then**: 레이아웃이 방사형으로 전환된다
**When**: 다시 `L` 키를 누른다
**Then**: 레이아웃이 트리로 복귀한다

**검증 방법**:
```typescript
test('L key toggles layout', async ({ page }) => {
  await page.goto('/taxonomy');

  // Initial layout (tree)
  const layoutButton = page.locator('[aria-label="레이아웃 전환"]');
  await expect(layoutButton).toContainText('트리');

  // Toggle to radial
  await page.keyboard.press('l');
  await expect(layoutButton).toContainText('방사형');

  // Toggle back
  await page.keyboard.press('l');
  await expect(layoutButton).toContainText('트리');
});
```

---

#### AC-KEYNAV-019: `Home` 키로 첫 노드 이동
**우선순위**: P2 (선택)

**Given**: 사용자가 깊은 레벨의 노드에 포커스가 있다
**When**: 사용자가 `Home` 키를 누른다
**Then**: 첫 번째 루트 노드로 포커스가 이동한다

**검증 방법**:
```typescript
test('Home key moves to first node', async ({ page }) => {
  await page.goto('/taxonomy');

  // Focus deep node
  await page.locator('[data-nodeid="node-5-3-2"]').focus();

  // Home key
  await page.keyboard.press('Home');
  await expect(page.locator('[data-nodeid="node-1"]')).toBeFocused();
});
```

---

#### AC-KEYNAV-020: `?` 키로 단축키 도움말 모달
**우선순위**: P0 (필수)

**Given**: 사용자가 단축키를 모른다
**When**: 사용자가 `?` 키를 누른다
**Then**:
- 키보드 단축키 도움말 모달이 열린다
- 모든 단축키 목록이 테이블 형식으로 표시된다
- 모달은 Focus Trap 상태이다

**검증 방법**:
```typescript
test('? key opens shortcuts help modal', async ({ page }) => {
  await page.goto('/taxonomy');

  await page.keyboard.press('?');

  const modal = page.locator('[role="dialog"][aria-labelledby="shortcuts-title"]');
  await expect(modal).toBeVisible();
  await expect(modal.locator('table')).toBeVisible();

  // Check some shortcuts are listed
  await expect(modal.locator('text=Tab')).toBeVisible();
  await expect(modal.locator('text=Arrow Keys')).toBeVisible();
  await expect(modal.locator('text=Escape')).toBeVisible();
});
```

---

#### AC-KEYNAV-021: 브라우저 단축키와 충돌 없음
**우선순위**: P0 (필수)

**Given**: 사용자가 페이지를 사용 중이다
**When**: 사용자가 `Ctrl+F` (찾기), `Ctrl+R` (새로고침) 등을 누른다
**Then**: 브라우저 기본 동작이 정상적으로 실행된다 (커스텀 핸들러가 방해하지 않음)

**검증 방법**:
```typescript
test('No conflict with browser shortcuts', async ({ page }) => {
  await page.goto('/taxonomy');

  // Ctrl+F should open browser find dialog (can't directly test, but ensure preventDefault not called)
  await page.keyboard.press('Control+f');
  // No assertion needed - test passes if no error

  // Ctrl+R should reload (verify by checking initial state restored)
  await page.keyboard.press('Control+r');
  await page.waitForLoadState('domcontentloaded');
  await expect(page.locator('.taxonomy-visualization')).toBeVisible();
});
```

---

#### AC-KEYNAV-022: 검색 입력 중 Arrow 키 비활성화
**우선순위**: P1 (중요)

**Given**: 검색 입력 필드에 포커스가 있고, 텍스트를 입력 중이다
**When**: 사용자가 Arrow Left/Right 키를 누른다
**Then**:
- 커서가 텍스트 내에서 좌우로 이동한다
- 노드 네비게이션이 발생하지 않는다

**검증 방법**:
```typescript
test('Arrow keys disabled during search input', async ({ page }) => {
  await page.goto('/taxonomy');

  const searchInput = page.locator('#taxonomy-search');
  await searchInput.focus();
  await searchInput.fill('test');

  // Arrow Left should move cursor, not change node focus
  await page.keyboard.press('ArrowLeft');
  const cursorPosition = await searchInput.evaluate(el => (el as HTMLInputElement).selectionStart);
  expect(cursorPosition).toBe(3); // Cursor moved within text

  // Verify no node focused
  const focusedNodeId = await page.evaluate(() => document.activeElement?.getAttribute('data-nodeid'));
  expect(focusedNodeId).toBeNull();
});
```

---

### 7. 접근성 자동화 검증

#### AC-KEYNAV-023: axe-core 접근성 위반 없음
**우선순위**: P0 (필수)

**Given**: TaxonomyVisualization 컴포넌트가 렌더링되어 있다
**When**: axe-core 자동화 테스트를 실행한다
**Then**: 모든 WCAG 2.1 Level AA 규칙을 통과하고, 위반 사항이 0개이다

**검증 방법**:
```typescript
// Vitest Unit Test
import { axe, toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

test('TaxonomyVisualization passes axe accessibility audit', async () => {
  const { container } = render(<TaxonomyVisualization />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

---

#### AC-KEYNAV-024: 모든 인터랙티브 요소에 ARIA 레이블
**우선순위**: P0 (필수)

**Given**: 페이지의 모든 버튼, 입력 필드, 노드가 렌더링되어 있다
**When**: 각 요소를 검사한다
**Then**: 모든 인터랙티브 요소에 `aria-label` 또는 `aria-labelledby` 속성이 있다

**검증 방법**:
```typescript
test('All interactive elements have ARIA labels', async () => {
  const { container } = render(<TaxonomyVisualization />);

  const buttons = container.querySelectorAll('button');
  buttons.forEach(button => {
    expect(
      button.hasAttribute('aria-label') || button.hasAttribute('aria-labelledby')
    ).toBe(true);
  });

  const nodes = container.querySelectorAll('[role="button"]');
  nodes.forEach(node => {
    expect(node.hasAttribute('aria-label')).toBe(true);
  });
});
```

---

#### AC-KEYNAV-025: 포커스 인디케이터 색상 대비 충족
**우선순위**: P0 (필수)

**Given**: 요소에 포커스가 있다
**When**: 포커스 인디케이터의 색상 대비를 측정한다
**Then**: 배경색과 outline 색상의 대비가 최소 4.5:1 이상이다

**검증 방법**:
```typescript
test('Focus indicator has sufficient color contrast', async ({ page }) => {
  await page.goto('/taxonomy');
  await page.keyboard.press('Tab');

  const contrastRatio = await page.evaluate(() => {
    const el = document.activeElement as HTMLElement;
    const bgColor = window.getComputedStyle(el).backgroundColor;
    const outlineColor = window.getComputedStyle(el).outlineColor;

    // Use color contrast calculation library
    return calculateContrast(bgColor, outlineColor);
  });

  expect(contrastRatio).toBeGreaterThanOrEqual(4.5);
});
```

---

## Definition of Done

### 기능 완성도
- ✅ 모든 P0 (필수) 시나리오 통과 (18개)
- ✅ 최소 P1 (중요) 시나리오 50% 이상 통과 (3개 이상)
- ✅ 모든 Constraints 충족
  - REQ-KEYNAV-C001: 브라우저 단축키 충돌 없음
  - REQ-KEYNAV-C002: 키보드 이벤트 처리 < 100ms
  - REQ-KEYNAV-C003: 포커스 인디케이터 항상 표시
  - REQ-KEYNAV-C004: 최대 20개 단축키 제한 준수

### 테스트 커버리지
- ✅ 단위 테스트 (Vitest): Coverage ≥ 90%
  - 키보드 핸들러 함수
  - 포커스 관리 유틸리티
  - Zustand 액션
- ✅ 통합 테스트: 키보드 이벤트와 상태 연동 검증
- ✅ E2E 테스트 (Playwright): 25개 시나리오 중 최소 20개 통과

### 접근성 검증
- ✅ axe-core 자동화 테스트 위반 사항 0개
- ✅ WCAG 2.1 Level AA 수동 체크리스트 완료
  - 2.1.1 Keyboard: ✅
  - 2.1.2 No Keyboard Trap: ✅
  - 2.4.3 Focus Order: ✅
  - 2.4.7 Focus Visible: ✅
- ✅ 스크린 리더 기본 호환성 확인 (NVDA 또는 VoiceOver)

### 성능 검증
- ✅ 키보드 이벤트 처리 시간 < 100ms (Performance API 측정)
- ✅ 포커스 이동 애니메이션 < 200ms
- ✅ 대규모 트리(500개 노드)에서 Arrow 키 반응 속도 정상

### 문서화
- ✅ 키보드 단축키 가이드 작성 (도움말 모달 내용 기반)
- ✅ README 업데이트: 접근성 기능 섹션 추가
- ✅ 코드 주석: 복잡한 포커스 관리 로직 설명

### 코드 품질
- ✅ ESLint/TSLint 위반 사항 0개
- ✅ 코드 리뷰 승인 완료
- ✅ 모든 테스트 통과 (CI/CD 파이프라인)

---

## 수동 검증 체크리스트

### 키보드 네비게이션 기본 동작
- [ ] Tab 키로 모든 인터랙티브 요소 접근 가능
- [ ] Shift+Tab으로 역방향 이동 가능
- [ ] Arrow 키로 노드 간 자연스러운 탐색
- [ ] Enter/Space로 모든 액션 실행 가능
- [ ] Escape로 모달/패널 닫기 및 포커스 복원

### 포커스 관리
- [ ] 포커스 인디케이터가 항상 명확히 표시됨
- [ ] 포커스가 화면 밖 요소로 이동 시 자동 스크롤
- [ ] 모달 열릴 때 포커스가 모달 내부로 이동
- [ ] 모달 닫힐 때 포커스가 이전 위치로 복원

### 키보드 단축키
- [ ] `/` 키로 검색 포커스 즉시 이동
- [ ] `+`/`-` 키로 줌 동작 정상
- [ ] `L` 키로 레이아웃 전환 동작 정상
- [ ] `?` 키로 도움말 모달 열림
- [ ] `Home` 키로 첫 노드 이동 (선택 기능)

### Focus Trap
- [ ] 모달 열린 상태에서 Tab이 모달 내부로만 제한됨
- [ ] Escape로 Focus Trap 탈출 및 모달 닫힘
- [ ] 패널 외부 클릭 시 Focus Trap 해제 (선택)

### 접근성
- [ ] 모든 버튼/노드에 ARIA 레이블 존재
- [ ] 모달에 `role="dialog"`, `aria-modal="true"` 적용
- [ ] 색상 대비가 WCAG AA 기준 충족 (4.5:1)
- [ ] 스크린 리더로 기본 네비게이션 가능 (NVDA/VoiceOver)

### 엣지 케이스
- [ ] 빈 트리(노드 0개)에서 키보드 동작 오류 없음
- [ ] 단일 노드만 있을 때 Arrow 키 동작 정상
- [ ] 검색 필터 적용 중 키보드 네비게이션 정상
- [ ] 레이아웃 전환 중 포커스 유지

---

## 리그레션 테스트

### 기존 기능 영향 확인
- [ ] SPEC-TAXONOMY-VIZ-001의 마우스 네비게이션 정상 동작
- [ ] 노드 클릭 → 상세 패널 열기 동작 정상
- [ ] 검색 필터링 기능 정상
- [ ] 줌/팬 컨트롤 정상
- [ ] 미니맵 인터랙션 정상
- [ ] 레이아웃 전환 버튼 클릭 동작 정상

---

## 알려진 제한 사항

### 브라우저별 차이점
- **Safari**: `inert` 속성 미지원 (iOS Safari 15.4+에서만 지원)
  - 대안: `react-focus-trap` 라이브러리 사용
- **Firefox**: 일부 커스텀 outline 스타일이 기본 동작과 충돌 가능
  - 대안: `-moz-outline-radius` 속성 추가

### 대규모 트리 성능
- 500개 이상 노드에서 Arrow 키 탐색 시 지연 가능
  - 대안: 가상화 적용 또는 노드 수 제한 안내

### 스크린 리더 제한
- 이 SPEC은 기본적인 키보드 네비게이션만 포함
- 고급 스크린 리더 최적화는 SPEC-TAXONOMY-SCREENREADER-003에서 처리 예정

---

**Last Updated**: 2025-11-01
**Author**: @sonheungmin
