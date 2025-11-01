# SPEC-AGENT-CREATE-FORM-001 인수 기준

## @TEST:AGENT-CREATE-FORM-001

---

## 기능 인수 기준

### 1. 폼 단계 네비게이션

#### 시나리오 1.1: Step 1 → Step 2 이동
**Given**: 사용자가 Step 1에서 유효한 Agent 이름 "Research Bot"을 입력하고,
**When**: "다음" 버튼을 클릭하면,
**Then**:
- Step 2 (Taxonomy 선택)로 이동해야 한다
- Step 1 데이터가 유지되어야 한다

**검증**:
```typescript
test('should navigate to step 2 with valid input', async () => {
  render(<AgentCreationForm />);

  const nameInput = screen.getByLabelText('Agent 이름');
  fireEvent.change(nameInput, { target: { value: 'Research Bot' } });

  const nextButton = screen.getByRole('button', { name: '다음' });
  fireEvent.click(nextButton);

  await waitFor(() => {
    expect(screen.getByText('Taxonomy 선택')).toBeInTheDocument();
  });
});
```

#### 시나리오 1.2: 검증 실패 시 이동 차단
**Given**: Agent 이름이 2자 (최소 3자 미만)이고,
**When**: "다음" 버튼을 클릭하면,
**Then**:
- Step 1에 머물러야 한다
- "이름은 최소 3자 이상이어야 합니다" 에러 메시지가 표시되어야 한다

**검증**:
```typescript
test('should block navigation with invalid input', async () => {
  render(<AgentCreationForm />);

  const nameInput = screen.getByLabelText('Agent 이름');
  fireEvent.change(nameInput, { target: { value: 'AB' } });

  const nextButton = screen.getByRole('button', { name: '다음' });
  fireEvent.click(nextButton);

  await waitFor(() => {
    expect(screen.getByText(/최소 3자 이상/)).toBeInTheDocument();
  });
});
```

---

### 2. Taxonomy 선택

#### 시나리오 2.1: 단일 Taxonomy 선택
**Given**: Taxonomy 목록이 렌더링되어 있고,
**When**: "Computer Science" 체크박스를 선택하면,
**Then**:
- 체크박스가 체크되어야 한다
- 선택된 Taxonomy 카운트가 "1개 선택됨"으로 표시되어야 한다

**검증**:
```typescript
test('should select taxonomy', async () => {
  render(<AgentCreationForm />);

  // Navigate to Step 2
  await navigateToStep(2);

  const checkbox = screen.getByLabelText('Computer Science');
  fireEvent.click(checkbox);

  expect(checkbox).toBeChecked();
  expect(screen.getByText('1개 선택됨')).toBeInTheDocument();
});
```

---

### 3. Agent 생성 제출

#### 시나리오 3.1: 성공적인 Agent 생성
**Given**: 모든 필수 필드가 채워져 있고,
**When**: "Agent 생성" 버튼을 클릭하면,
**Then**:
- POST /api/agents가 호출되어야 한다
- 성공 메시지 "Agent가 생성되었습니다"가 표시되어야 한다
- Agent 상세 페이지로 리디렉션되어야 한다

**검증**:
```typescript
test('should create agent successfully', async () => {
  render(<AgentCreationForm />);

  // Fill all steps
  await fillStep1({ name: 'Research Bot' });
  await fillStep2({ taxonomyIds: ['cs-001'] });
  await fillStep3({ promptTemplate: 'research' });

  const submitButton = screen.getByRole('button', { name: 'Agent 생성' });
  fireEvent.click(submitButton);

  await waitFor(() => {
    expect(screen.getByText(/Agent가 생성되었습니다/)).toBeInTheDocument();
  });
});
```

#### 시나리오 3.2: API 에러 처리
**Given**: 백엔드 API가 500 에러를 반환하고,
**When**: "Agent 생성" 버튼을 클릭하면,
**Then**:
- 에러 메시지 "Agent 생성에 실패했습니다"가 표시되어야 한다
- 폼 데이터가 유지되어야 한다

---

### 4. 로컬 스토리지 임시 저장 (선택 기능)

#### 시나리오 4.1: 폼 데이터 자동 저장
**Given**: 사용자가 Agent 이름을 입력하고,
**When**: 다른 필드로 포커스가 이동하면,
**Then**:
- 로컬 스토리지에 폼 데이터가 저장되어야 한다

**검증**:
```typescript
test('should auto-save form data to localStorage', async () => {
  render(<AgentCreationForm />);

  const nameInput = screen.getByLabelText('Agent 이름');
  fireEvent.change(nameInput, { target: { value: 'Research Bot' } });
  fireEvent.blur(nameInput);

  await waitFor(() => {
    const savedData = localStorage.getItem('agent-form-draft');
    expect(JSON.parse(savedData!).name).toBe('Research Bot');
  });
});
```

---

## 비기능 인수 기준

### 성능

#### 시나리오 P1: 폼 검증 반응 시간
**Given**: 사용자가 유효하지 않은 값을 입력하고,
**When**: 필드에서 포커스가 벗어나면,
**Then**:
- 에러 메시지가 100ms 이내에 표시되어야 한다

### 접근성

#### 시나리오 A1: 키보드 네비게이션
**Given**: 폼이 렌더링되어 있고,
**When**: Tab 키를 누르면,
**Then**:
- 포커스가 순차적으로 이동해야 한다 (이름 → 설명 → 목적 → 다음 버튼)

---

## Definition of Done
- ✅ 모든 인수 기준 시나리오 통과
- ✅ 테스트 커버리지 ≥ 85%
- ✅ 폼 제출 시간 < 1초
- ✅ ARIA 레이블 적용

---

**작성자**: @spec-builder
**작성일**: 2025-10-31
