# React + TypeScript + Vite

Dynamic Taxonomy RAG System - Frontend Application

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

---

## @DOC:AGENT-CARD-001-README

# Pokemon-Style Agent Card System

에이전트 성장 시스템을 Pokemon 카드 스타일로 시각화한 게임화 UI/UX 기능입니다.

### 주요 기능

- **XP/레벨 시스템**: 대화, 피드백, RAGAS 평가를 통한 경험치 획득 및 레벨업 (1-10+ levels)
- **4단계 희귀도**: Common → Rare → Epic → Legendary 진화 시스템
- **실시간 데이터**: TanStack Query를 활용한 에이전트 데이터 페칭
- **레벨업 애니메이션**: framer-motion + react-confetti를 이용한 축하 효과
- **반응형 그리드**: 1/2/3/4 컬럼 레이아웃 (모바일, 태블릿, 데스크톱)

### Quick Start

#### 1. 에이전트 목록 조회

```tsx
import { useAgents } from '@/hooks/useAgents'
import { AgentCard } from '@/components/agent-card/AgentCard'

export function AgentList() {
  const { data: agents, isLoading } = useAgents()

  if (isLoading) return <div>Loading...</div>

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {agents?.map((agent) => (
        <AgentCard
          key={agent.agent_id}
          agent={agent}
          onView={() => console.log('View', agent.agent_id)}
          onDelete={() => console.log('Delete', agent.agent_id)}
        />
      ))}
    </div>
  )
}
```

#### 2. XP 계산

```typescript
import { calculateXp } from '@/lib/utils/xpCalculator'

// 단일 행동
const chatXp = calculateXp('CHAT')        // 10 XP
const feedbackXp = calculateXp('FEEDBACK') // 50 XP
const ragasXp = calculateXp('RAGAS')      // 100 XP

// 다중 행동
const totalXp = calculateXp(['CHAT', 'FEEDBACK', 'RAGAS']) // 160 XP
```

#### 3. 레벨 및 희귀도 계산

```typescript
import { calculateLevel, getNextLevelXp } from '@/lib/utils/levelCalculator'
import { resolveRarity } from '@/lib/utils/rarityResolver'

const currentXp = 1500
const level = calculateLevel(currentXp)      // 5
const rarity = resolveRarity(level)          // 'Rare'
const nextLevelXp = getNextLevelXp(level)    // 2000
```

#### 4. 품질 점수 계산

```typescript
import { calculateQualityScore } from '@/lib/utils/qualityScoreCalculator'

const ragasScore = 0.92 // RAGAS faithfulness (0.0-1.0)
const qualityScore = calculateQualityScore(ragasScore) // 92%
```

### 레벨 진행 테이블

| Level | Required XP | Rarity | Border Color |
|-------|-------------|--------|--------------|
| 1 | 0 | Common | Gray |
| 2 | 100 | Common | Gray |
| 3 | 250 | Common | Gray |
| 4 | 500 | Rare | Blue |
| 5 | 1000 | Rare | Blue |
| 6 | 2000 | Rare | Blue |
| 7 | 3500 | Epic | Purple + Glow |
| 8 | 5500 | Epic | Purple + Glow |
| 9 | 8000 | Legendary | Gold + Rainbow |
| 10 | 11000 | Legendary | Gold + Rainbow |

### 상세 문서

- **[COMPONENTS.md](./docs/COMPONENTS.md)** - 컴포넌트 API 문서 (AgentCard, RarityBadge, ProgressBar 등)
- **[UTILITIES.md](./docs/UTILITIES.md)** - 유틸리티 함수 문서 (XP, 레벨, 희귀도 계산)
- **[TESTING.md](./docs/TESTING.md)** - 테스트 가이드 (148/148 통과, 100% 커버리지)

### 기술 스택

- React 19.1.1
- TypeScript 5.9.3
- Tailwind CSS 4.1.16
- TanStack Query 5.90.5
- framer-motion 11.18.2
- react-confetti 6.4.0
- Vitest 2.1.9 + React Testing Library 16.3.0

### 디렉토리 구조

```
frontend/src/
├── components/
│   └── agent-card/              # 에이전트 카드 컴포넌트
│       ├── AgentCard.tsx        # 메인 카드
│       ├── RarityBadge.tsx      # 희귀도 배지
│       ├── ProgressBar.tsx      # XP 진행 바
│       ├── StatDisplay.tsx      # 스탯 표시
│       ├── ActionButtons.tsx    # 액션 버튼
│       ├── LevelUpModal.tsx     # 레벨업 모달
│       └── __tests__/           # 컴포넌트 테스트
├── lib/
│   └── utils/                   # 유틸리티 함수
│       ├── xpCalculator.ts      # XP 계산
│       ├── levelCalculator.ts   # 레벨 계산
│       ├── rarityResolver.ts    # 희귀도 결정
│       ├── qualityScoreCalculator.ts # 품질 점수
│       └── __tests__/           # 유틸리티 테스트
├── hooks/
│   └── useAgents.ts             # 에이전트 데이터 훅
└── app/
    └── page.tsx                 # 홈 페이지 (그리드 레이아웃)
```

### SPEC 참조

- **원본 명세**: `.moai/specs/SPEC-AGENT-CARD-001/spec.md`
- **버전**: v0.1.0 (구현 완료)
- **상태**: completed
- **TAG 체인**: @SPEC → @CODE (13) → @TEST (14) → @DOC (4)

---

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
