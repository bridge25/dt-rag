---
id: AGENT-CARD-001
version: 0.0.1
status: draft
created: 2025-10-30
updated: 2025-10-30
author: @Alfred
priority: high
category: feature
labels:
  - frontend
  - ui
  - pokemon-style
  - agent-card
  - gamification
scope:
  packages:
    - frontend/src/components/agent-card
    - frontend/src/components/level-up
    - frontend/src/lib/utils
    - frontend/src/hooks
---

# @SPEC:AGENT-CARD-001 Pokemon-Style Agent Card System

## 개요

포켓몬 카드 스타일의 에이전트 성장 시스템을 프론트엔드에 구현합니다. 사용자 상호작용(채팅, 피드백, RAGAS 평가)을 통해 에이전트가 경험치를 획득하고 레벨업하며, 희귀도(Rarity)가 진화하는 게임화된 UI/UX를 제공합니다.

이 SPEC은 3단계를 통합합니다:
- **Phase 1**: UI 컴포넌트 (AgentCard, ProgressBar, RarityBadge, StatDisplay)
- **Phase 2**: 게임 로직 (XP 계산, 레벨 진행, 희귀도 결정, 품질 점수)
- **Phase 3**: 애니메이션 (레벨업 모달, XP 획득 효과, confetti)

## 환경 (Environment)

### 기술 스택
- **Frontend Framework**: React 19.1.1
- **Language**: TypeScript 5.9.3
- **Styling**: Tailwind CSS 4.1.16 (디자인 토큰 구성 완료)
- **Type Validation**: Zod 4.1.12
- **State Management**: Zustand 5.0.8
- **Data Fetching**: TanStack Query 5.90.5
- **Routing**: React Router DOM 7.9.5
- **Animation Libraries** (NEW - 설치 필요):
  - react-confetti ^6.1.0
  - framer-motion ^11.15.0
- **Icons**: lucide-react 0.548.0

### 백엔드 API 엔드포인트
- `GET /api/v1/agents` - 에이전트 목록 조회 (필터링 지원)
- `GET /api/v1/agents/{agent_id}` - 단일 에이전트 조회
- `POST /api/v1/agents/{agent_id}/query` - 에이전트 쿼리 실행
- `GET /api/v1/agents/{agent_id}/coverage` - 커버리지 계산
- `GET /api/v1/agents/{agent_id}/gaps` - 지식 갭 탐지

### 백엔드 데이터 모델 (활용 가능)
```typescript
// AgentResponse (apps/api/schemas/agent_schemas.py)
{
  agent_id: UUID4
  name: string
  level: number (1-5)           // ⚠️ 프론트엔드는 1-10+ 지원 필요
  current_xp: number            // ✅ 활용
  total_documents: number       // ✅ "지식 X개"로 표시
  total_chunks: number          // ✅ 참고용
  total_queries: number         // ✅ "대화 X회"로 표시
  successful_queries: number    // ✅ 성공률 계산
  avg_faithfulness: number      // ✅ 품질 점수 계산 (0.0-1.0)
  avg_response_time_ms: number  // ⚠️ 백엔드 미구현
  coverage_percent: number      // ✅ 커버리지 표시
  retrieval_config: JSONB       // 참고용
  features_config: JSONB        // 참고용
  created_at: datetime
  updated_at: datetime
  last_query_at: datetime
}
```

### 백엔드와 프론트엔드 간 데이터 갭
1. **희귀도 시스템**: 백엔드 `level` (1-5) → 프론트엔드 희귀도 계산 필요
2. **피드백 추적**: 백엔드에 `positive_feedbacks`, `negative_feedbacks` 컬럼 없음 → `avg_faithfulness`로 대체
3. **품질 점수**: 백엔드에 종합 품질 점수 없음 → 프론트엔드에서 계산 (피드백 70% + RAGAS 30%)
4. **XP 증가 로직**: 백엔드에 XP 증가 엔드포인트 없음 → 클라이언트 사이드 계산 또는 향후 추가
5. **레벨업 알림**: 실시간 레벨업 트리거 없음 → 프론트엔드에서 threshold 기반 판단

### 디렉토리 구조
```
frontend/src/
├── components/
│   ├── agent-card/
│   │   ├── AgentCard.tsx           # 메인 카드 컴포넌트 (280px 고정 너비)
│   │   ├── ProgressBar.tsx         # XP 진행 바 (희귀도별 그라디언트)
│   │   ├── RarityBadge.tsx         # 희귀도 배지 (Common/Rare/Epic/Legendary)
│   │   ├── StatDisplay.tsx         # 스탯 표시 (지식, 대화, 품질)
│   │   └── ActionButtons.tsx       # 액션 버튼 (대화/기록)
│   └── level-up/
│       ├── LevelUpModal.tsx        # 레벨업 축하 모달
│       └── ConfettiAnimation.tsx   # react-confetti 래퍼
├── lib/
│   ├── api/
│   │   ├── types.ts                # AgentCardData 타입 추가
│   │   └── client.ts               # ✅ 기존 API 클라이언트
│   └── utils/
│       ├── xpCalculator.ts         # XP 계산 로직
│       ├── levelCalculator.ts      # 레벨 계산 (XP → Level)
│       ├── rarityResolver.ts       # 희귀도 결정 (Level → Rarity)
│       └── qualityScoreCalculator.ts # 품질 점수 계산
├── hooks/
│   ├── useAgents.ts                # TanStack Query: 에이전트 목록
│   ├── useAgentGrowth.ts           # XP/레벨 상태 관리
│   └── useLevelUpNotification.ts   # 레벨업 트리거 감지
└── pages/
    └── HomePage.tsx                # 에이전트 카드 그리드 표시
```

## 가정 (Assumptions)

### 비즈니스 로직 가정
1. **XP 획득 규칙**:
   - 대화 완료: +10 XP
   - 긍정 피드백 (👍): +50 XP
   - RAGAS 고품질 응답 (faithfulness >= 0.9): +100 XP

2. **레벨 진행 테이블**:
   | Level | Required XP | Cumulative XP | Rarity       |
   |-------|-------------|---------------|--------------|
   | 1     | 0           | 0             | Common       |
   | 2     | 100         | 100           | Common       |
   | 3     | 200         | 300           | Rare         |
   | 4     | 300         | 600           | Rare         |
   | 5     | 400         | 1000          | Epic         |
   | 6     | 500         | 1500          | Epic         |
   | 7     | 600         | 2100          | Epic         |
   | 8     | 800         | 2900          | Legendary    |
   | 9     | 1000        | 3900          | Legendary    |
   | 10+   | 1500/level  | N/A           | Legendary    |

3. **희귀도별 시각적 스타일**:
   - **Common** (Lv.1-2): Gray border, 단순 그라디언트
   - **Rare** (Lv.3-4): Blue border, 청색 그라디언트
   - **Epic** (Lv.5-7): Purple border, 보라색 그라디언트 + 글로우
   - **Legendary** (Lv.8+): Gold border, 무지개 그라디언트 + 강한 글로우 + 반짝임 효과

4. **품질 점수 계산**:
   ```typescript
   qualityScore = (feedbackScore * 0.7) + (ragasScore * 0.3)
   // feedbackScore: positive_feedbacks / (positive + negative)
   // ragasScore: avg_faithfulness (0.0-1.0 → 0-100%)
   // ⚠️ 백엔드 피드백 데이터 없으므로 초기에는 avg_faithfulness만 사용
   ```

### 백엔드 호환성 가정
1. **레벨 범위 확장**: 백엔드 `level` (1-5) → 프론트엔드 계산으로 1-10+ 지원
2. **XP 데이터 신뢰**: 백엔드 `current_xp` 필드가 정확하다고 가정
3. **피드백 미구현 대응**: 초기 버전에서는 `avg_faithfulness`를 품질 점수로 사용
4. **실시간 업데이트**: TanStack Query의 polling/refetch를 통해 준실시간 업데이트 구현

### UI/UX 가정
1. **카드 크기**: 고정 너비 280px, 높이는 콘텐츠에 따라 가변
2. **그리드 레이아웃**: 반응형 그리드 (1열: mobile, 2열: tablet, 3-4열: desktop)
3. **애니메이션 시간**: 레벨업 모달 3초, XP 획득 효과 1초
4. **접근성**: ARIA 레이블, 키보드 네비게이션 지원

## 요구사항 (Requirements)

### @REQ:AGENT-CARD-001-R01 카드 렌더링
**WHEN** 에이전트 데이터가 로드되면, **THEN** 시스템은 다음을 포함한 포켓몬 스타일 카드를 렌더링해야 한다:
- 에이전트 이름 (최대 2줄, 말줄임표)
- 현재 레벨 (Lv.X 형식)
- 희귀도 배지 (텍스트 + 아이콘)
- XP 진행 바 (현재 XP / 다음 레벨 XP)
- 스탯 (지식 개수, 대화 횟수, 품질 점수)
- 액션 버튼 (대화, 기록)
- 희귀도별 테두리/배경 스타일

### @REQ:AGENT-CARD-001-R02 희귀도 시스템
**WHEN** 에이전트의 레벨이 변경되면, **THEN** 시스템은 다음 희귀도 매핑을 적용해야 한다:
- Lv.1-2: Common (회색 테두리, `#9CA3AF`)
- Lv.3-4: Rare (청색 테두리, `#3B82F6`)
- Lv.5-7: Epic (보라색 테두리, `#8B5CF6`, 8px blur 글로우)
- Lv.8+: Legendary (금색 테두리, 무지개 그라디언트, 12px blur 글로우, 반짝임 애니메이션)

**IF** 희귀도가 변경되면, **THEN** 시스템은 테두리 그라디언트 전환 애니메이션을 실행해야 한다 (0.5초 ease-in-out).

### @REQ:AGENT-CARD-001-R03 XP 진행 바
**WHEN** 에이전트 카드가 렌더링되면, **THEN** 시스템은 다음을 표시하는 XP 진행 바를 렌더링해야 한다:
- 현재 레벨 내 XP 진행도 (백분율)
- 희귀도별 그라디언트 색상
- XP 텍스트 (예: "450 / 600 XP")
- 부드러운 애니메이션 (0.3초 ease-out)

**WHILE** XP가 증가하는 동안, **THEN** 시스템은 진행 바를 부드럽게 확장해야 한다.

### @REQ:AGENT-CARD-001-R04 스탯 표시
**WHEN** 에이전트 카드가 렌더링되면, **THEN** 시스템은 다음 스탯을 표시해야 한다:
- **지식**: `total_documents` (예: "지식 125개")
- **대화**: `total_queries` (예: "대화 342회")
- **품질**: 계산된 품질 점수 (예: "품질 92%")

**IF** 품질 점수가 90% 이상이면, **THEN** 녹색 색상을 적용해야 한다.
**IF** 품질 점수가 70-89%이면, **THEN** 황색 색상을 적용해야 한다.
**IF** 품질 점수가 70% 미만이면, **THEN** 적색 색상을 적용해야 한다.

### @REQ:AGENT-CARD-001-R05 XP 계산 로직
**WHEN** 사용자가 다음 행동을 완료하면, **THEN** 시스템은 해당 XP를 증가시켜야 한다:
- 대화 완료: +10 XP (플로팅 텍스트 표시)
- 긍정 피드백: +50 XP (플로팅 텍스트 표시)
- RAGAS 보너스 (faithfulness >= 0.9): +100 XP (플로팅 텍스트 + 특수 효과)

**IF** 에이전트에게 피드백 데이터가 없으면, **THEN** 시스템은 `avg_faithfulness`만으로 품질 점수를 계산해야 한다.

### @REQ:AGENT-CARD-001-R06 레벨 계산
**WHEN** 에이전트의 `current_xp`가 변경되면, **THEN** 시스템은 다음 공식으로 레벨을 계산해야 한다:

```typescript
function getLevelFromXP(xp: number): number {
  const thresholds = [0, 100, 300, 600, 1000, 1500, 2100, 2900, 3900];
  for (let i = thresholds.length - 1; i >= 0; i--) {
    if (xp >= thresholds[i]) return i + 1;
  }
  return 1;
}
```

**IF** XP가 레벨업 임계값에 도달하면, **THEN** 시스템은 `useLevelUpNotification` 훅을 트리거해야 한다.

### @REQ:AGENT-CARD-001-R07 레벨업 모달
**WHEN** 에이전트가 레벨업하면, **THEN** 시스템은 다음을 포함한 모달을 표시해야 한다:
- "축하합니다!" 제목
- 새 레벨 (예: "Lv.5 달성!")
- 희귀도 변경 여부 (예: "Rare → Epic 진화!")
- Confetti 애니메이션 (화면 전체, 3초 동안)
- "확인" 버튼

**IF** 희귀도가 변경되었으면, **THEN** 시스템은 진화 효과를 표시해야 한다.

### @REQ:AGENT-CARD-001-R08 애니메이션 효과
**WHEN** 사용자가 XP를 획득하면, **THEN** 시스템은 다음 애니메이션을 표시해야 한다:
- 플로팅 텍스트 (+10 XP, +50 XP 등)
- 텍스트가 위로 이동하며 페이드아웃 (1초)
- framer-motion을 사용한 부드러운 전환

**WHEN** 레벨업이 발생하면, **THEN** 시스템은 다음을 실행해야 한다:
- react-confetti 화면 전체 애니메이션
- 테두리 그라디언트 펄스 효과 (0.5초 × 3회 반복)
- 카드 전체 스케일 애니메이션 (1.0 → 1.05 → 1.0, 0.5초)

### @REQ:AGENT-CARD-001-R09 반응형 그리드
**WHEN** 사용자가 홈페이지를 방문하면, **THEN** 시스템은 반응형 그리드로 에이전트 카드를 표시해야 한다:
- Mobile (<640px): 1열
- Tablet (640-1024px): 2열
- Desktop (1024-1536px): 3열
- Large Desktop (>1536px): 4열

**WHILE** 화면 크기가 변경되는 동안, **THEN** 시스템은 부드럽게 레이아웃을 재조정해야 한다.

### @REQ:AGENT-CARD-001-R10 TanStack Query 통합
**WHEN** 컴포넌트가 마운트되면, **THEN** 시스템은 TanStack Query를 사용하여 에이전트 목록을 조회해야 한다:
- `useQuery({ queryKey: ['agents'], queryFn: fetchAgents })`
- Stale time: 30초
- Refetch on window focus: true
- Polling interval: 60초 (옵션)

**IF** 데이터 로딩 중이면, **THEN** 스켈레톤 카드를 표시해야 한다.
**IF** 에러가 발생하면, **THEN** 에러 메시지를 표시해야 한다.

### @REQ:AGENT-CARD-001-R11 접근성
**WHEN** 에이전트 카드가 렌더링되면, **THEN** 시스템은 다음 접근성 기능을 제공해야 한다:
- ARIA 레이블 (role="article", aria-label="Agent card: {name}")
- 키보드 네비게이션 (Tab, Enter)
- 포커스 표시 (2px 청색 outline)
- 스크린 리더 지원 (progress bar의 aria-valuenow/aria-valuemax)

### @REQ:AGENT-CARD-001-R12 품질 점수 계산
**WHEN** 에이전트 데이터가 로드되면, **THEN** 시스템은 다음 공식으로 품질 점수를 계산해야 한다:

```typescript
// 초기 버전 (피드백 데이터 없음)
qualityScore = avg_faithfulness * 100; // 0.85 → 85%

// 향후 버전 (피드백 데이터 추가 시)
feedbackScore = positive_feedbacks / (positive_feedbacks + negative_feedbacks);
ragasScore = avg_faithfulness;
qualityScore = (feedbackScore * 0.7 + ragasScore * 0.3) * 100;
```

**IF** `avg_faithfulness`가 null이면, **THEN** 품질 점수를 0%로 표시해야 한다.

## 명세 (Specifications)

### 컴포넌트 명세

#### 1. AgentCard.tsx
```typescript
interface AgentCardProps {
  agent: AgentCardData;
  onChatClick?: (agentId: string) => void;
  onHistoryClick?: (agentId: string) => void;
}

export function AgentCard({ agent, onChatClick, onHistoryClick }: AgentCardProps) {
  const rarity = getRarity(agent.level);
  const { current, max } = getXPProgress(agent.current_xp, agent.level);
  const qualityScore = calculateQualityScore(agent);

  return (
    <article
      role="article"
      aria-label={`Agent card: ${agent.name}`}
      className={cn(
        "relative w-[280px] rounded-lg p-4",
        "transition-all duration-300",
        rarityStyles[rarity].border,
        rarityStyles[rarity].shadow
      )}
    >
      {/* 희귀도 배지 */}
      <RarityBadge rarity={rarity} level={agent.level} />

      {/* 에이전트 이름 */}
      <h3 className="text-lg font-bold line-clamp-2">{agent.name}</h3>

      {/* XP 진행 바 */}
      <ProgressBar current={current} max={max} rarity={rarity} />

      {/* 스탯 표시 */}
      <StatDisplay
        knowledge={agent.total_documents}
        chats={agent.total_queries}
        quality={qualityScore}
      />

      {/* 액션 버튼 */}
      <ActionButtons
        onChatClick={() => onChatClick?.(agent.agent_id)}
        onHistoryClick={() => onHistoryClick?.(agent.agent_id)}
      />
    </article>
  );
}
```

#### 2. ProgressBar.tsx
```typescript
interface ProgressBarProps {
  current: number;
  max: number;
  rarity: Rarity;
}

export function ProgressBar({ current, max, rarity }: ProgressBarProps) {
  const percentage = (current / max) * 100;

  return (
    <div className="relative mt-2">
      {/* 배경 바 */}
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        {/* 진행 바 */}
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          className={cn(
            "h-full rounded-full",
            rarityGradients[rarity]
          )}
          role="progressbar"
          aria-valuenow={current}
          aria-valuemax={max}
        />
      </div>

      {/* XP 텍스트 */}
      <p className="text-xs text-gray-600 mt-1">
        {current} / {max} XP
      </p>
    </div>
  );
}
```

#### 3. RarityBadge.tsx
```typescript
interface RarityBadgeProps {
  rarity: Rarity;
  level: number;
}

export function RarityBadge({ rarity, level }: RarityBadgeProps) {
  const icons = {
    common: "⭐",
    rare: "🔹",
    epic: "💎",
    legendary: "👑"
  };

  return (
    <div className={cn(
      "inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold",
      rarityColors[rarity]
    )}>
      <span>{icons[rarity]}</span>
      <span>Lv.{level}</span>
      <span>{rarity.toUpperCase()}</span>
    </div>
  );
}
```

#### 4. LevelUpModal.tsx
```typescript
interface LevelUpModalProps {
  isOpen: boolean;
  onClose: () => void;
  newLevel: number;
  oldRarity: Rarity;
  newRarity: Rarity;
}

export function LevelUpModal({
  isOpen,
  onClose,
  newLevel,
  oldRarity,
  newRarity
}: LevelUpModalProps) {
  const rarityChanged = oldRarity !== newRarity;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Confetti 애니메이션 */}
          <ConfettiAnimation duration={3000} />

          {/* 모달 오버레이 */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          >
            {/* 모달 콘텐츠 */}
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              className="bg-white rounded-lg p-8 max-w-md"
            >
              <h2 className="text-2xl font-bold text-center">🎉 축하합니다!</h2>
              <p className="text-lg text-center mt-4">Lv.{newLevel} 달성!</p>

              {rarityChanged && (
                <p className="text-center mt-2 text-purple-600 font-semibold">
                  {oldRarity.toUpperCase()} → {newRarity.toUpperCase()} 진화!
                </p>
              )}

              <button
                onClick={onClose}
                className="mt-6 w-full py-2 bg-blue-600 text-white rounded-lg"
              >
                확인
              </button>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```

### 유틸리티 함수 명세

#### 1. xpCalculator.ts
```typescript
export const XP_GAINS = {
  CHAT_COMPLETE: 10,
  POSITIVE_FEEDBACK: 50,
  RAGAS_BONUS: 100,
} as const;

export function calculateXPGain(
  action: 'chat' | 'feedback' | 'ragas',
  faithfulness?: number
): number {
  switch (action) {
    case 'chat':
      return XP_GAINS.CHAT_COMPLETE;
    case 'feedback':
      return XP_GAINS.POSITIVE_FEEDBACK;
    case 'ragas':
      return faithfulness && faithfulness >= 0.9
        ? XP_GAINS.RAGAS_BONUS
        : 0;
    default:
      return 0;
  }
}
```

#### 2. levelCalculator.ts
```typescript
const LEVEL_THRESHOLDS = [0, 100, 300, 600, 1000, 1500, 2100, 2900, 3900];

export function getLevelFromXP(xp: number): number {
  for (let i = LEVEL_THRESHOLDS.length - 1; i >= 0; i--) {
    if (xp >= LEVEL_THRESHOLDS[i]) {
      return i + 1;
    }
  }
  return 1;
}

export function getXPProgress(currentXP: number, level: number): {
  current: number;
  max: number;
  percentage: number;
} {
  const levelStart = LEVEL_THRESHOLDS[level - 1] || 0;
  const levelEnd = LEVEL_THRESHOLDS[level] || levelStart + 1500;

  const current = currentXP - levelStart;
  const max = levelEnd - levelStart;
  const percentage = (current / max) * 100;

  return { current, max, percentage };
}
```

#### 3. rarityResolver.ts
```typescript
export type Rarity = 'common' | 'rare' | 'epic' | 'legendary';

export function getRarity(level: number): Rarity {
  if (level >= 8) return 'legendary';
  if (level >= 5) return 'epic';
  if (level >= 3) return 'rare';
  return 'common';
}

export const rarityStyles = {
  common: {
    border: 'border-2 border-gray-400',
    shadow: 'shadow-sm',
  },
  rare: {
    border: 'border-2 border-blue-500',
    shadow: 'shadow-md shadow-blue-500/50',
  },
  epic: {
    border: 'border-2 border-purple-500',
    shadow: 'shadow-lg shadow-purple-500/50',
  },
  legendary: {
    border: 'border-4 border-transparent bg-gradient-to-r from-yellow-400 via-pink-500 to-purple-600 bg-clip-padding',
    shadow: 'shadow-xl shadow-yellow-500/50 animate-pulse',
  },
} as const;
```

#### 4. qualityScoreCalculator.ts
```typescript
interface QualityScoreInput {
  avg_faithfulness: number | null;
  positive_feedbacks?: number;
  negative_feedbacks?: number;
}

export function calculateQualityScore(input: QualityScoreInput): number {
  const { avg_faithfulness, positive_feedbacks, negative_feedbacks } = input;

  // 피드백 데이터가 있는 경우
  if (
    positive_feedbacks !== undefined &&
    negative_feedbacks !== undefined &&
    (positive_feedbacks + negative_feedbacks) > 0
  ) {
    const feedbackScore = positive_feedbacks / (positive_feedbacks + negative_feedbacks);
    const ragasScore = avg_faithfulness ?? 0;
    return Math.round((feedbackScore * 0.7 + ragasScore * 0.3) * 100);
  }

  // 피드백 데이터가 없는 경우
  if (avg_faithfulness !== null) {
    return Math.round(avg_faithfulness * 100);
  }

  return 0;
}

export function getQualityColor(score: number): string {
  if (score >= 90) return 'text-green-600';
  if (score >= 70) return 'text-yellow-600';
  return 'text-red-600';
}
```

### 타입 정의

```typescript
// lib/api/types.ts에 추가
export interface AgentCardData {
  agent_id: string;
  name: string;
  level: number;
  current_xp: number;
  total_documents: number;
  total_queries: number;
  avg_faithfulness: number | null;
  coverage_percent: number;
  created_at: string;
  updated_at: string;
}

export const AgentCardDataSchema = z.object({
  agent_id: z.string(),
  name: z.string(),
  level: z.number().min(1),
  current_xp: z.number().min(0),
  total_documents: z.number().min(0),
  total_queries: z.number().min(0),
  avg_faithfulness: z.number().min(0).max(1).nullable(),
  coverage_percent: z.number().min(0).max(100),
  created_at: z.string(),
  updated_at: z.string(),
});

export type AgentCardData = z.infer<typeof AgentCardDataSchema>;
```

## 추적성 (Traceability)

### 연관 SPEC
- `SPEC-AGENT-GROWTH-001`: 백엔드 에이전트 테이블 스키마 (@CODE:AGENT-GROWTH-001:SCHEMA)
- `SPEC-AGENT-GROWTH-002`: 백엔드 API 엔드포인트 (@CODE:AGENT-GROWTH-002:SCHEMA)
- `SPEC-AGENT-GROWTH-003`: 백엔드 게임 로직 (@CODE:AGENT-GROWTH-003:LOGIC)
- `SPEC-FRONTEND-INIT-001`: 프론트엔드 초기화 (@CODE:FRONTEND-INIT-001)

### TAG 체인
```
@SPEC:AGENT-CARD-001
  └─> @CODE:AGENT-CARD-001:COMPONENT (AgentCard.tsx)
  └─> @CODE:AGENT-CARD-001:PROGRESS (ProgressBar.tsx)
  └─> @CODE:AGENT-CARD-001:RARITY (RarityBadge.tsx)
  └─> @CODE:AGENT-CARD-001:STATS (StatDisplay.tsx)
  └─> @CODE:AGENT-CARD-001:LEVELUP (LevelUpModal.tsx)
  └─> @CODE:AGENT-CARD-001:XP-CALC (xpCalculator.ts)
  └─> @CODE:AGENT-CARD-001:LEVEL-CALC (levelCalculator.ts)
  └─> @CODE:AGENT-CARD-001:RARITY-CALC (rarityResolver.ts)
  └─> @CODE:AGENT-CARD-001:QUALITY-CALC (qualityScoreCalculator.ts)
  └─> @TEST:AGENT-CARD-001:COMPONENT
  └─> @TEST:AGENT-CARD-001:UTILS
```

## 제약사항 (Constraints)

### 기술적 제약
1. **백엔드 레벨 제한**: 백엔드 DB는 `level` 1-5만 지원 → 프론트엔드 계산 필요
2. **피드백 데이터 없음**: 초기 버전에서는 `avg_faithfulness`만 사용
3. **실시간 업데이트 없음**: WebSocket 미구현 → TanStack Query polling 사용
4. **XP 증가 API 없음**: 클라이언트 사이드 계산 또는 향후 백엔드 추가 필요

### 성능 제약
1. **카드 렌더링**: 최대 100개 카드까지 지원 (가상 스크롤 미구현)
2. **애니메이션**: 동시 10개 이상 레벨업 시 성능 저하 가능
3. **Polling 간격**: 60초 (너무 짧으면 서버 부하)

### 디자인 제약
1. **카드 크기 고정**: 280px (반응형 조정 불가)
2. **그리드 간격**: 16px (Tailwind gap-4)
3. **폰트**: 시스템 기본 폰트 (커스텀 폰트 미사용)

## 향후 확장성

### Phase 2 기능 (백엔드 추가 필요)
1. **피드백 시스템**: `positive_feedbacks`, `negative_feedbacks` 컬럼 추가
2. **XP 증가 API**: `POST /agents/{id}/xp` 엔드포인트
3. **레벨업 알림**: WebSocket 실시간 알림

### Phase 3 기능 (고급 UI)
1. **가상 스크롤**: 1000+ 카드 지원
2. **필터링/정렬**: 레벨, 희귀도, 품질별 필터
3. **카드 상세 모달**: 클릭 시 상세 정보 표시
4. **비교 모드**: 여러 에이전트 비교

---

**작성일**: 2025-10-30
**작성자**: @Alfred
**버전**: 0.0.1 (초안)
