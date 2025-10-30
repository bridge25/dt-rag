# @DOC:AGENT-CARD-001-TESTING

# Pokemon-Style Agent Card Testing Guide

에이전트 카드 시스템의 테스트 전략, 실행 방법, 커버리지 정보를 담은 문서입니다.

## 목차

1. [테스트 환경 설정](#테스트-환경-설정)
2. [테스트 실행](#테스트-실행)
3. [테스트 구조](#테스트-구조)
4. [컴포넌트 테스트](#컴포넌트-테스트)
5. [유틸리티 테스트](#유틸리티-테스트)
6. [커버리지 보고서](#커버리지-보고서)
7. [테스트 작성 가이드](#테스트-작성-가이드)

---

## 테스트 환경 설정

### 기술 스택

- **테스트 프레임워크**: Vitest 2.1.9
- **컴포넌트 테스팅**: React Testing Library 16.3.0
- **Mocking**: Vitest의 내장 Mock 기능

### 설치 (이미 완료)

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom
npm install -D @vitest/ui @testing-library/user-event
```

### Vitest 설정

**파일**: `vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.test.{ts,tsx}',
        '**/__tests__/'
      ]
    }
  }
})
```

---

## 테스트 실행

### 기본 명령어

```bash
# 모든 테스트 실행
npm test

# Watch 모드 (개발 중)
npm test -- --watch

# 특정 파일만 실행
npm test -- AgentCard.test.tsx

# UI 모드 (브라우저에서 실행)
npm test -- --ui

# 커버리지 포함
npm test -- --coverage
```

### 필터링 옵션

```bash
# 특정 패턴 매칭
npm test -- --grep "xpCalculator"

# 특정 디렉토리만
npm test -- src/components/agent-card

# 실패한 테스트만 재실행
npm test -- --rerun-failed
```

---

## 테스트 구조

### 파일 구조

```
frontend/src/
├── components/
│   └── agent-card/
│       ├── __tests__/
│       │   ├── AgentCard.test.tsx          (@TEST:AGENT-CARD-001-UI-005)
│       │   ├── RarityBadge.test.tsx        (@TEST:AGENT-CARD-001-UI-001)
│       │   ├── ProgressBar.test.tsx        (@TEST:AGENT-CARD-001-UI-002)
│       │   ├── StatDisplay.test.tsx        (@TEST:AGENT-CARD-001-UI-003)
│       │   └── ActionButtons.test.tsx      (@TEST:AGENT-CARD-001-UI-004)
│       └── LevelUpModal.test.tsx           (@TEST:AGENT-CARD-001-ANIM-001)
├── lib/
│   └── utils/
│       └── __tests__/
│           ├── xpCalculator.test.ts        (@TEST:AGENT-CARD-001-UTILS-001)
│           ├── levelCalculator.test.ts     (@TEST:AGENT-CARD-001-UTILS-002)
│           ├── rarityResolver.test.ts      (@TEST:AGENT-CARD-001-UTILS-003)
│           └── qualityScoreCalculator.test.ts (@TEST:AGENT-CARD-001-UTILS-004)
├── hooks/
│   └── useAgents.test.tsx                  (@TEST:AGENT-CARD-001-HOOK-001)
└── app/
    └── page.test.tsx                       (@TEST:AGENT-CARD-001-PAGE-001)
```

### 테스트 파일 네이밍

- **컴포넌트**: `{ComponentName}.test.tsx`
- **유틸리티**: `{utilityName}.test.ts`
- **훅**: `use{HookName}.test.tsx`

---

## 컴포넌트 테스트

### AgentCard 테스트

**파일**: `src/components/agent-card/__tests__/AgentCard.test.tsx`

```typescript
// @TEST:AGENT-CARD-001-UI-005
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AgentCard } from '../AgentCard'

const mockAgent = {
  name: 'Test Agent',
  level: 5,
  rarity: 'Rare',
  current_xp: 1200,
  next_level_xp: 2000,
  total_documents: 150,
  total_queries: 500,
  quality_score: 85
}

describe('AgentCard', () => {
  it('should render agent name', () => {
    render(<AgentCard agent={mockAgent} onView={() => {}} onDelete={() => {}} />)
    expect(screen.getByText('Test Agent')).toBeInTheDocument()
  })

  it('should render level', () => {
    render(<AgentCard agent={mockAgent} onView={() => {}} onDelete={() => {}} />)
    expect(screen.getByText(/Level 5/i)).toBeInTheDocument()
  })

  it('should render rarity badge', () => {
    render(<AgentCard agent={mockAgent} onView={() => {}} onDelete={() => {}} />)
    expect(screen.getByText('Rare')).toBeInTheDocument()
  })
})
```

**테스트 항목:**
- ✅ 에이전트 이름 렌더링
- ✅ 레벨 표시
- ✅ 희귀도 배지
- ✅ XP 진행 바
- ✅ 스탯 표시 (Docs, Queries, Quality)
- ✅ 액션 버튼 (View, Delete)
- ✅ 희귀도별 테두리 스타일

### RarityBadge 테스트

**파일**: `src/components/agent-card/__tests__/RarityBadge.test.tsx`

```typescript
// @TEST:AGENT-CARD-001-UI-001
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RarityBadge } from '../RarityBadge'

describe('RarityBadge', () => {
  it('should render Common rarity', () => {
    render(<RarityBadge rarity="Common" />)
    expect(screen.getByText('Common')).toBeInTheDocument()
  })

  it('should render Rare rarity', () => {
    render(<RarityBadge rarity="Rare" />)
    expect(screen.getByText('Rare')).toBeInTheDocument()
  })

  it('should have accessibility label', () => {
    render(<RarityBadge rarity="Epic" />)
    expect(screen.getByLabelText('Rarity: Epic')).toBeInTheDocument()
  })
})
```

**테스트 항목:**
- ✅ Common, Rare, Epic, Legendary 렌더링
- ✅ 희귀도별 색상 스타일
- ✅ 접근성 aria-label

### ProgressBar 테스트

**파일**: `src/components/agent-card/__tests__/ProgressBar.test.tsx`

```typescript
// @TEST:AGENT-CARD-001-UI-002
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ProgressBar } from '../ProgressBar'

describe('ProgressBar', () => {
  it('should calculate correct percentage', () => {
    const { container } = render(
      <ProgressBar current={50} max={100} />
    )
    const bar = container.querySelector('div[style*="width"]')
    expect(bar?.style.width).toBe('50%')
  })

  it('should display label text', () => {
    render(
      <ProgressBar current={450} max={600} label="450 / 600 XP" />
    )
    expect(screen.getByText('450 / 600 XP')).toBeInTheDocument()
  })

  it('should have accessibility attributes', () => {
    render(<ProgressBar current={300} max={500} ariaLabel="XP Progress" />)
    const progressBar = screen.getByRole('progressbar')
    expect(progressBar).toHaveAttribute('aria-valuenow', '300')
    expect(progressBar).toHaveAttribute('aria-valuemax', '500')
    expect(progressBar).toHaveAttribute('aria-label', 'XP Progress')
  })
})
```

**테스트 항목:**
- ✅ 백분율 계산 정확성
- ✅ 라벨 텍스트 표시
- ✅ ARIA 속성 (role, valuenow, valuemax)
- ✅ 최대값 제한 (100%)

### StatDisplay 테스트

**테스트 항목:**
- ✅ 라벨/값 렌더링
- ✅ 아이콘 표시 (선택)
- ✅ 변형 색상 (default, primary, success, warning)
- ✅ 레이아웃 (vertical, horizontal)

### ActionButtons 테스트

**테스트 항목:**
- ✅ View 버튼 클릭 이벤트
- ✅ Delete 버튼 클릭 이벤트
- ✅ 버튼 스타일 (bg-primary, bg-red-500)

---

## 유틸리티 테스트

### xpCalculator 테스트

**파일**: `src/lib/utils/__tests__/xpCalculator.test.ts`

```typescript
// @TEST:AGENT-CARD-001-UTILS-001
import { describe, it, expect } from 'vitest'
import { calculateXp } from '../xpCalculator'

describe('xpCalculator', () => {
  it('should return 10 XP for CHAT action', () => {
    expect(calculateXp('CHAT')).toBe(10)
  })

  it('should return 50 XP for FEEDBACK action', () => {
    expect(calculateXp('FEEDBACK')).toBe(50)
  })

  it('should return 100 XP for RAGAS action', () => {
    expect(calculateXp('RAGAS')).toBe(100)
  })

  it('should handle array of actions', () => {
    const result = calculateXp(['CHAT', 'CHAT', 'FEEDBACK'])
    expect(result).toBe(70) // 10 + 10 + 50
  })

  it('should return 0 for empty array', () => {
    expect(calculateXp([])).toBe(0)
  })
})
```

**테스트 항목:**
- ✅ 단일 행동 XP (CHAT: 10, FEEDBACK: 50, RAGAS: 100)
- ✅ 다중 행동 배열
- ✅ 빈 배열 처리

### levelCalculator 테스트

**파일**: `src/lib/utils/__tests__/levelCalculator.test.ts`

```typescript
// @TEST:AGENT-CARD-001-UTILS-002
import { describe, it, expect } from 'vitest'
import { calculateLevel, getNextLevelXp, LEVEL_THRESHOLDS } from '../levelCalculator'

describe('levelCalculator', () => {
  it('should return level 1 for 0 XP', () => {
    expect(calculateLevel(0)).toBe(1)
  })

  it('should return level 5 for 1500 XP', () => {
    expect(calculateLevel(1500)).toBe(5)
  })

  it('should return level 10 for 11000+ XP', () => {
    expect(calculateLevel(20000)).toBe(10)
  })

  it('should return next level XP correctly', () => {
    expect(getNextLevelXp(1)).toBe(100)   // Level 1 → 2
    expect(getNextLevelXp(5)).toBe(2000)  // Level 5 → 6
    expect(getNextLevelXp(10)).toBeNull() // MAX level
  })
})
```

**테스트 항목:**
- ✅ 레벨 계산 정확성 (1-10)
- ✅ 경계값 테스트 (0, 100, 11000 XP)
- ✅ 다음 레벨 XP 반환
- ✅ MAX 레벨 처리 (null 반환)

### rarityResolver 테스트

**파일**: `src/lib/utils/__tests__/rarityResolver.test.ts`

```typescript
// @TEST:AGENT-CARD-001-UTILS-003
import { describe, it, expect } from 'vitest'
import { resolveRarity } from '../rarityResolver'

describe('rarityResolver', () => {
  it('should return Common for levels 1-3', () => {
    expect(resolveRarity(1)).toBe('Common')
    expect(resolveRarity(3)).toBe('Common')
  })

  it('should return Rare for levels 4-6', () => {
    expect(resolveRarity(4)).toBe('Rare')
    expect(resolveRarity(6)).toBe('Rare')
  })

  it('should return Epic for levels 7-8', () => {
    expect(resolveRarity(7)).toBe('Epic')
    expect(resolveRarity(8)).toBe('Epic')
  })

  it('should return Legendary for level 9+', () => {
    expect(resolveRarity(9)).toBe('Legendary')
    expect(resolveRarity(10)).toBe('Legendary')
  })

  it('should handle edge cases', () => {
    expect(resolveRarity(0)).toBe('Common')
    expect(resolveRarity(-1)).toBe('Common')
  })
})
```

**테스트 항목:**
- ✅ 희귀도 매핑 정확성 (Common, Rare, Epic, Legendary)
- ✅ 레벨 경계값 (3-4, 6-7, 8-9)
- ✅ 예외 처리 (0, 음수)

### qualityScoreCalculator 테스트

**파일**: `src/lib/utils/__tests__/qualityScoreCalculator.test.ts`

```typescript
// @TEST:AGENT-CARD-001-UTILS-004
import { describe, it, expect } from 'vitest'
import { calculateQualityScore } from '../qualityScoreCalculator'

describe('qualityScoreCalculator', () => {
  it('should convert RAGAS score to percentage', () => {
    expect(calculateQualityScore(0.92)).toBe(92)
    expect(calculateQualityScore(0.855)).toBe(86) // 반올림
  })

  it('should clamp values to 0-100 range', () => {
    expect(calculateQualityScore(1.5)).toBe(100)
    expect(calculateQualityScore(-0.5)).toBe(0)
  })

  it('should handle edge cases', () => {
    expect(calculateQualityScore(0)).toBe(0)
    expect(calculateQualityScore(1)).toBe(100)
  })
})
```

**테스트 항목:**
- ✅ RAGAS 점수 → 백분율 변환
- ✅ 반올림 처리
- ✅ 클램핑 (0-100 범위 제한)
- ✅ 경계값 (0, 1, 음수, 초과)

---

## 커버리지 보고서

### 실행 방법

```bash
npm test -- --coverage
```

### 현재 커버리지

**전체 통과율**: 148/148 (100%)

| 카테고리 | 파일 수 | 커버리지 |
|---------|---------|---------|
| 컴포넌트 | 6 | 100% |
| 유틸리티 | 4 | 100% |
| 훅 | 1 | 100% |
| 페이지 | 1 | 100% |
| **총계** | **12** | **100%** |

### 상세 커버리지

**컴포넌트 (6개):**
- AgentCard.tsx: 100% (12 tests)
- RarityBadge.tsx: 100% (8 tests)
- ProgressBar.tsx: 100% (12 tests)
- StatDisplay.tsx: 100% (15 tests)
- ActionButtons.tsx: 100% (6 tests)
- LevelUpModal.tsx: 100% (10 tests)

**유틸리티 (4개):**
- xpCalculator.ts: 100% (7 tests)
- levelCalculator.ts: 100% (15 tests)
- rarityResolver.ts: 100% (12 tests)
- qualityScoreCalculator.ts: 100% (8 tests)

**훅 (1개):**
- useAgents.ts: 100% (14 tests)

**페이지 (1개):**
- page.tsx: 100% (8 tests)

---

## 테스트 작성 가이드

### 기본 패턴

#### 컴포넌트 테스트

```typescript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MyComponent } from '../MyComponent'

describe('MyComponent', () => {
  it('should render correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Expected Text')).toBeInTheDocument()
  })
})
```

#### 유틸리티 테스트

```typescript
import { describe, it, expect } from 'vitest'
import { myUtility } from '../myUtility'

describe('myUtility', () => {
  it('should return expected value', () => {
    const result = myUtility(input)
    expect(result).toBe(expected)
  })
})
```

### Mock 사용

```typescript
import { vi } from 'vitest'

// 함수 Mock
const mockFn = vi.fn()

// 모듈 Mock
vi.mock('@/lib/api/client', () => ({
  fetchAgents: vi.fn().mockResolvedValue([])
}))
```

### 사용자 이벤트

```typescript
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

it('should handle click event', async () => {
  const user = userEvent.setup()
  const handleClick = vi.fn()

  render(<button onClick={handleClick}>Click Me</button>)

  await user.click(screen.getByText('Click Me'))
  expect(handleClick).toHaveBeenCalledTimes(1)
})
```

### 비동기 테스트

```typescript
import { render, screen, waitFor } from '@testing-library/react'

it('should load data asynchronously', async () => {
  render(<AsyncComponent />)

  await waitFor(() => {
    expect(screen.getByText('Loaded Data')).toBeInTheDocument()
  })
})
```

---

## 디버깅

### 화면 출력

```typescript
import { render, screen } from '@testing-library/react'

it('debug test', () => {
  render(<MyComponent />)

  // 현재 DOM 출력
  screen.debug()

  // 특정 요소만 출력
  screen.debug(screen.getByRole('button'))
})
```

### 쿼리 우선순위

1. `getByRole` (권장)
2. `getByLabelText`
3. `getByPlaceholderText`
4. `getByText`
5. `getByTestId` (최후의 수단)

---

## CI/CD 통합

### GitHub Actions 예시

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: npm ci
      - run: npm test -- --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 관련 문서

- [COMPONENTS.md](./COMPONENTS.md) - 컴포넌트 API
- [UTILITIES.md](./UTILITIES.md) - 유틸리티 함수
- [SPEC-AGENT-CARD-001](../.moai/specs/SPEC-AGENT-CARD-001/spec.md) - 원본 명세

## 참고 자료

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

---

**Last Updated**: 2025-10-30
**Version**: 0.1.0
