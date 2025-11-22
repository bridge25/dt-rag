---
id: SPEC-FRONTEND-MIGRATION-001
version: 1.0.0
status: draft
created: 2025-11-21
updated: 2025-11-21
author: "@spec-builder"
priority: high
domain: frontend
tags: [migration, nextjs, vite, agent-card, taxonomy]
---

# @SPEC:FRONTEND-MIGRATION-001 Vite Agent Card 시스템 Next.js 마이그레이션

> **English**: Migration of Vite Agent Card System to Next.js

## HISTORY

### v1.0.0 (2025-11-21)

- **INITIAL**: SPEC 문서 초안 작성
- **AUTHOR**: @spec-builder
- **SECTIONS**: 환경분석, 요구사항, EARS 사양, 마이그레이션 계획

---

## 1. 환경 분석 (Environment)

### 1.1 현재 시스템 구조

현재 프로젝트에는 **두 개의 독립적인 프론트엔드**가 존재합니다:

#### Next.js 프론트엔드 (apps/frontend/)

- **배포 URL**: dt-rag-frontend.vercel.app
- **프레임워크**: Next.js 14.2.10 + React 18
- **스타일링**: Tailwind CSS 3.4.1 + tailwindcss-animate
- **UI 라이브러리**: Radix UI (@radix-ui/react-*)
- **상태관리**: @tanstack/react-query 5.0.0
- **주요 기능**:
  - RAG 검색 (Search)
  - 문서 업로드 (Documents)
  - 택소노미 관리 (Taxonomy)
  - 모니터링 (Monitoring)
  - 파이프라인 (Pipeline)
  - HITL (Human-in-the-Loop)

#### Vite 프론트엔드 (frontend/)

- **배포 URL**: frontend-one-swart-20.vercel.app
- **프레임워크**: Vite 7.1.7 + React 19.1.1
- **스타일링**: Tailwind CSS 4.1.16
- **애니메이션**: framer-motion 11.18.2
- **시각화**: @xyflow/react 12.9.0, recharts 2.15.4
- **상태관리**: zustand 5.0.8
- **가상화**: react-window 1.8.11
- **주요 기능**:
  - Agent Card 시스템 (Pokemon 스타일 카드)
  - XP/레벨 시스템
  - 희귀도 시스템
  - 택소노미 트리 시각화

### 1.2 마이그레이션 대상 (25개 컴포넌트 + 4개 유틸리티)

#### Agent Card 컴포넌트 (4개)

| 컴포넌트 | 위치 | 설명 |
|----------|------|------|
| AgentCard | components/agent-card/ | 메인 에이전트 카드 |
| AgentCardAvatar | components/agent-card/ | 에이전트 아바타 |
| AgentDetailCard | components/agent-detail/ | 상세 정보 카드 |
| ActionButtons | components/agent-card/ | 액션 버튼 그룹 |

#### XP/Level 컴포넌트 (7개)

| 컴포넌트 | 위치 | 설명 |
|----------|------|------|
| ProgressBar | components/agent-card/ | 진행률 표시 바 |
| RarityBadge | components/agent-card/ | 희귀도 뱃지 |
| StatDisplay | components/agent-card/ | 스탯 표시 |
| LevelUpModal | components/agent-card/ | 레벨업 모달 |
| LevelUpTimeline | components/agent-detail/ | 레벨업 타임라인 |
| XPAwardButton | components/agent-detail/ | XP 수여 버튼 |
| XPGrowthChart | components/history/ | XP 성장 차트 |

#### Chart 컴포넌트 (2개)

| 컴포넌트 | 위치 | 설명 |
|----------|------|------|
| CoverageChart | components/history/ | 커버리지 차트 |
| ChartContainer | components/history/ | 차트 컨테이너 |

#### Taxonomy 컴포넌트 (7개)

| 컴포넌트 | 위치 | 설명 |
|----------|------|------|
| TaxonomyTreeView | components/taxonomy/ | 트리 뷰 메인 |
| TaxonomyNode | components/taxonomy/ | 트리 노드 |
| TaxonomyEdge | components/taxonomy/ | 트리 엣지 |
| TaxonomyDetailPanel | components/taxonomy/ | 상세 패널 |
| TaxonomySearchFilter | components/taxonomy/ | 검색 필터 |
| TaxonomyLayoutToggle | components/taxonomy/ | 레이아웃 토글 |
| KeyboardShortcutsModal | components/taxonomy/ | 키보드 단축키 모달 |

#### Common 컴포넌트 (3개)

| 컴포넌트 | 위치 | 설명 |
|----------|------|------|
| VirtualList | components/common/ | 가상화 리스트 |
| LoadingSpinner | components/common/ | 로딩 스피너 |
| ErrorBoundary | components/agent-card/ | 에러 경계 |

#### Home 컴포넌트 (2개)

| 컴포넌트 | 위치 | 설명 |
|----------|------|------|
| StatCard | components/home/ | 통계 카드 |
| RecommendationPanel | components/home/ | 추천 패널 |

#### 유틸리티 (4개)

| 유틸리티 | 위치 | 설명 |
|----------|------|------|
| levelCalculator.ts | lib/utils/ | 레벨 계산 |
| xpCalculator.ts | lib/utils/ | XP 계산 |
| rarityResolver.ts | lib/utils/ | 희귀도 결정 |
| qualityScoreCalculator.ts | lib/utils/ | 품질 점수 계산 |

#### Zustand Store (1개)

| Store | 위치 | 설명 |
|-------|------|------|
| useTaxonomyStore | stores/ | 택소노미 상태 관리 |

### 1.3 추가 의존성

| 패키지 | 버전 | 용도 |
|--------|------|------|
| framer-motion | ^11.18.2 | 애니메이션 |
| react-confetti | ^6.4.0 | 레벨업 효과 |
| react-window | ^1.8.11 | 가상화 리스트 |
| @xyflow/react | ^12.9.0 | 택소노미 그래프 |
| zustand | ^5.0.8 | 상태관리 |
| dagre | ^0.8.5 | 그래프 레이아웃 |
| d3-force | ^3.0.0 | 물리 시뮬레이션 |

---

## 2. 가정 (Assumptions)

### 2.1 기술적 가정

- Next.js 14는 React 18 기반이며, Vite의 React 19 컴포넌트는 React 18과 호환됨
- Tailwind CSS 4.x 문법은 3.x로 변환 가능함 (주로 @apply → 유틸리티 클래스)
- framer-motion은 Next.js App Router와 호환됨 ("use client" 지시어 필요)
- @xyflow/react는 Next.js SSR 환경에서 dynamic import로 처리 가능함

### 2.2 비즈니스 가정

- 마이그레이션 완료 후 Vite 프론트엔드(frontend/)는 아카이브됨
- 단일 Next.js 앱(apps/frontend/)으로 통합하여 유지보수 비용 절감
- 기존 Vite 프론트엔드의 기능과 UX는 100% 보존됨

### 2.3 배포 가정

- 마이그레이션 후 dt-rag-frontend.vercel.app에서 모든 기능 제공
- frontend-one-swart-20.vercel.app은 폐기 예정

---

## 3. EARS 요구사항 (Requirements)

### 3.1 Ubiquitous Requirements (기본 요구사항)

- **[REQ-U-001]** 시스템은 Agent Card 표시 기능을 제공해야 한다.
- **[REQ-U-002]** 시스템은 XP/레벨 시스템 기능을 제공해야 한다.
- **[REQ-U-003]** 시스템은 택소노미 트리 시각화 기능을 제공해야 한다.
- **[REQ-U-004]** 시스템은 가상화 리스트 렌더링 기능을 제공해야 한다.
- **[REQ-U-005]** 시스템은 레벨업 애니메이션 효과를 제공해야 한다.

### 3.2 Event-driven Requirements (이벤트 기반 요구사항)

- **[REQ-E-001]** WHEN 에이전트가 XP를 획득하면, 시스템은 경험치 바를 애니메이션으로 업데이트해야 한다.
- **[REQ-E-002]** WHEN 에이전트가 레벨업하면, 시스템은 LevelUpModal과 confetti 효과를 표시해야 한다.
- **[REQ-E-003]** WHEN 사용자가 택소노미 노드를 클릭하면, 시스템은 상세 패널을 표시해야 한다.
- **[REQ-E-004]** WHEN 사용자가 검색어를 입력하면, 시스템은 실시간으로 택소노미를 필터링해야 한다.
- **[REQ-E-005]** WHEN 컴포넌트에서 에러가 발생하면, ErrorBoundary가 폴백 UI를 표시해야 한다.

### 3.3 State-driven Requirements (상태 기반 요구사항)

- **[REQ-S-001]** WHILE 에이전트 목록이 로딩 중이면, 시스템은 LoadingSpinner를 표시해야 한다.
- **[REQ-S-002]** WHILE 택소노미 트리가 확장 상태이면, 시스템은 자식 노드를 표시해야 한다.
- **[REQ-S-003]** WHILE 대량 데이터를 표시 중이면, 시스템은 가상화 리스트를 사용해야 한다.

### 3.4 Optional Features (선택적 기능)

- **[REQ-O-001]** WHERE 사용자가 다크 모드를 선택하면, 시스템은 카드 스타일을 조정할 수 있다.
- **[REQ-O-002]** WHERE 키보드 접근성이 필요하면, 시스템은 키보드 단축키를 제공할 수 있다.
- **[REQ-O-003]** WHERE 모바일 환경이면, 시스템은 반응형 레이아웃을 제공할 수 있다.

### 3.5 Constraints (제약사항)

- **[REQ-C-001]** IF Tailwind CSS 버전이 3.x이면, 시스템은 4.x 문법을 3.x로 변환해야 한다.
- **[REQ-C-002]** IF SSR 환경이면, 시스템은 클라이언트 전용 컴포넌트에 "use client"를 적용해야 한다.
- **[REQ-C-003]** 모든 마이그레이션된 컴포넌트는 기존 테스트를 통과해야 한다.
- **[REQ-C-004]** 번들 크기 증가는 기존 대비 30% 이내여야 한다.

---

## 4. 사양 (Specifications)

### 4.1 디렉토리 구조

```
apps/frontend/
├── components/
│   ├── agent-card/              # NEW: Agent Card 컴포넌트
│   │   ├── AgentCard.tsx
│   │   ├── AgentCardAvatar.tsx
│   │   ├── ActionButtons.tsx
│   │   ├── ProgressBar.tsx
│   │   ├── RarityBadge.tsx
│   │   ├── StatDisplay.tsx
│   │   ├── LevelUpModal.tsx
│   │   └── ErrorBoundary.tsx
│   ├── agent-detail/            # NEW: Agent Detail 컴포넌트
│   │   ├── AgentDetailCard.tsx
│   │   ├── LevelUpTimeline.tsx
│   │   └── XPAwardButton.tsx
│   ├── history/                 # NEW: History 차트 컴포넌트
│   │   ├── CoverageChart.tsx
│   │   ├── ChartContainer.tsx
│   │   └── XPGrowthChart.tsx
│   ├── taxonomy/                # NEW: Taxonomy 컴포넌트
│   │   ├── TaxonomyTreeView.tsx
│   │   ├── TaxonomyNode.tsx
│   │   ├── TaxonomyEdge.tsx
│   │   ├── TaxonomyDetailPanel.tsx
│   │   ├── TaxonomySearchFilter.tsx
│   │   ├── TaxonomyLayoutToggle.tsx
│   │   └── KeyboardShortcutsModal.tsx
│   ├── common/                  # NEW: Common 컴포넌트
│   │   ├── VirtualList.tsx
│   │   └── LoadingSpinner.tsx
│   └── home/                    # NEW: Home 컴포넌트
│       ├── StatCard.tsx
│       └── RecommendationPanel.tsx
├── lib/
│   └── utils/                   # NEW: 유틸리티 함수
│       ├── levelCalculator.ts
│       ├── xpCalculator.ts
│       ├── rarityResolver.ts
│       └── qualityScoreCalculator.ts
└── stores/                      # NEW: Zustand 스토어
    └── useTaxonomyStore.ts
```

### 4.2 기술 스택 호환성 매트릭스

| 항목 | Vite (Source) | Next.js (Target) | 호환성 전략 |
|------|---------------|------------------|-------------|
| React 버전 | 19.1.1 | 18.x | 하위 호환 (기능 제한 없음) |
| Tailwind CSS | 4.1.16 | 3.4.1 | 문법 변환 필요 |
| 상태관리 | zustand 5.0.8 | zustand 5.0.8 | 직접 호환 |
| 애니메이션 | framer-motion 11.18.2 | framer-motion 11.18.2 | "use client" 추가 |
| 그래프 | @xyflow/react 12.9.0 | @xyflow/react 12.9.0 | dynamic import |
| 가상화 | react-window 1.8.11 | react-window 1.8.11 | 직접 호환 |
| 차트 | recharts 2.15.4 | recharts 3.2.1 | 버전 통일 (3.x) |

### 4.3 마이그레이션 우선순위

| Phase | 컴포넌트 그룹 | 의존성 | 예상 복잡도 |
|-------|--------------|--------|------------|
| Phase 1 | 유틸리티 (4개) | 없음 | Low |
| Phase 2 | Common (3개) | 유틸리티 | Low |
| Phase 3 | Agent Card (11개) | 유틸리티, Common | Medium |
| Phase 4 | Taxonomy (8개) | zustand, @xyflow/react | High |
| Phase 5 | Home (2개) | Agent Card | Low |
| Phase 6 | 통합 테스트 | 전체 | Medium |

---

## 5. 추적성 (Traceability)

### 5.1 TAG 체인

```
@SPEC:FRONTEND-MIGRATION-001
├── @TEST:FRONTEND-MIGRATION-001 (마이그레이션 테스트)
├── @CODE:FRONTEND-MIGRATION-001:UTILS (유틸리티 코드)
├── @CODE:FRONTEND-MIGRATION-001:COMPONENTS (컴포넌트 코드)
├── @CODE:FRONTEND-MIGRATION-001:STORES (스토어 코드)
└── @DOC:FRONTEND-MIGRATION-001 (문서화)
```

### 5.2 관련 SPEC

- @SPEC:FRONTEND-INIT-001: 프론트엔드 초기화
- @SPEC:FRONTEND-INTEGRATION-001: 프론트엔드 통합
- @SPEC:AGENT-CARD-001: Agent Card 시스템
- @SPEC:TAXONOMY-VIZ-001: Taxonomy 시각화

---

## SUMMARY (English)

This SPEC defines the migration of the Vite-based Agent Card system to the Next.js frontend. The project currently maintains two separate frontends: a Next.js app (apps/frontend/) with core RAG functionality and a Vite app (frontend/) featuring Pokemon-style Agent Cards with XP/level systems and taxonomy visualization.

The migration scope includes 25 components across 6 categories (Agent Card, XP/Level, Charts, Taxonomy, Common, Home), 4 utility functions (level/XP calculators, rarity resolver), and 1 Zustand store. Key dependencies to add include framer-motion, react-confetti, react-window, @xyflow/react, and zustand.

Technical considerations include React version compatibility (19 to 18), Tailwind CSS syntax conversion (v4 to v3), SSR handling with "use client" directives, and dynamic imports for client-only libraries. The migration follows a 6-phase approach: utilities, common components, agent cards, taxonomy components, home components, and integration testing.

Success criteria include 100% feature parity, all existing tests passing, bundle size increase under 30%, and full SSR compatibility.

---

_이 문서는 `/alfred:2-run SPEC-FRONTEND-MIGRATION-001` 실행 시 기준이 됩니다._
