---
id: SPEC-FRONTEND-MIGRATION-001-PLAN
version: 1.0.0
status: draft
created: 2025-11-21
updated: 2025-11-21
author: "@spec-builder"
parent_spec: SPEC-FRONTEND-MIGRATION-001
---

# @SPEC:FRONTEND-MIGRATION-001 구현 계획

> **English**: Implementation Plan for Vite to Next.js Migration

## HISTORY

### v1.0.0 (2025-11-21)

- **INITIAL**: 구현 계획 초안 작성
- **AUTHOR**: @spec-builder
- **SECTIONS**: 마일스톤, 기술 접근법, 아키텍처 설계, 리스크 관리

---

## 1. 마일스톤 (우선순위 기반)

### Phase 1: 의존성 설치 및 유틸리티 마이그레이션

**우선순위**: Critical (최우선)
**의존성**: 없음

#### 1.1 의존성 설치

```bash
cd apps/frontend
npm install framer-motion react-confetti react-window @xyflow/react zustand dagre d3-force
npm install -D @types/react-window @types/dagre @types/d3-force
```

#### 1.2 유틸리티 마이그레이션 (4개 파일)

| 파일 | 소스 | 타겟 | 변경 사항 |
|------|------|------|----------|
| levelCalculator.ts | frontend/src/lib/utils/ | apps/frontend/lib/utils/ | 경로만 변경 |
| xpCalculator.ts | frontend/src/lib/utils/ | apps/frontend/lib/utils/ | 경로만 변경 |
| rarityResolver.ts | frontend/src/lib/utils/ | apps/frontend/lib/utils/ | 경로만 변경 |
| qualityScoreCalculator.ts | frontend/src/lib/utils/ | apps/frontend/lib/utils/ | 경로만 변경 |

#### 1.3 테스트 마이그레이션

| 테스트 파일 | 소스 | 타겟 |
|------------|------|------|
| levelCalculator.test.ts | frontend/src/lib/utils/__tests__/ | apps/frontend/lib/utils/__tests__/ |
| xpCalculator.test.ts | frontend/src/lib/utils/__tests__/ | apps/frontend/lib/utils/__tests__/ |
| rarityResolver.test.ts | frontend/src/lib/utils/__tests__/ | apps/frontend/lib/utils/__tests__/ |
| qualityScoreCalculator.test.ts | frontend/src/lib/utils/__tests__/ | apps/frontend/lib/utils/__tests__/ |

---

### Phase 2: Common 컴포넌트 마이그레이션

**우선순위**: High
**의존성**: Phase 1

#### 2.1 컴포넌트 마이그레이션 (3개)

| 컴포넌트 | 변경 사항 |
|----------|----------|
| VirtualList.tsx | "use client" 추가, react-window import 유지 |
| LoadingSpinner.tsx | 스타일 조정 (Tailwind v4 -> v3) |
| ErrorBoundary.tsx | "use client" 추가 (클래스 컴포넌트) |

#### 2.2 Tailwind CSS 변환 가이드

```tsx
// Vite (Tailwind v4)
<div className="bg-slate-900/80 backdrop-blur-sm">

// Next.js (Tailwind v3) - 동일 (호환)
<div className="bg-slate-900/80 backdrop-blur-sm">
```

주요 변환 항목:
- `@layer` 지시어: 동일하게 지원됨
- CSS 변수: Tailwind 설정에서 정의 필요
- 커스텀 색상: tailwind.config.ts에 추가

---

### Phase 3: Agent Card 컴포넌트 마이그레이션

**우선순위**: High
**의존성**: Phase 1, Phase 2

#### 3.1 기본 카드 컴포넌트 (4개)

| 컴포넌트 | 변경 사항 |
|----------|----------|
| AgentCard.tsx | "use client", framer-motion 호환성 확인 |
| AgentCardAvatar.tsx | 이미지 컴포넌트 Next.js Image로 변환 고려 |
| ActionButtons.tsx | "use client" |
| StatDisplay.tsx | "use client", 스타일 조정 |

#### 3.2 XP/Level 컴포넌트 (7개)

| 컴포넌트 | 변경 사항 |
|----------|----------|
| ProgressBar.tsx | "use client", framer-motion 애니메이션 |
| RarityBadge.tsx | "use client" |
| LevelUpModal.tsx | "use client", react-confetti dynamic import |
| LevelUpTimeline.tsx | "use client" |
| XPAwardButton.tsx | "use client" |
| XPGrowthChart.tsx | "use client", recharts 버전 호환성 |
| CoverageChart.tsx | "use client", recharts 버전 호환성 |
| ChartContainer.tsx | "use client" |

#### 3.3 framer-motion 호환성 처리

```tsx
// 파일 상단
"use client";

import { motion, AnimatePresence } from "framer-motion";

// 동일하게 사용 가능
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  exit={{ opacity: 0 }}
>
  {/* content */}
</motion.div>
```

#### 3.4 react-confetti Dynamic Import

```tsx
"use client";

import dynamic from "next/dynamic";

const Confetti = dynamic(() => import("react-confetti"), {
  ssr: false,
  loading: () => null,
});

export function LevelUpModal({ show, onClose }: Props) {
  return (
    <AnimatePresence>
      {show && (
        <>
          <Confetti numberOfPieces={200} recycle={false} />
          {/* modal content */}
        </>
      )}
    </AnimatePresence>
  );
}
```

---

### Phase 4: Taxonomy 컴포넌트 마이그레이션

**우선순위**: Medium
**의존성**: Phase 1, Phase 2

#### 4.1 Zustand Store 마이그레이션

```tsx
// apps/frontend/stores/useTaxonomyStore.ts
"use client";

import { create } from "zustand";

interface TaxonomyState {
  selectedNode: string | null;
  expandedNodes: Set<string>;
  // ... 기타 상태
}

export const useTaxonomyStore = create<TaxonomyState>((set) => ({
  selectedNode: null,
  expandedNodes: new Set(),
  // ... 기타 액션
}));
```

#### 4.2 @xyflow/react Dynamic Import

```tsx
"use client";

import dynamic from "next/dynamic";
import type { Node, Edge } from "@xyflow/react";

const ReactFlow = dynamic(
  () => import("@xyflow/react").then((mod) => mod.ReactFlow),
  { ssr: false }
);

const Background = dynamic(
  () => import("@xyflow/react").then((mod) => mod.Background),
  { ssr: false }
);

const Controls = dynamic(
  () => import("@xyflow/react").then((mod) => mod.Controls),
  { ssr: false }
);
```

#### 4.3 Taxonomy 컴포넌트 (7개)

| 컴포넌트 | 변경 사항 |
|----------|----------|
| TaxonomyTreeView.tsx | "use client", @xyflow/react dynamic import |
| TaxonomyNode.tsx | "use client", memo 유지 |
| TaxonomyEdge.tsx | "use client" |
| TaxonomyDetailPanel.tsx | "use client", framer-motion |
| TaxonomySearchFilter.tsx | "use client" |
| TaxonomyLayoutToggle.tsx | "use client" |
| KeyboardShortcutsModal.tsx | "use client", Dialog 컴포넌트 통합 |

#### 4.4 React Flow CSS Import

```tsx
// apps/frontend/app/(dashboard)/taxonomy/page.tsx
import "@xyflow/react/dist/style.css";
```

또는 `app/globals.css`에 추가:

```css
@import "@xyflow/react/dist/style.css";
```

---

### Phase 5: Home 컴포넌트 및 페이지 통합

**우선순위**: Medium
**의존성**: Phase 3

#### 5.1 Home 컴포넌트 (2개)

| 컴포넌트 | 변경 사항 |
|----------|----------|
| StatCard.tsx | "use client" |
| RecommendationPanel.tsx | "use client", AgentCard 의존성 |

#### 5.2 Agents 페이지 업데이트

```tsx
// apps/frontend/app/(dashboard)/agents/page.tsx
import { AgentCard } from "@/components/agent-card/AgentCard";
import { VirtualList } from "@/components/common/VirtualList";

export default function AgentsPage() {
  // 기존 에이전트 목록에 AgentCard 통합
}
```

#### 5.3 대시보드 홈 페이지 업데이트

```tsx
// apps/frontend/app/(dashboard)/page.tsx
import { StatCard } from "@/components/home/StatCard";
import { RecommendationPanel } from "@/components/home/RecommendationPanel";

export default function DashboardPage() {
  // StatCard 및 RecommendationPanel 통합
}
```

---

### Phase 6: 통합 테스트 및 최적화

**우선순위**: High
**의존성**: Phase 1-5

#### 6.1 테스트 마이그레이션

Vitest -> Jest 변환 필요 (Next.js 표준):

```tsx
// 테스트 파일 변환 예시
// From: import { describe, it, expect, vi } from 'vitest';
// To: (Jest는 전역 import 불필요)

describe("AgentCard", () => {
  it("should render correctly", () => {
    // 테스트 코드 (대부분 호환)
  });
});
```

#### 6.2 번들 분석

```bash
cd apps/frontend
npm run build
# Next.js 빌드 출력에서 번들 크기 확인
```

#### 6.3 성능 최적화

- 코드 스플리팅: Dynamic import 활용
- 이미지 최적화: Next.js Image 컴포넌트 사용
- 폰트 최적화: next/font 활용

---

## 2. 기술 접근법

### 2.1 "use client" 지시어 전략

| 컴포넌트 유형 | "use client" 필요 |
|--------------|------------------|
| 상태 사용 (useState, useReducer) | Yes |
| 이벤트 핸들러 | Yes |
| 라이프사이클 (useEffect) | Yes |
| Context 소비 (useContext) | Yes |
| 애니메이션 (framer-motion) | Yes |
| 차트 (recharts) | Yes |
| 그래프 (@xyflow/react) | Yes |
| 순수 UI (props only) | No |

### 2.2 Import Path 전략

```tsx
// 절대 경로 사용 (tsconfig.json의 paths 설정 활용)
import { AgentCard } from "@/components/agent-card/AgentCard";
import { levelCalculator } from "@/lib/utils/levelCalculator";
import { useTaxonomyStore } from "@/stores/useTaxonomyStore";
```

### 2.3 타입 정의 통합

```tsx
// apps/frontend/types/agent.ts
export interface Agent {
  id: string;
  name: string;
  level: number;
  xp: number;
  rarity: "common" | "uncommon" | "rare" | "epic" | "legendary";
  // ...
}
```

---

## 3. 아키텍처 설계 방향

### 3.1 컴포넌트 계층 구조

```
apps/frontend/
├── components/
│   ├── ui/                 # 기존 shadcn/ui 컴포넌트
│   ├── agent-card/         # NEW: Agent Card 시스템
│   ├── agent-detail/       # NEW: Agent 상세 정보
│   ├── taxonomy/           # NEW: Taxonomy 시각화
│   ├── history/            # NEW: 히스토리 차트
│   ├── common/             # NEW: 공통 컴포넌트
│   ├── home/               # NEW: 홈 대시보드
│   └── charts/             # 기존 차트 컴포넌트
├── lib/
│   ├── api/                # 기존 API 클라이언트
│   └── utils/              # 기존 + NEW 유틸리티
├── stores/                 # NEW: Zustand 스토어
└── app/
    └── (dashboard)/
        ├── agents/         # Agent Card 통합
        ├── taxonomy/       # Taxonomy 트리 통합
        └── page.tsx        # 홈 대시보드 통합
```

### 3.2 상태 관리 전략

```
React Query (서버 상태)     Zustand (클라이언트 상태)
├── 에이전트 목록 조회       ├── 택소노미 UI 상태
├── 에이전트 상세 조회       ├── 선택된 노드
├── XP 수여 뮤테이션        ├── 확장된 노드 목록
└── 택소노미 데이터         └── 검색 필터 상태
```

---

## 4. 리스크 및 대응 계획

### 4.1 기술적 리스크

| 리스크 | 발생 가능성 | 영향도 | 대응 전략 |
|--------|------------|--------|----------|
| React 19 -> 18 호환성 문제 | Low | High | 기능별 테스트, 폴리필 검토 |
| Tailwind v4 -> v3 스타일 깨짐 | Medium | Medium | 컴포넌트별 시각적 검증 |
| SSR 하이드레이션 불일치 | Medium | High | Dynamic import, "use client" |
| recharts 버전 충돌 | Low | Medium | 버전 통일 (3.x) |

### 4.2 의존성 충돌 대응

```json
// package.json 의존성 버전 관리
{
  "dependencies": {
    "framer-motion": "^11.18.2",
    "react-confetti": "^6.4.0",
    "react-window": "^1.8.11",
    "@xyflow/react": "^12.9.0",
    "zustand": "^5.0.8",
    "recharts": "^3.2.1"  // 기존 버전 유지
  },
  "resolutions": {
    // 필요시 의존성 해결
  }
}
```

### 4.3 롤백 계획

1. **Git 분기 전략**: `feature/SPEC-FRONTEND-MIGRATION-001` 브랜치에서 작업
2. **단계별 커밋**: Phase별 커밋으로 롤백 지점 확보
3. **Vite 프론트엔드 보존**: 마이그레이션 완료 전까지 frontend/ 유지

---

## 5. 전문가 상담 권장

### 5.1 frontend-expert 상담 권장

이 SPEC은 복잡한 컴포넌트 마이그레이션을 포함합니다:

- framer-motion + Next.js App Router 통합
- @xyflow/react SSR 처리
- 대규모 컴포넌트 구조 설계

**권장 사항**: `/alfred:2-run` 실행 전 frontend-expert 에이전트와 상담하여 아키텍처 리뷰를 받으시기 바랍니다.

---

## SUMMARY (English)

The implementation plan follows a 6-phase approach prioritized by dependencies. Phase 1 installs dependencies and migrates 4 utility functions. Phase 2 migrates 3 common components with SSR considerations. Phase 3 handles 11 Agent Card components with framer-motion and react-confetti integration. Phase 4 addresses 8 Taxonomy components including @xyflow/react dynamic imports and Zustand store setup. Phase 5 integrates 2 Home components and updates page layouts. Phase 6 performs integration testing and bundle optimization.

Key technical strategies include using "use client" directives for interactive components, dynamic imports for SSR-incompatible libraries, and maintaining compatibility between Tailwind CSS versions. Risk mitigation includes Git branching for rollback capability and phase-by-phase commits.

Expert consultation with frontend-expert agent is recommended before implementation to review the architecture decisions, especially regarding framer-motion SSR handling and @xyflow/react integration patterns.

---

_이 계획은 `/alfred:2-run SPEC-FRONTEND-MIGRATION-001` 실행 시 구현 가이드로 사용됩니다._
