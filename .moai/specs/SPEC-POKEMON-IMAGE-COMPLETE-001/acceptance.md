<!-- @DOC:POKEMON-IMAGE-ACCEPTANCE-001 -->

# Pokemon 카드 캐릭터 이미지 완성 - 인수 기준

**SPEC ID**: POKEMON-IMAGE-COMPLETE-001
**버전**: v0.0.1
**작성일**: 2025-11-08

---

## 📋 인수 기준 개요

이 문서는 Pokemon 스타일 Agent 카드 캐릭터 이미지 기능의 **완료 조건**을 정의합니다. 모든 시나리오가 통과해야 SPEC이 완료 상태로 전환됩니다.

---

## 🎯 Acceptance Criteria (Given-When-Then Format)

### AC-1: Agent 생성 시 기본 아바타 자동 할당

**Priority**: CRITICAL

**Given**: 사용자가 새로운 Agent를 생성할 때
**When**: POST `/agents/from-taxonomy` API가 호출될 때
**Then**:
- 응답 JSON에 `avatar_url` 필드가 포함되어야 함
- `avatar_url`은 `/avatars/{rarity}/default-{1|2|3}.png` 형식이어야 함
- `rarity` 필드가 `["Common", "Rare", "Epic", "Legendary"]` 중 하나여야 함
- 같은 `agent_id`로 재요청 시 항상 동일한 `avatar_url`을 반환해야 함 (deterministic)

**Verification**:
```bash
# Test command
curl -X POST http://localhost:8000/agents/from-taxonomy \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Agent",
    "taxonomy_node_ids": ["550e8400-e29b-41d4-a716-446655440000"]
  }'

# Expected response (example)
{
  "agent_id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Test Agent",
  "avatar_url": "/avatars/common/default-2.png",
  "rarity": "Common",
  ...
}
```

---

### AC-2: Rarity 자동 계산 로직

**Priority**: CRITICAL

**Given**: Agent가 생성될 때 taxonomy 노드 수가 주어질 때
**When**: 백엔드가 `calculate_initial_rarity()` 함수를 실행할 때
**Then**:
- 10개 이상 노드 → Rarity는 `"Legendary"`
- 5-9개 노드 → Rarity는 `"Epic"`
- 2-4개 노드 → Rarity는 `"Rare"`
- 1개 노드 → Rarity는 `"Common"`

**Test Scenarios**:

| Taxonomy Nodes | Expected Rarity |
|----------------|-----------------|
| 1 | Common |
| 2 | Rare |
| 5 | Epic |
| 10 | Legendary |
| 15 | Legendary |

**Verification**:
```python
# Unit test
def test_calculate_initial_rarity():
    assert calculate_initial_rarity([uuid4()]) == "Common"
    assert calculate_initial_rarity([uuid4(), uuid4()]) == "Rare"
    assert calculate_initial_rarity([uuid4() for _ in range(5)]) == "Epic"
    assert calculate_initial_rarity([uuid4() for _ in range(10)]) == "Legendary"
```

---

### AC-3: Database Migration 성공 (기존 데이터 영향 없음)

**Priority**: CRITICAL

**Given**: 기존 Agent 데이터가 Database에 존재할 때
**When**: Alembic migration `add_agent_avatar_fields`를 실행할 때
**Then**:
- `agents` 테이블에 3개 컬럼이 추가되어야 함:
  - `avatar_url` (VARCHAR 500, nullable)
  - `rarity` (VARCHAR 20, nullable, default='Common')
  - `character_description` (TEXT, nullable)
- 기존 Agent 레코드의 다른 필드는 변경되지 않아야 함
- Migration rollback (`alembic downgrade -1`)이 성공해야 함

**Verification**:
```bash
# Apply migration
alembic upgrade head

# Verify columns exist
psql -c "SELECT column_name, data_type, is_nullable, column_default
         FROM information_schema.columns
         WHERE table_name='agents'
         AND column_name IN ('avatar_url', 'rarity', 'character_description');"

# Expected output:
# column_name            | data_type        | is_nullable | column_default
# -----------------------|------------------|-------------|----------------
# avatar_url             | character varying| YES         | NULL
# rarity                 | character varying| YES         | 'Common'::character varying
# character_description  | text             | YES         | NULL

# Test rollback
alembic downgrade -1
psql -c "SELECT column_name FROM information_schema.columns WHERE table_name='agents' AND column_name='avatar_url';"
# Expected: (0 rows) - column should be dropped
```

---

### AC-4: AgentCard 컴포넌트에 캐릭터 이미지 표시

**Priority**: CRITICAL

**Given**: Agent 데이터에 `avatar_url` 필드가 포함되어 있을 때
**When**: `AgentCard` 컴포넌트가 렌더링될 때
**Then**:
- Header와 XP Progress 사이에 이미지 영역이 표시되어야 함
- 이미지 크기는 `h-48` (192px) 높이여야 함
- `<img>` 태그의 `src` 속성이 `avatar_url` 값과 일치해야 함
- `alt` 텍스트가 `"{agent.name} character"` 형식이어야 함
- `loading="lazy"` 속성이 적용되어야 함

**Verification**:
```tsx
// Component test
import { render, screen } from '@testing-library/react'
import { AgentCard } from '../AgentCard'

test('renders character avatar image', () => {
  const mockAgent = {
    agent_id: '123e4567-e89b-12d3-a456-426614174000',
    name: 'Test Agent',
    avatar_url: '/avatars/epic/default-1.png',
    rarity: 'Epic',
    level: 5,
    current_xp: 5000,
    next_level_xp: 10000,
    total_documents: 100,
    total_queries: 200,
    quality_score: 85,
    status: 'active',
    created_at: '2025-11-08T00:00:00Z',
  }

  render(<AgentCard agent={mockAgent} onView={() => {}} onDelete={() => {}} />)

  const avatar = screen.getByAlt('Test Agent character')
  expect(avatar).toBeInTheDocument()
  expect(avatar).toHaveAttribute('src', '/avatars/epic/default-1.png')
  expect(avatar).toHaveAttribute('loading', 'lazy')
})
```

---

### AC-5: 이미지 로드 실패 시 Fallback 아이콘 표시

**Priority**: HIGH

**Given**: `avatar_url`이 유효하지 않거나 이미지가 404 에러를 반환할 때
**When**: `<img>` 태그의 `onError` 이벤트가 발생할 때
**Then**:
- 이미지는 숨겨지고 Fallback 아이콘이 표시되어야 함
- Fallback 아이콘은 Rarity에 따라 다음과 같아야 함:
  - Legendary: 👑
  - Epic: ⚡
  - Rare: 💎
  - Common: 🤖
- Fallback 영역에 `role="img"` 및 `aria-label="{agent.name} avatar"` 속성이 있어야 함

**Verification**:
```tsx
// Component test
import { fireEvent } from '@testing-library/react'

test('shows fallback icon when image fails to load', async () => {
  const mockAgent = {
    agent_id: '123e4567-e89b-12d3-a456-426614174000',
    name: 'Test Agent',
    avatar_url: '/invalid-url.png',
    rarity: 'Legendary',
    level: 10,
    // ... other fields
  }

  render(<AgentCard agent={mockAgent} onView={() => {}} onDelete={() => {}} />)

  const avatar = screen.getByAlt('Test Agent character')
  fireEvent.error(avatar)  // Simulate image load error

  // Fallback icon should appear
  expect(screen.getByText('👑')).toBeInTheDocument()  // Legendary icon
  expect(screen.getByLabelText('Test Agent avatar')).toBeInTheDocument()
})
```

---

### AC-6: 기본 아바타 에셋 존재 검증

**Priority**: HIGH

**Given**: 프로덕션 배포 전
**When**: 정적 파일 디렉토리를 검사할 때
**Then**:
- `frontend/public/avatars/` 디렉토리에 4개 Rarity 폴더가 존재해야 함
- 각 Rarity 폴더에 3개 이미지 파일이 존재해야 함 (`default-1.png`, `default-2.png`, `default-3.png`)
- 총 12개 이미지 파일이 모두 존재해야 함
- 각 이미지 파일은 50KB 이하여야 함 (성능 최적화)

**Verification**:
```bash
# Automated check script
#!/bin/bash
for rarity in common rare epic legendary; do
  for i in 1 2 3; do
    file="frontend/public/avatars/$rarity/default-$i.png"
    if [ ! -f "$file" ]; then
      echo "❌ Missing: $file"
      exit 1
    fi

    # Check file size (<50KB)
    size=$(du -k "$file" | cut -f1)
    if [ "$size" -gt 50 ]; then
      echo "⚠️ File too large: $file (${size}KB)"
    fi
  done
done
echo "✅ All 12 avatar images present and optimized"
```

---

### AC-7: Backend-Frontend 타입 일치성

**Priority**: HIGH

**Given**: Backend API 응답과 Frontend Zod 스키마가 정의되어 있을 때
**When**: API 응답을 Zod schema로 파싱할 때
**Then**:
- `AgentResponse` (Pydantic)와 `AgentCardDataSchema` (Zod)의 필드가 일치해야 함
- 특히 다음 필드가 양쪽에 존재해야 함:
  - `avatar_url: Optional[str]` (Backend) ↔ `avatar_url: z.string().url().optional().nullable()` (Frontend)
  - `rarity: Rarity` (Backend) ↔ `rarity: RaritySchema` (Frontend)
- Zod 파싱 에러가 발생하지 않아야 함

**Verification**:
```typescript
// Integration test
import { AgentCardDataSchema } from '@/lib/api/types'

test('API response conforms to Zod schema', async () => {
  const response = await fetch('http://localhost:8000/agents/search')
  const data = await response.json()

  // Should not throw ZodError
  const agents = data.agents.map((agent: unknown) =>
    AgentCardDataSchema.parse(agent)
  )

  expect(agents.length).toBeGreaterThan(0)
  expect(agents[0]).toHaveProperty('avatar_url')
  expect(agents[0]).toHaveProperty('rarity')
})
```

---

### AC-8: Avatar URL 결정론적 분포 검증

**Priority**: MEDIUM

**Given**: `AvatarService.get_default_avatar_url()` 함수가 구현되어 있을 때
**When**: 10,000개의 무작위 UUID로 아바타 URL을 생성할 때
**Then**:
- 각 아바타 (`default-1`, `default-2`, `default-3`)의 사용 비율이 33% ± 3% 범위 내여야 함
- 같은 `agent_id`와 `rarity`로 여러 번 호출 시 항상 동일한 URL을 반환해야 함

**Verification**:
```python
# Distribution test
from uuid import uuid4
from collections import Counter

def test_avatar_distribution():
    results = []
    for _ in range(10000):
        agent_id = str(uuid4())
        url = AvatarService.get_default_avatar_url("Epic", agent_id)
        results.append(url)

    counts = Counter(results)
    for avatar, count in counts.items():
        ratio = count / 10000
        assert 0.30 <= ratio <= 0.36, f"{avatar}: {ratio*100:.2f}% (expected 33% ± 3%)"

def test_avatar_determinism():
    agent_id = "550e8400-e29b-41d4-a716-446655440000"
    url1 = AvatarService.get_default_avatar_url("Legendary", agent_id)
    url2 = AvatarService.get_default_avatar_url("Legendary", agent_id)
    assert url1 == url2  # Must be identical
```

---

### AC-9: E2E User Flow (Agent 생성 → 카드 표시)

**Priority**: HIGH

**Given**: 사용자가 웹 애플리케이션에 로그인한 상태일 때
**When**: 사용자가 "Create Agent" 버튼을 클릭하고 Agent를 생성할 때
**Then**:
1. Agent 생성 API가 성공적으로 호출되어야 함
2. Agent 목록 페이지로 리디렉션되어야 함
3. 새로 생성된 Agent 카드가 표시되어야 함
4. Agent 카드에 다음 요소가 모두 표시되어야 함:
   - Agent 이름 (Header)
   - Rarity Badge (Header)
   - **캐릭터 이미지 (Header와 XP Progress 사이)** ← 핵심 검증
   - XP Progress Bar
   - Stats Grid (Docs, Queries, Quality)
   - Action Buttons (View, Delete)

**Verification** (Playwright E2E):
```typescript
// e2e/agent-card-avatar.spec.ts
import { test, expect } from '@playwright/test'

test('user can create agent and see character avatar', async ({ page }) => {
  // 1. Navigate to home page
  await page.goto('http://localhost:3000')

  // 2. Click "Create Agent" button
  await page.click('button:has-text("Create Agent")')

  // 3. Fill form and submit
  await page.fill('input[name="name"]', 'E2E Test Agent')
  await page.selectOption('select[name="taxonomy"]', 'AI/ML')
  await page.click('button:has-text("Create")')

  // 4. Verify redirect to agent list
  await expect(page).toHaveURL('http://localhost:3000/agents')

  // 5. Verify agent card exists
  const agentCard = page.locator('article:has-text("E2E Test Agent")')
  await expect(agentCard).toBeVisible()

  // 6. Verify character avatar exists
  const avatar = agentCard.locator('img[alt*="character"]')
  await expect(avatar).toBeVisible()
  await expect(avatar).toHaveAttribute('src', /\/avatars\/\w+\/default-\d\.png/)

  // 7. Verify all card sections
  await expect(agentCard.locator('h3:has-text("E2E Test Agent")')).toBeVisible()  // Name
  await expect(agentCard.locator('[data-testid="rarity-badge"]')).toBeVisible()    // Rarity
  await expect(agentCard.locator('[data-testid="xp-progress"]')).toBeVisible()     // XP
  await expect(agentCard.locator('[data-testid="stats-grid"]')).toBeVisible()      // Stats
})
```

---

### AC-10: Visual Regression (UI 완성도 검증)

**Priority**: MEDIUM

**Given**: 모든 기능 구현이 완료된 상태일 때
**When**: Agent 카드를 스크린샷으로 촬영할 때
**Then**:
- Pokemon 카드 레이아웃이 다음 순서로 표시되어야 함:
  1. Header (Name + Rarity Badge)
  2. **Character Image (200x200px, gradient background)** ← 핵심 검증
  3. XP Progress Bar
  4. Stats Grid
  5. Action Buttons
- Rarity별 시각적 구분이 명확해야 함 (border 색상, badge 색상)
- Responsive design이 유지되어야 함 (mobile/tablet/desktop)

**Verification** (Visual Regression):
```typescript
// Percy/Chromatic visual test
import { percySnapshot } from '@percy/playwright'

test('pokemon card visual regression', async ({ page }) => {
  await page.goto('http://localhost:3000/agents')

  // Take snapshot for each rarity
  for (const rarity of ['Common', 'Rare', 'Epic', 'Legendary']) {
    const card = page.locator(`article:has([data-testid="rarity-badge"]:has-text("${rarity}"))`)
    await card.scrollIntoViewIfNeeded()
    await percySnapshot(page, `Agent Card - ${rarity}`)
  }
})
```

**Expected Result** (Pokemon 카드 구조):
```
┌────────────────────────────────┐
│ RAG Assistant Alpha      [EPIC]│  ← Header
│ Level 8                  (보라)│
├────────────────────────────────┤
│  ╔════════════════════════╗    │
│  ║                        ║    │
│  ║    🧙‍♂️ [Character]      ║    │  ← 🆕 Image Section
│  ║    (200x200px)         ║    │
│  ║                        ║    │
│  ╚════════════════════════╝    │
│  (Gradient Background)         │
├────────────────────────────────┤
│ [XP: 8500 / 10000 XP]          │  ← XP Progress
│ ████████████████░░░░ 85%       │
├────────────────────────────────┤
│ Docs    Queries   Quality      │  ← Stats Grid
│ 1250    3420      92           │
├────────────────────────────────┤
│        [View] [Delete]         │  ← Actions
└────────────────────────────────┘
```

---

## 🏁 Definition of Done (DoD)

### 필수 조건 (All MUST Pass)

- ✅ **AC-1**: Agent 생성 시 기본 아바타 자동 할당
- ✅ **AC-2**: Rarity 자동 계산 로직
- ✅ **AC-3**: Database Migration 성공
- ✅ **AC-4**: AgentCard 컴포넌트에 캐릭터 이미지 표시
- ✅ **AC-5**: 이미지 로드 실패 시 Fallback 아이콘 표시
- ✅ **AC-6**: 기본 아바타 에셋 존재 검증
- ✅ **AC-7**: Backend-Frontend 타입 일치성
- ✅ **AC-8**: Avatar URL 결정론적 분포 검증
- ✅ **AC-9**: E2E User Flow (Agent 생성 → 카드 표시)
- ✅ **AC-10**: Visual Regression (UI 완성도 검증)

### 추가 품질 기준

- ✅ **Test Coverage**: 85% 이상
- ✅ **TypeScript/Python Type Check**: 에러 없음
- ✅ **Accessibility**: WCAG 2.1 AA 준수 (alt text, aria-label)
- ✅ **Performance**: 이미지 로드 시간 < 500ms (Lazy loading 적용)
- ✅ **Browser Compatibility**: Chrome, Firefox, Safari 최신 2개 버전

---

## 📊 Quality Gates

### Gate 1: Unit Tests

**조건**:
- Backend: `pytest tests/integration/test_agent_avatar_api.py` 통과
- Frontend: `npm test -- AgentCard.test.tsx` 통과
- Coverage ≥ 85%

**실행 명령**:
```bash
# Backend
pytest tests/integration/test_agent_avatar_api.py --cov=apps.api.services --cov-report=term

# Frontend
npm test -- AgentCard.test.tsx --coverage
```

### Gate 2: Integration Tests

**조건**:
- API 응답에 `avatar_url`, `rarity` 필드 포함
- Zod schema 파싱 성공
- Database migration 성공 (rollback 포함)

**실행 명령**:
```bash
# API integration
pytest tests/integration/ --tb=short

# Migration test
alembic upgrade head && alembic downgrade -1 && alembic upgrade head
```

### Gate 3: E2E Tests

**조건**:
- Agent 생성 → 카드 표시 시나리오 성공
- 캐릭터 이미지 표시 확인
- Fallback 아이콘 표시 확인 (이미지 404 시)

**실행 명령**:
```bash
# Playwright E2E
npx playwright test e2e/agent-card-avatar.spec.ts
```

### Gate 4: Visual Regression

**조건**:
- Pokemon 카드 레이아웃 baseline과 일치
- Rarity별 시각적 구분 명확
- Responsive design 유지

**실행 명령**:
```bash
# Percy/Chromatic
npx percy exec -- playwright test
```

---

## 🚫 Rejection Criteria (DoD 실패 조건)

다음 조건 중 하나라도 발생 시 SPEC은 **완료 불가** 상태로 간주:

1. **이미지 에셋 누락**: 12개 아바타 이미지 중 하나라도 없을 경우
2. **Fallback 아이콘 미작동**: 이미지 404 에러 시 빈 화면 표시
3. **Backend-Frontend 타입 불일치**: Zod 파싱 에러 발생
4. **Database Migration 실패**: 기존 데이터 손실 또는 Rollback 실패
5. **E2E 시나리오 실패**: Agent 생성 후 카드에 이미지 미표시
6. **Test Coverage < 85%**: 품질 기준 미달
7. **Accessibility 위반**: alt text, aria-label 누락

---

## 📝 Test Evidence (증적 자료)

구현 완료 후 다음 증적 자료를 제출해야 합니다:

### 1. Test Reports
- ✅ Backend unit test report (pytest HTML report)
- ✅ Frontend component test report (Jest/Vitest HTML report)
- ✅ E2E test report (Playwright HTML report)
- ✅ Coverage report (85% 이상 확인)

### 2. Screenshots
- ✅ Pokemon 카드 스크린샷 (Rarity별 4종: Common, Rare, Epic, Legendary)
- ✅ Fallback 아이콘 스크린샷 (이미지 404 시나리오)
- ✅ Responsive design 스크린샷 (mobile/tablet/desktop)

### 3. API Response Examples
- ✅ `/agents/from-taxonomy` POST 응답 (avatar_url, rarity 포함)
- ✅ `/agents/search` GET 응답 (전체 Agent 리스트)

### 4. Database Schema Evidence
- ✅ `agents` 테이블 스키마 출력 (`\d agents` in psql)
- ✅ Migration history (`alembic history`)

---

**문서 버전**: v0.0.1
**최종 업데이트**: 2025-11-08
**작성자**: @spec-builder (MoAI-ADK Agent)
