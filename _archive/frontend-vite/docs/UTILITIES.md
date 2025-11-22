# @DOC:AGENT-CARD-001-UTILITIES

# Pokemon-Style Agent Card Utilities

에이전트 성장 시스템의 게임 로직을 담당하는 유틸리티 함수들의 문서입니다.

## 목차

1. [xpCalculator](#xpcalculator) - XP 계산
2. [levelCalculator](#levelcalculator) - 레벨 계산
3. [rarityResolver](#rarityresolver) - 희귀도 결정
4. [qualityScoreCalculator](#qualityscorecalculator) - 품질 점수 계산

---

## xpCalculator

**파일**: `frontend/src/lib/utils/xpCalculator.ts`
**TAG**: @CODE:AGENT-CARD-001-UTILS-001

사용자 행동에 따른 XP 획득량을 계산하는 함수입니다.

### 타입

```typescript
export type XpAction = 'CHAT' | 'FEEDBACK' | 'RAGAS'
```

### 함수

#### `calculateXp(action: XpAction | XpAction[]): number`

단일 또는 다중 행동에 대한 XP를 계산합니다.

**매개변수:**
- `action` - 단일 행동 또는 행동 배열

**반환값:**
- `number` - 획득한 총 XP

**XP 값 표:**

| Action | XP Value | Description |
|--------|----------|-------------|
| CHAT | 10 | 대화 완료 시 획득 |
| FEEDBACK | 50 | 긍정 피드백 (👍) 시 획득 |
| RAGAS | 100 | RAGAS 고품질 응답 (faithfulness >= 0.9) |

### 사용 예시

```typescript
import { calculateXp } from '@/lib/utils/xpCalculator'

// 단일 행동
const chatXp = calculateXp('CHAT')
console.log(chatXp) // 10

// 다중 행동
const totalXp = calculateXp(['CHAT', 'FEEDBACK', 'RAGAS'])
console.log(totalXp) // 160 (10 + 50 + 100)
```

### 실전 사용

```typescript
// 쿼리 완료 후 XP 증가
async function handleQueryComplete(agentId: string, faithfulness: number) {
  const actions: XpAction[] = ['CHAT']

  // RAGAS 보너스 조건
  if (faithfulness >= 0.9) {
    actions.push('RAGAS')
  }

  const xpGain = calculateXp(actions)
  await updateAgentXp(agentId, xpGain)
}

// 피드백 처리
async function handlePositiveFeedback(agentId: string) {
  const xpGain = calculateXp('FEEDBACK')
  await updateAgentXp(agentId, xpGain)
}
```

---

## levelCalculator

**파일**: `frontend/src/lib/utils/levelCalculator.ts`
**TAG**: @CODE:AGENT-CARD-001-UTILS-002

현재 XP를 기반으로 레벨을 계산하고 다음 레벨 XP를 반환하는 함수입니다.

### 상수

#### `LEVEL_THRESHOLDS: number[]`

각 레벨에 필요한 누적 XP 임계값입니다.

```typescript
export const LEVEL_THRESHOLDS = [
  0,      // Level 1: 0 XP
  100,    // Level 2: 100 XP
  250,    // Level 3: 250 XP
  500,    // Level 4: 500 XP
  1000,   // Level 5: 1000 XP
  2000,   // Level 6: 2000 XP
  3500,   // Level 7: 3500 XP
  5500,   // Level 8: 5500 XP
  8000,   // Level 9: 8000 XP
  11000   // Level 10: 11000 XP
]
```

**레벨 진행 테이블:**

| Level | Cumulative XP | XP to Next | Rarity |
|-------|---------------|------------|---------|
| 1 | 0 | 100 | Common |
| 2 | 100 | 150 | Common |
| 3 | 250 | 250 | Common |
| 4 | 500 | 500 | Rare |
| 5 | 1000 | 1000 | Rare |
| 6 | 2000 | 1500 | Rare |
| 7 | 3500 | 2000 | Epic |
| 8 | 5500 | 2500 | Epic |
| 9 | 8000 | 3000 | Legendary |
| 10 | 11000 | - | Legendary (MAX) |

### 함수

#### `calculateLevel(currentXp: number): number`

현재 XP를 기반으로 레벨을 계산합니다.

**매개변수:**
- `currentXp` - 현재 누적 XP

**반환값:**
- `number` - 계산된 레벨 (1-10)

**알고리즘:**
1. 임계값 배열을 역순으로 순회
2. 현재 XP가 임계값 이상인 첫 번째 레벨 반환
3. 조건을 만족하지 못하면 레벨 1 반환

#### `getNextLevelXp(currentLevel: number): number | null`

다음 레벨에 필요한 XP를 반환합니다.

**매개변수:**
- `currentLevel` - 현재 레벨

**반환값:**
- `number | null` - 다음 레벨 XP (MAX 레벨이면 null)

### 사용 예시

```typescript
import { calculateLevel, getNextLevelXp, LEVEL_THRESHOLDS } from '@/lib/utils/levelCalculator'

// 레벨 계산
const currentXp = 1500
const level = calculateLevel(currentXp)
console.log(level) // 5

// 다음 레벨 XP
const nextXp = getNextLevelXp(level)
console.log(nextXp) // 2000

// MAX 레벨 체크
const maxLevel = calculateLevel(20000)
console.log(maxLevel) // 10
console.log(getNextLevelXp(maxLevel)) // null
```

### 진행 바 계산

```typescript
import { calculateLevel, getNextLevelXp, LEVEL_THRESHOLDS } from '@/lib/utils/levelCalculator'

function getXpProgress(currentXp: number) {
  const level = calculateLevel(currentXp)
  const nextLevelXp = getNextLevelXp(level)

  // MAX 레벨 처리
  if (nextLevelXp === null) {
    return {
      current: currentXp,
      max: currentXp,
      percentage: 100
    }
  }

  // 현재 레벨 시작 XP
  const levelStartXp = LEVEL_THRESHOLDS[level - 1]

  // 레벨 내 진행 XP
  const current = currentXp - levelStartXp
  const max = nextLevelXp - levelStartXp
  const percentage = (current / max) * 100

  return { current, max, percentage }
}

// 사용 예시
const progress = getXpProgress(1500)
// { current: 500, max: 1000, percentage: 50 }
```

---

## rarityResolver

**파일**: `frontend/src/lib/utils/rarityResolver.ts`
**TAG**: @CODE:AGENT-CARD-001-UTILS-003

레벨을 기반으로 에이전트의 희귀도를 결정하는 함수입니다.

### 타입

```typescript
export type Rarity = 'Common' | 'Rare' | 'Epic' | 'Legendary'
```

### 함수

#### `resolveRarity(level: number): Rarity`

레벨에 따른 희귀도를 반환합니다.

**매개변수:**
- `level` - 에이전트 레벨 (1-10+)

**반환값:**
- `Rarity` - 희귀도 ('Common' | 'Rare' | 'Epic' | 'Legendary')

**희귀도 매핑 규칙:**

| Level Range | Rarity | Visual Style |
|-------------|--------|--------------|
| ≤ 0 | Common | Gray border |
| 1-3 | Common | Gray border |
| 4-6 | Rare | Blue border |
| 7-8 | Epic | Purple border + glow |
| ≥ 9 | Legendary | Gold border + rainbow glow |

### 사용 예시

```typescript
import { resolveRarity } from '@/lib/utils/rarityResolver'

console.log(resolveRarity(1))  // 'Common'
console.log(resolveRarity(3))  // 'Common'
console.log(resolveRarity(4))  // 'Rare'
console.log(resolveRarity(7))  // 'Epic'
console.log(resolveRarity(9))  // 'Legendary'
console.log(resolveRarity(10)) // 'Legendary'
```

### 레벨업 시 진화 감지

```typescript
import { resolveRarity } from '@/lib/utils/rarityResolver'

function detectEvolution(oldLevel: number, newLevel: number) {
  const oldRarity = resolveRarity(oldLevel)
  const newRarity = resolveRarity(newLevel)

  const evolved = oldRarity !== newRarity

  return {
    evolved,
    oldRarity,
    newRarity,
    message: evolved
      ? `${oldRarity} → ${newRarity} 진화!`
      : `레벨업! (${newRarity} 유지)`
  }
}

// 사용 예시
const result = detectEvolution(3, 4)
// {
//   evolved: true,
//   oldRarity: 'Common',
//   newRarity: 'Rare',
//   message: 'Common → Rare 진화!'
// }
```

### 희귀도별 스타일 적용

```typescript
import { resolveRarity } from '@/lib/utils/rarityResolver'

const rarityStyles = {
  Common: 'border-gray-300',
  Rare: 'border-blue-400',
  Epic: 'border-purple-500 shadow-purple-500/50',
  Legendary: 'border-accent-gold shadow-yellow-500/50 animate-pulse'
}

function getCardStyle(level: number) {
  const rarity = resolveRarity(level)
  return rarityStyles[rarity]
}
```

---

## qualityScoreCalculator

**파일**: `frontend/src/lib/utils/qualityScoreCalculator.ts`
**TAG**: @CODE:AGENT-CARD-001-UTILS-004

RAGAS 점수를 기반으로 품질 점수를 계산하는 함수입니다.

### 함수

#### `calculateQualityScore(ragasScore: number): number`

RAGAS 점수를 0-100 범위의 품질 점수로 변환합니다.

**매개변수:**
- `ragasScore` - RAGAS faithfulness 점수 (0.0-1.0)

**반환값:**
- `number` - 품질 점수 (0-100, 반올림)

**알고리즘:**
1. 입력값을 0-1 범위로 클램핑
2. 100을 곱하여 백분율로 변환
3. 소수점 반올림

### 사용 예시

```typescript
import { calculateQualityScore } from '@/lib/utils/qualityScoreCalculator'

console.log(calculateQualityScore(0.92))   // 92
console.log(calculateQualityScore(0.855))  // 86 (반올림)
console.log(calculateQualityScore(1.2))    // 100 (클램핑)
console.log(calculateQualityScore(-0.5))   // 0 (클램핑)
```

### 품질 등급 분류

```typescript
import { calculateQualityScore } from '@/lib/utils/qualityScoreCalculator'

function getQualityGrade(ragasScore: number) {
  const score = calculateQualityScore(ragasScore)

  if (score >= 90) {
    return { grade: 'S', color: 'text-green-600', label: '우수' }
  }
  if (score >= 80) {
    return { grade: 'A', color: 'text-blue-600', label: '양호' }
  }
  if (score >= 70) {
    return { grade: 'B', color: 'text-yellow-600', label: '보통' }
  }
  return { grade: 'C', color: 'text-red-600', label: '개선 필요' }
}

// 사용 예시
const grade = getQualityGrade(0.92)
// { grade: 'S', color: 'text-green-600', label: '우수' }
```

### StatDisplay 통합

```typescript
import { calculateQualityScore } from '@/lib/utils/qualityScoreCalculator'
import { StatDisplay } from '@/components/agent-card/StatDisplay'

function QualityDisplay({ ragasScore }: { ragasScore: number }) {
  const score = calculateQualityScore(ragasScore)
  const variant = score >= 90 ? 'success' : score >= 70 ? 'warning' : 'default'

  return (
    <StatDisplay
      label="Quality"
      value={`${score}%`}
      variant={variant}
    />
  )
}
```

---

## 유틸리티 조합 예시

### 에이전트 성장 전체 로직

```typescript
import { calculateXp } from '@/lib/utils/xpCalculator'
import { calculateLevel, getNextLevelXp } from '@/lib/utils/levelCalculator'
import { resolveRarity } from '@/lib/utils/rarityResolver'
import { calculateQualityScore } from '@/lib/utils/qualityScoreCalculator'

interface AgentGrowthData {
  currentXp: number
  level: number
  rarity: Rarity
  nextLevelXp: number | null
  qualityScore: number
}

function calculateAgentGrowth(
  currentXp: number,
  ragasScore: number
): AgentGrowthData {
  const level = calculateLevel(currentXp)
  const rarity = resolveRarity(level)
  const nextLevelXp = getNextLevelXp(level)
  const qualityScore = calculateQualityScore(ragasScore)

  return {
    currentXp,
    level,
    rarity,
    nextLevelXp,
    qualityScore
  }
}

// 사용 예시
const growth = calculateAgentGrowth(1500, 0.92)
// {
//   currentXp: 1500,
//   level: 5,
//   rarity: 'Rare',
//   nextLevelXp: 2000,
//   qualityScore: 92
// }
```

### XP 증가 및 레벨업 감지

```typescript
import { calculateXp } from '@/lib/utils/xpCalculator'
import { calculateLevel } from '@/lib/utils/levelCalculator'
import { resolveRarity } from '@/lib/utils/rarityResolver'

function processXpGain(
  currentXp: number,
  action: XpAction | XpAction[]
) {
  const oldLevel = calculateLevel(currentXp)
  const oldRarity = resolveRarity(oldLevel)

  const xpGain = calculateXp(action)
  const newXp = currentXp + xpGain

  const newLevel = calculateLevel(newXp)
  const newRarity = resolveRarity(newLevel)

  const leveledUp = newLevel > oldLevel
  const evolved = oldRarity !== newRarity

  return {
    xpGain,
    newXp,
    oldLevel,
    newLevel,
    leveledUp,
    evolved,
    oldRarity,
    newRarity
  }
}

// 사용 예시
const result = processXpGain(480, ['CHAT', 'RAGAS'])
// {
//   xpGain: 110,
//   newXp: 590,
//   oldLevel: 3,
//   newLevel: 4,
//   leveledUp: true,
//   evolved: true,
//   oldRarity: 'Common',
//   newRarity: 'Rare'
// }
```

---

## 테스트 커버리지

모든 유틸리티 함수는 100% 테스트 커버리지를 달성했습니다:

- `xpCalculator.test.ts` - 단일/다중 행동 XP 계산
- `levelCalculator.test.ts` - 레벨 계산 및 임계값 검증
- `rarityResolver.test.ts` - 희귀도 매핑 및 경계 케이스
- `qualityScoreCalculator.test.ts` - 점수 변환 및 클램핑

자세한 내용은 [TESTING.md](./TESTING.md)를 참조하세요.

---

## 관련 문서

- [COMPONENTS.md](./COMPONENTS.md) - 컴포넌트 API
- [TESTING.md](./TESTING.md) - 테스트 가이드
- [SPEC-AGENT-CARD-001](../.moai/specs/SPEC-AGENT-CARD-001/spec.md) - 원본 명세

## 기술 스택

- TypeScript 5.9.3
- Vitest 2.1.9 (테스트 프레임워크)

---

**Last Updated**: 2025-10-30
**Version**: 0.1.0
