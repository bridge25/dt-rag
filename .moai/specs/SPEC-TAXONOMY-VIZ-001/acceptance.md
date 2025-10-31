# SPEC-TAXONOMY-VIZ-001 인수 기준

## @TEST:TAXONOMY-VIZ-001

---

## 개요

본 문서는 **SPEC-TAXONOMY-VIZ-001: Dynamic Taxonomy 시각화 with React Flow**의 인수 기준을 정의합니다. 모든 시나리오는 Given-When-Then 형식으로 작성되며, 자동화된 테스트로 검증 가능해야 합니다.

---

## 기능 인수 기준

### 1. Taxonomy 트리 초기 렌더링

#### 시나리오 1.1: 정상적인 Taxonomy 데이터 로드
**Given**: 백엔드 API `/api/taxonomy/tree`가 정상적으로 응답하고,
**When**: 사용자가 Taxonomy 시각화 페이지에 접속하면,
**Then**:
- Taxonomy 트리가 노드-엣지 그래프로 표시되어야 한다
- 각 노드는 분류명, 레벨, 문서 개수를 표시해야 한다
- 루트 노드가 캔버스 중앙에 위치해야 한다
- 로딩 스피너가 사라지고 캔버스가 나타나야 한다

**검증 방법**:
```typescript
test('should render taxonomy tree on load', async () => {
  render(<TaxonomyVisualization />);

  await waitFor(() => {
    expect(screen.getByText('Computer Science')).toBeInTheDocument();
    expect(screen.getByText('Level: 0')).toBeInTheDocument();
    expect(screen.getByText('Documents: 42')).toBeInTheDocument();
  });
});
```

#### 시나리오 1.2: API 로드 실패 시 에러 표시
**Given**: 백엔드 API `/api/taxonomy/tree`가 500 에러를 반환하고,
**When**: 사용자가 페이지에 접속하면,
**Then**:
- 에러 메시지 "Taxonomy 데이터를 불러올 수 없습니다"가 표시되어야 한다
- "재시도" 버튼이 표시되어야 한다
- 스켈레톤 로더가 사라져야 한다

**검증 방법**:
```typescript
test('should show error message on API failure', async () => {
  server.use(
    http.get('/api/taxonomy/tree', () => {
      return HttpResponse.error();
    })
  );

  render(<TaxonomyVisualization />);

  await waitFor(() => {
    expect(screen.getByText(/Taxonomy 데이터를 불러올 수 없습니다/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '재시도' })).toBeInTheDocument();
  });
});
```

---

### 2. 노드 인터랙션

#### 시나리오 2.1: 노드 클릭 시 상세 정보 표시
**Given**: Taxonomy 트리가 렌더링되어 있고,
**When**: 사용자가 "Machine Learning" 노드를 클릭하면,
**Then**:
- 사이드 패널에 "Machine Learning" 상세 정보가 표시되어야 한다
- 노드가 시각적으로 강조되어야 한다 (테두리 색상 변경)
- 상세 패널에는 레이블, 레벨, 문서 개수, 부모 노드가 표시되어야 한다

**검증 방법**:
```typescript
test('should display detail panel on node click', async () => {
  render(<TaxonomyVisualization />);

  const nodeElement = await screen.findByText('Machine Learning');
  fireEvent.click(nodeElement);

  await waitFor(() => {
    expect(screen.getByTestId('detail-panel')).toBeInTheDocument();
    expect(screen.getByText('Machine Learning')).toBeInTheDocument();
    expect(screen.getByText('Level: 2')).toBeInTheDocument();
  });
});
```

#### 시나리오 2.2: 노드 확장/축소 토글
**Given**: "Computer Science" 노드가 자식 노드를 가지고 있고,
**When**: 사용자가 노드의 확장 버튼을 클릭하면,
**Then**:
- 자식 노드가 표시되거나 숨겨져야 한다
- 버튼 아이콘이 "-" (축소) 또는 "+" (확장)로 변경되어야 한다
- 레이아웃이 자동으로 재조정되어야 한다

**검증 방법**:
```typescript
test('should toggle node expansion', async () => {
  render(<TaxonomyVisualization />);

  const expandButton = await screen.findByTestId('expand-button-cs-001');
  fireEvent.click(expandButton);

  await waitFor(() => {
    expect(screen.getByText('Machine Learning')).toBeInTheDocument();
  });

  fireEvent.click(expandButton);

  await waitFor(() => {
    expect(screen.queryByText('Machine Learning')).not.toBeInTheDocument();
  });
});
```

---

### 3. 줌 및 팬 컨트롤

#### 시나리오 3.1: 줌 인/아웃 기능
**Given**: Taxonomy 트리가 렌더링되어 있고,
**When**: 사용자가 마우스 휠을 위로 스크롤하면,
**Then**:
- 캔버스가 확대되어야 한다 (줌 인)
- 노드 크기와 간격이 비례적으로 증가해야 한다

**When**: 사용자가 마우스 휠을 아래로 스크롤하면,
**Then**:
- 캔버스가 축소되어야 한다 (줌 아웃)

**검증 방법**:
```typescript
test('should zoom in/out on mouse wheel', async () => {
  render(<TaxonomyVisualization />);

  const canvas = await screen.findByTestId('flow-canvas');

  fireEvent.wheel(canvas, { deltaY: -100 }); // Zoom in
  await waitFor(() => {
    expect(canvas).toHaveStyle('transform: scale(1.2)');
  });

  fireEvent.wheel(canvas, { deltaY: 100 }); // Zoom out
  await waitFor(() => {
    expect(canvas).toHaveStyle('transform: scale(1.0)');
  });
});
```

#### 시나리오 3.2: 드래그로 캔버스 이동
**Given**: Taxonomy 트리가 렌더링되어 있고,
**When**: 사용자가 캔버스를 드래그하면,
**Then**:
- 캔버스가 드래그 방향으로 이동해야 한다
- 마우스 커서가 "grab" 아이콘으로 변경되어야 한다

**검증 방법**:
```typescript
test('should pan canvas on drag', async () => {
  render(<TaxonomyVisualization />);

  const canvas = await screen.findByTestId('flow-canvas');

  fireEvent.mouseDown(canvas, { clientX: 0, clientY: 0 });
  fireEvent.mouseMove(canvas, { clientX: 100, clientY: 100 });
  fireEvent.mouseUp(canvas);

  await waitFor(() => {
    expect(canvas).toHaveStyle('transform: translate(100px, 100px)');
  });
});
```

---

### 4. 미니맵 및 검색 필터

#### 시나리오 4.1: 미니맵 표시
**Given**: Taxonomy 트리가 렌더링되어 있고,
**When**: 사용자가 페이지에 접속하면,
**Then**:
- 캔버스 우측 하단에 미니맵이 표시되어야 한다
- 미니맵에는 전체 Taxonomy 구조가 축소되어 표시되어야 한다
- 현재 뷰포트 영역이 하이라이트되어야 한다

**검증 방법**:
```typescript
test('should display minimap', async () => {
  render(<TaxonomyVisualization />);

  await waitFor(() => {
    expect(screen.getByTestId('minimap')).toBeInTheDocument();
    expect(screen.getByTestId('minimap-viewport')).toBeInTheDocument();
  });
});
```

#### 시나리오 4.2: 검색 필터로 노드 하이라이트
**Given**: Taxonomy 트리가 렌더링되어 있고,
**When**: 사용자가 검색 입력창에 "machine"을 입력하면,
**Then**:
- "Machine Learning" 노드가 하이라이트되어야 한다
- 다른 노드는 투명도가 낮아져야 한다 (opacity: 0.3)
- 매칭된 노드 개수가 표시되어야 한다 ("1 results found")

**검증 방법**:
```typescript
test('should highlight nodes on search', async () => {
  render(<TaxonomyVisualization />);

  const searchInput = await screen.findByPlaceholderText('Search nodes...');
  fireEvent.change(searchInput, { target: { value: 'machine' } });

  await waitFor(() => {
    const mlNode = screen.getByText('Machine Learning');
    expect(mlNode).toHaveClass('highlighted');
    expect(screen.getByText('1 results found')).toBeInTheDocument();
  });
});
```

---

### 5. 레이아웃 전환 (선택 기능)

#### 시나리오 5.1: 트리 레이아웃 → 방사형 레이아웃 전환
**Given**: 현재 레이아웃이 트리 레이아웃이고,
**When**: 사용자가 "Radial Layout" 버튼을 클릭하면,
**Then**:
- 노드 배치가 방사형으로 재배치되어야 한다
- 애니메이션 효과가 적용되어야 한다 (500ms transition)
- 버튼 텍스트가 "Tree Layout"으로 변경되어야 한다

**검증 방법**:
```typescript
test('should switch to radial layout', async () => {
  render(<TaxonomyVisualization />);

  const layoutButton = await screen.findByRole('button', { name: 'Radial Layout' });
  fireEvent.click(layoutButton);

  await waitFor(() => {
    expect(screen.getByRole('button', { name: 'Tree Layout' })).toBeInTheDocument();
    // 노드 위치 변경 검증 (특정 노드의 x, y 좌표 확인)
  });
});
```

---

## 비기능 인수 기준

### 성능

#### 시나리오 P1: 초기 렌더링 시간
**Given**: Taxonomy에 100개의 노드가 있고,
**When**: 사용자가 페이지에 접속하면,
**Then**:
- 초기 렌더링이 2초 이내에 완료되어야 한다

**검증 방법**:
- Chrome DevTools Performance 프로파일링
- Lighthouse Performance Score ≥ 90

#### 시나리오 P2: 노드 클릭 반응 시간
**Given**: 노드가 선택되지 않은 상태이고,
**When**: 사용자가 노드를 클릭하면,
**Then**:
- 상세 패널이 100ms 이내에 표시되어야 한다

**검증 방법**:
```typescript
test('should respond to node click within 100ms', async () => {
  const startTime = performance.now();

  render(<TaxonomyVisualization />);
  const nodeElement = await screen.findByText('Machine Learning');
  fireEvent.click(nodeElement);

  await waitFor(() => {
    const endTime = performance.now();
    expect(endTime - startTime).toBeLessThan(100);
    expect(screen.getByTestId('detail-panel')).toBeInTheDocument();
  });
});
```

#### 시나리오 P3: 메모리 사용량
**Given**: Taxonomy에 100개의 노드가 렌더링되어 있고,
**When**: 사용자가 10분 동안 페이지를 사용하면,
**Then**:
- 브라우저 메모리 사용량이 200MB를 초과하지 않아야 한다

**검증 방법**:
- Chrome DevTools Memory Profiler (Heap Snapshot)
- 메모리 누수 없음 (Detached DOM nodes < 10)

---

### 접근성

#### 시나리오 A1: 키보드 네비게이션
**Given**: Taxonomy 트리가 렌더링되어 있고,
**When**: 사용자가 Tab 키를 누르면,
**Then**:
- 포커스가 첫 번째 노드로 이동해야 한다
- 포커스된 노드에 시각적 표시가 있어야 한다 (outline 또는 border)

**When**: 사용자가 Arrow Down 키를 누르면,
**Then**:
- 포커스가 다음 노드로 이동해야 한다

**검증 방법**:
```typescript
test('should support keyboard navigation', async () => {
  render(<TaxonomyVisualization />);

  const firstNode = await screen.findByText('Computer Science');
  firstNode.focus();

  fireEvent.keyDown(firstNode, { key: 'Tab' });
  await waitFor(() => {
    expect(document.activeElement).toHaveTextContent('Machine Learning');
  });
});
```

#### 시나리오 A2: ARIA 레이블 적용
**Given**: Taxonomy 트리가 렌더링되어 있고,
**When**: 스크린 리더가 노드를 읽으면,
**Then**:
- "Computer Science, Level 0, 42 documents" 형식으로 읽혀야 한다

**검증 방법**:
```typescript
test('should have proper ARIA labels', async () => {
  render(<TaxonomyVisualization />);

  const nodeElement = await screen.findByText('Computer Science');
  expect(nodeElement).toHaveAttribute('aria-label', 'Computer Science, Level 0, 42 documents');
});
```

#### 시나리오 A3: 색상 대비 비율
**Given**: 노드와 배경색이 정의되어 있고,
**When**: WCAG 색상 대비 도구로 측정하면,
**Then**:
- 대비 비율이 최소 4.5:1 이상이어야 한다 (AA 등급)

**검증 방법**:
- Chrome Lighthouse Accessibility Score ≥ 90
- axe DevTools로 자동 검증

---

### 보안

#### 시나리오 S1: API 인증 토큰 필수
**Given**: 사용자가 로그인하지 않은 상태이고,
**When**: `/api/taxonomy/tree`를 호출하면,
**Then**:
- 401 Unauthorized 에러가 반환되어야 한다
- "로그인이 필요합니다" 메시지가 표시되어야 한다

**검증 방법**:
```typescript
test('should require authentication', async () => {
  server.use(
    http.get('/api/taxonomy/tree', () => {
      return HttpResponse.json({ error: 'Unauthorized' }, { status: 401 });
    })
  );

  render(<TaxonomyVisualization />);

  await waitFor(() => {
    expect(screen.getByText(/로그인이 필요합니다/)).toBeInTheDocument();
  });
});
```

#### 시나리오 S2: XSS 방지
**Given**: Taxonomy 노드 레이블에 `<script>alert('XSS')</script>`가 포함되어 있고,
**When**: 노드가 렌더링되면,
**Then**:
- 스크립트가 실행되지 않고 텍스트로 표시되어야 한다

**검증 방법**:
```typescript
test('should sanitize node labels', async () => {
  const maliciousData = {
    id: 'malicious',
    label: '<script>alert("XSS")</script>',
    level: 0,
    documentCount: 0,
    children: [],
  };

  render(<TaxonomyNode data={{ taxonomyNode: maliciousData, isExpanded: false }} />);

  expect(screen.getByText('<script>alert("XSS")</script>')).toBeInTheDocument();
  expect(window.alert).not.toHaveBeenCalled();
});
```

---

## 엣지 케이스

### 엣지 케이스 1: 빈 Taxonomy
**Given**: 백엔드 API가 빈 배열 `[]`을 반환하고,
**When**: 사용자가 페이지에 접속하면,
**Then**:
- "Taxonomy가 비어 있습니다" 메시지가 표시되어야 한다
- 캔버스는 비어 있어야 한다

### 엣지 케이스 2: 단일 노드 (자식 없음)
**Given**: Taxonomy에 루트 노드 1개만 있고,
**When**: 렌더링되면,
**Then**:
- 노드가 캔버스 중앙에 표시되어야 한다
- 확장 버튼이 표시되지 않아야 한다

### 엣지 케이스 3: 매우 긴 노드 레이블
**Given**: 노드 레이블이 100자 이상이고,
**When**: 렌더링되면,
**Then**:
- 레이블이 50자까지만 표시되고 "..." 말줄임표가 추가되어야 한다

### 엣지 케이스 4: 500개 이상의 노드
**Given**: Taxonomy에 600개의 노드가 있고,
**When**: 렌더링되면,
**Then**:
- 경고 메시지 "노드 수가 많아 성능이 저하될 수 있습니다"가 표시되어야 한다
- 가상화가 자동으로 활성화되어야 한다

---

## Definition of Done (완료 기준)

### 필수 조건
- ✅ 모든 Ubiquitous, Event-driven, State-driven 요구사항 구현
- ✅ 모든 인수 기준 시나리오 통과 (자동화된 테스트)
- ✅ 테스트 커버리지 ≥ 85%
- ✅ TypeScript 컴파일 에러 0건
- ✅ ESLint 에러 0건
- ✅ 모든 Constraints 준수 (API 타임아웃, 메모리 사용량 등)

### 추가 조건
- ✅ 최소 1개 이상의 Optional Feature 구현 (레이아웃 전환 권장)
- ✅ 성능 기준 충족 (초기 렌더링 < 2초, 노드 클릭 < 100ms)
- ✅ 접근성 기준 충족 (Lighthouse Accessibility ≥ 90)
- ✅ 컴포넌트 사용 가이드 문서 작성 (@DOC:TAXONOMY-VIZ-001)

### 검증 방법
1. **자동화 테스트 실행**:
   ```bash
   npm test -- TaxonomyVisualization
   npm run test:coverage
   ```

2. **성능 측정**:
   ```bash
   npm run build
   npm run preview
   # Chrome DevTools Lighthouse 실행
   ```

3. **수동 검증**:
   - [ ] 노드 클릭 → 상세 정보 표시
   - [ ] 노드 확장/축소 동작
   - [ ] 줌/팬 컨트롤
   - [ ] 검색 필터 하이라이트
   - [ ] 키보드 네비게이션

---

**작성자**: @spec-builder
**작성일**: 2025-10-31
**연관 SPEC**: SPEC-TAXONOMY-VIZ-001
