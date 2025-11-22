# @DOC:AGENT-CARD-001-COMPONENTS

# Pokemon-Style Agent Card Components

에이전트 카드 시스템을 구성하는 React 컴포넌트들의 API 문서입니다.

## 목차

1. [AgentCard](#agentcard) - 메인 카드 컴포넌트
2. [RarityBadge](#raritybadge) - 희귀도 배지
3. [ProgressBar](#progressbar) - XP 진행 바
4. [StatDisplay](#statdisplay) - 스탯 표시
5. [ActionButtons](#actionbuttons) - 액션 버튼
6. [LevelUpModal](#levelupmodal) - 레벨업 모달

---

## AgentCard

**파일**: `frontend/src/components/agent-card/AgentCard.tsx`
**TAG**: @CODE:AGENT-CARD-001-UI-005

Pokemon 스타일 에이전트 카드의 메인 컴포넌트입니다. 희귀도별 테두리, XP 진행 바, 스탯 표시, 액션 버튼을 포함합니다.

### Props

```typescript
interface AgentCardProps {
  agent: AgentCardData      // 에이전트 데이터
  onView: () => void        // View 버튼 클릭 핸들러
  onDelete: () => void      // Delete 버튼 클릭 핸들러
  className?: string        // 추가 CSS 클래스
}
```

### AgentCardData 타입

```typescript
interface AgentCardData {
  name: string
  level: number
  rarity: Rarity                    // 'Common' | 'Rare' | 'Epic' | 'Legendary'
  current_xp: number
  next_level_xp: number | null      // null이면 MAX 레벨
  total_documents: number
  total_queries: number
  quality_score: number             // 0-100
}
```

### 사용 예시

```tsx
import { AgentCard } from '@/components/agent-card/AgentCard'

function HomePage() {
  const agent = {
    name: 'Customer Support Agent',
    level: 5,
    rarity: 'Epic',
    current_xp: 450,
    next_level_xp: 600,
    total_documents: 125,
    total_queries: 342,
    quality_score: 92
  }

  return (
    <AgentCard
      agent={agent}
      onView={() => console.log('View clicked')}
      onDelete={() => console.log('Delete clicked')}
    />
  )
}
```

### 희귀도별 스타일

| Rarity | Border Color | Shadow |
|--------|-------------|--------|
| Common | Gray (#d1d5db) | shadow-md |
| Rare | Blue (#60a5fa) | shadow-md |
| Epic | Purple (#a855f7) | shadow-md |
| Legendary | Gold (#ffd700) | shadow-lg |

### 접근성

- 카드 너비: 고정 280px
- 반응형 그리드 레이아웃 지원
- Hover 시 shadow 확대 효과

---

## RarityBadge

**파일**: `frontend/src/components/agent-card/RarityBadge.tsx`
**TAG**: @CODE:AGENT-CARD-001-UI-001

에이전트의 희귀도를 표시하는 배지 컴포넌트입니다.

### Props

```typescript
interface RarityBadgeProps {
  rarity: Rarity         // 'Common' | 'Rare' | 'Epic' | 'Legendary'
  className?: string     // 추가 CSS 클래스
}
```

### 사용 예시

```tsx
import { RarityBadge } from '@/components/agent-card/RarityBadge'

<RarityBadge rarity="Epic" />
```

### 희귀도별 색상

| Rarity | Background | Text Color |
|--------|-----------|-----------|
| Common | bg-gray-500 | text-white |
| Rare | bg-blue-500 | text-white |
| Epic | bg-purple-600 | text-white |
| Legendary | bg-accent-gold | text-black |

### 접근성

- `aria-label="Rarity: {rarity}"` 포함
- 대문자 표시 (uppercase)
- 반올림 테두리 (rounded-full)

---

## ProgressBar

**파일**: `frontend/src/components/agent-card/ProgressBar.tsx`
**TAG**: @CODE:AGENT-CARD-001-UI-002

XP 진행 상태를 시각화하는 진행 바 컴포넌트입니다.

### Props

```typescript
interface ProgressBarProps {
  current: number       // 현재 XP
  max: number          // 최대 XP (다음 레벨)
  label?: string       // 하단 라벨 텍스트 (예: "450 / 600 XP")
  ariaLabel?: string   // 접근성 라벨 (기본값: "Progress")
  className?: string   // 추가 CSS 클래스
}
```

### 사용 예시

```tsx
import { ProgressBar } from '@/components/agent-card/ProgressBar'

<ProgressBar
  current={450}
  max={600}
  label="450 / 600 XP"
  ariaLabel="Experience progress"
/>
```

### 시각적 특징

- **높이**: 8px (h-2)
- **배경**: 회색 (bg-gray-200)
- **진행 바**: 그라디언트 (blue → purple → pink)
- **애니메이션**: 0.3초 ease-out 전환
- **최대 백분율**: 100% 제한

### 접근성

- `role="progressbar"` 속성
- `aria-valuenow`, `aria-valuemin`, `aria-valuemax` 포함
- 스크린 리더 지원

---

## StatDisplay

**파일**: `frontend/src/components/agent-card/StatDisplay.tsx`
**TAG**: @CODE:AGENT-CARD-001-UI-003

스탯 정보를 표시하는 범용 컴포넌트입니다.

### Props

```typescript
interface StatDisplayProps {
  label: string                 // 스탯 라벨 (예: "Docs", "Quality")
  value: string | number        // 스탯 값
  icon?: ReactNode             // 아이콘 (선택)
  variant?: 'default' | 'primary' | 'success' | 'warning'  // 색상 변형
  layout?: 'vertical' | 'horizontal'  // 레이아웃 방향
  className?: string           // 추가 CSS 클래스
}
```

### 사용 예시

```tsx
import { StatDisplay } from '@/components/agent-card/StatDisplay'
import { BookOpen } from 'lucide-react'

// 세로 레이아웃 (기본)
<StatDisplay label="Docs" value={125} layout="vertical" />

// 가로 레이아웃 + 아이콘
<StatDisplay
  label="Quality"
  value="92%"
  icon={<BookOpen size={16} />}
  variant="success"
  layout="horizontal"
/>
```

### 변형 색상

| Variant | Color Class | Use Case |
|---------|------------|----------|
| default | text-gray-900 | 일반 스탯 |
| primary | text-primary | 강조 스탯 |
| success | text-green-600 | 품질 점수 (90%+) |
| warning | text-yellow-600 | 경고 스탯 (70-89%) |

### 레이아웃

- **Vertical**: 라벨 위, 값 아래 (기본)
- **Horizontal**: 라벨 좌측, 값 우측

---

## ActionButtons

**파일**: `frontend/src/components/agent-card/ActionButtons.tsx`
**TAG**: @CODE:AGENT-CARD-001-UI-004

에이전트 카드의 액션 버튼 컴포넌트입니다.

### Props

```typescript
interface ActionButtonsProps {
  onView: () => void      // View 버튼 클릭 핸들러
  onDelete: () => void    // Delete 버튼 클릭 핸들러
  className?: string      // 추가 CSS 클래스
}
```

### 사용 예시

```tsx
import { ActionButtons } from '@/components/agent-card/ActionButtons'

<ActionButtons
  onView={() => navigate(`/agents/${agentId}`)}
  onDelete={() => handleDelete(agentId)}
/>
```

### 버튼 스타일

| Button | Background | Hover Effect |
|--------|-----------|-------------|
| View | bg-primary (blue) | opacity-90 |
| Delete | bg-red-500 | opacity-90 |

### 접근성

- 동일한 너비 (flex-1)
- 2px 간격 (gap-2)
- 클릭 영역 확보 (px-3 py-1.5)

---

## LevelUpModal

**파일**: `frontend/src/components/agent-card/LevelUpModal.tsx`
**TAG**: @CODE:AGENT-CARD-001-ANIM-001

레벨업 시 표시되는 축하 모달 컴포넌트입니다.

### Props

```typescript
interface LevelUpModalProps {
  isOpen: boolean           // 모달 표시 여부
  onClose: () => void       // 닫기 핸들러
  newLevel: number          // 새 레벨
  oldRarity: Rarity        // 이전 희귀도
  newRarity: Rarity        // 새 희귀도
}
```

### 사용 예시

```tsx
import { LevelUpModal } from '@/components/agent-card/LevelUpModal'
import { useState } from 'react'

function AgentPage() {
  const [showModal, setShowModal] = useState(false)

  return (
    <LevelUpModal
      isOpen={showModal}
      onClose={() => setShowModal(false)}
      newLevel={6}
      oldRarity="Rare"
      newRarity="Epic"
    />
  )
}
```

### 애니메이션 효과

1. **Confetti**: 화면 전체 3초 애니메이션 (react-confetti)
2. **모달 등장**: Scale 0.8 → 1.0 (framer-motion)
3. **희귀도 진화**: 이전/새 희귀도 표시 (변경 시에만)

### 모달 구조

```
┌─────────────────────────────┐
│     🎉 축하합니다!           │
│                              │
│     Lv.6 달성!              │
│                              │
│  Rare → Epic 진화!          │ (희귀도 변경 시)
│                              │
│      [ 확인 ]               │
└─────────────────────────────┘
```

---

## 컴포넌트 조합 예시

### 에이전트 카드 그리드

```tsx
import { AgentCard } from '@/components/agent-card/AgentCard'
import { useAgents } from '@/hooks/useAgents'

export function AgentGrid() {
  const { data: agents, isLoading } = useAgents()

  if (isLoading) return <div>Loading...</div>

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {agents?.map((agent) => (
        <AgentCard
          key={agent.agent_id}
          agent={agent}
          onView={() => navigate(`/agents/${agent.agent_id}`)}
          onDelete={() => handleDelete(agent.agent_id)}
        />
      ))}
    </div>
  )
}
```

### 반응형 브레이크포인트

| Screen Size | Columns | Breakpoint |
|-------------|---------|-----------|
| Mobile | 1 | < 640px |
| Tablet | 2 | 640px - 1024px |
| Desktop | 3 | 1024px - 1536px |
| Large Desktop | 4 | > 1536px |

---

## 관련 문서

- [UTILITIES.md](./UTILITIES.md) - 유틸리티 함수
- [TESTING.md](./TESTING.md) - 테스트 가이드
- [SPEC-AGENT-CARD-001](../.moai/specs/SPEC-AGENT-CARD-001/spec.md) - 원본 명세

## 기술 스택

- React 19.1.1
- TypeScript 5.9.3
- Tailwind CSS 4.1.16
- framer-motion 11.18.2
- react-confetti 6.4.0

---

**Last Updated**: 2025-10-30
**Version**: 0.1.0
