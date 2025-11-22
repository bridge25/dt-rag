---
id: SPEC-FRONTEND-MIGRATION-002
version: 1.0.0
status: draft
created: 2025-11-23
updated: 2025-11-23
author: "@spec-builder"
priority: high
domain: frontend
tags: [migration, nextjs, vite, agent-detail, history, pages]
parent: SPEC-FRONTEND-MIGRATION-001
---

# @SPEC:FRONTEND-MIGRATION-002 Agent Detail/History 페이지 및 컴포넌트 마이그레이션

> **English**: Migration of Agent Detail/History Pages and Missing Components to Next.js

## HISTORY

### v1.0.0 (2025-11-23)

- **INITIAL**: SPEC 문서 초안 작성
- **AUTHOR**: @spec-builder
- **SECTIONS**: 환경분석, 요구사항, EARS 사양, 마이그레이션 계획

---

## 1. 환경 분석 (Environment)

### 1.1 상위 SPEC 참조

본 SPEC은 `SPEC-FRONTEND-MIGRATION-001`의 후속 작업으로, 컴포넌트 마이그레이션 완료 후 누락된 페이지 라우트 및 관련 컴포넌트를 마이그레이션합니다.

### 1.2 마이그레이션 대상

#### 페이지 라우트 (2개)

| 페이지 | Vite 소스 | Next.js 대상 | 설명 |
|--------|-----------|--------------|------|
| AgentDetailPage | `_archive/frontend-vite/src/pages/AgentDetailPage.tsx` | `app/(dashboard)/agents/[id]/page.tsx` | 에이전트 상세 정보 페이지 |
| AgentHistoryPage | `_archive/frontend-vite/src/pages/AgentHistoryPage.tsx` | `app/(dashboard)/agents/[id]/history/page.tsx` | 에이전트 히스토리 페이지 |

#### agent-detail 컴포넌트 (3개)

| 컴포넌트 | Vite 소스 | Next.js 대상 | 설명 |
|----------|-----------|--------------|------|
| AgentDetailCard | `_archive/frontend-vite/src/components/agent-detail/AgentDetailCard.tsx` | `components/agent-detail/AgentDetailCard.tsx` | 에이전트 상세 카드 |
| LevelUpTimeline | `_archive/frontend-vite/src/components/agent-detail/LevelUpTimeline.tsx` | `components/agent-detail/LevelUpTimeline.tsx` | 레벨업 타임라인 |
| XPAwardButton | `_archive/frontend-vite/src/components/agent-detail/XPAwardButton.tsx` | `components/agent-detail/XPAwardButton.tsx` | XP 수여 버튼 |

#### history 컴포넌트 (3개)

| 컴포넌트 | Vite 소스 | Next.js 대상 | 설명 |
|----------|-----------|--------------|------|
| CoverageChart | `_archive/frontend-vite/src/components/history/CoverageChart.tsx` | `components/history/CoverageChart.tsx` | 커버리지 차트 |
| ChartContainer | `_archive/frontend-vite/src/components/history/ChartContainer.tsx` | `components/history/ChartContainer.tsx` | 차트 컨테이너 |
| XPGrowthChart | `_archive/frontend-vite/src/components/history/XPGrowthChart.tsx` | `components/history/XPGrowthChart.tsx` | XP 성장 차트 |

### 1.3 기술 스택

| 항목 | 버전 | 용도 |
|------|------|------|
| Next.js | 14.x | App Router, 동적 라우팅 |
| React | 18.x | UI 라이브러리 |
| Tailwind CSS | 3.4.x | 스타일링 |
| @tanstack/react-query | 5.x | 서버 상태 관리 |
| recharts | 3.x | 차트 시각화 |
| framer-motion | 11.x | 애니메이션 |

### 1.4 의존성 관계

```
AgentDetailPage
├── AgentDetailCard
│   ├── RarityBadge (기존)
│   ├── ProgressBar (기존)
│   └── StatDisplay (기존)
├── LevelUpTimeline
├── XPAwardButton
└── LevelUpModal (기존)

AgentHistoryPage
├── ChartContainer
├── CoverageChart
└── XPGrowthChart
```

---

## 2. 가정 (Assumptions)

### 2.1 기술적 가정

- Next.js App Router의 동적 라우팅 `[id]`는 Vite의 `useParams`를 대체함
- `react-router-dom`의 `Link`, `useNavigate`는 Next.js의 `Link`, `useRouter`로 대체됨
- 기존 hooks (`useAgent`, `useCoverageHistory`)가 Next.js 환경에서 동작함
- recharts는 "use client" 지시어로 클라이언트 사이드 렌더링 처리

### 2.2 비즈니스 가정

- 기존 Vite 페이지의 기능과 UX는 100% 보존됨
- 에이전트 상세/히스토리 URL 구조: `/agents/:id` 및 `/agents/:id/history`
- 마이그레이션 후 Vite 아카이브 파일은 참조용으로만 유지

### 2.3 선행 조건

- SPEC-FRONTEND-MIGRATION-001의 다음 컴포넌트가 마이그레이션 완료:
  - `components/agent-card/RarityBadge.tsx`
  - `components/agent-card/ProgressBar.tsx`
  - `components/agent-card/StatDisplay.tsx`
  - `components/agent-card/LevelUpModal.tsx`

---

## 3. EARS 요구사항 (Requirements)

### 3.1 Ubiquitous Requirements (기본 요구사항)

- **[REQ-U-001]** 시스템은 에이전트 상세 정보 페이지를 제공해야 한다.
- **[REQ-U-002]** 시스템은 에이전트 히스토리 및 분석 페이지를 제공해야 한다.
- **[REQ-U-003]** 시스템은 XP 수여 기능을 제공해야 한다.
- **[REQ-U-004]** 시스템은 커버리지 및 XP 성장 차트를 제공해야 한다.

### 3.2 Event-driven Requirements (이벤트 기반 요구사항)

- **[REQ-E-001]** WHEN 사용자가 에이전트 카드를 클릭하면, 시스템은 `/agents/:id` 페이지로 이동해야 한다.
- **[REQ-E-002]** WHEN 사용자가 "View History" 버튼을 클릭하면, 시스템은 `/agents/:id/history` 페이지로 이동해야 한다.
- **[REQ-E-003]** WHEN 사용자가 XP Award 버튼을 클릭하면, 시스템은 XP를 부여하고 UI를 업데이트해야 한다.
- **[REQ-E-004]** WHEN 에이전트가 레벨업하면, 시스템은 LevelUpModal을 표시해야 한다.
- **[REQ-E-005]** WHEN 사용자가 기간 필터를 변경하면, 시스템은 차트 데이터를 필터링해야 한다.
- **[REQ-E-006]** WHEN 뒤로 가기 버튼을 클릭하면, 시스템은 이전 페이지로 네비게이션해야 한다.

### 3.3 State-driven Requirements (상태 기반 요구사항)

- **[REQ-S-001]** WHILE 에이전트 데이터가 로딩 중이면, 시스템은 스켈레톤 UI를 표시해야 한다.
- **[REQ-S-002]** WHILE 히스토리 데이터가 로딩 중이면, 시스템은 차트 영역에 로딩 상태를 표시해야 한다.
- **[REQ-S-003]** WHILE 에러 상태이면, 시스템은 에러 메시지와 재시도 버튼을 표시해야 한다.

### 3.4 Optional Features (선택적 기능)

- **[REQ-O-001]** WHERE 히스토리 데이터가 없으면, 시스템은 빈 상태 메시지를 표시할 수 있다.
- **[REQ-O-002]** WHERE 에이전트가 존재하지 않으면, 시스템은 404 상태를 표시할 수 있다.

### 3.5 Constraints (제약사항)

- **[REQ-C-001]** 모든 페이지 컴포넌트는 "use client" 지시어를 사용해야 한다.
- **[REQ-C-002]** 동적 라우트 파라미터는 Next.js의 `params` prop으로 접근해야 한다.
- **[REQ-C-003]** `react-router-dom`의 `Link`는 `next/link`로 대체해야 한다.
- **[REQ-C-004]** `useNavigate`는 `next/navigation`의 `useRouter`로 대체해야 한다.
- **[REQ-C-005]** 모든 마이그레이션된 컴포넌트는 단위 테스트를 포함해야 한다.

---

## 4. 사양 (Specifications)

### 4.1 디렉토리 구조

```
apps/frontend/
├── app/
│   └── (dashboard)/
│       └── agents/
│           ├── page.tsx           # 기존 (에이전트 목록)
│           └── [id]/              # NEW: 동적 라우트
│               ├── page.tsx       # NEW: AgentDetailPage
│               └── history/
│                   └── page.tsx   # NEW: AgentHistoryPage
├── components/
│   ├── agent-detail/              # NEW: 디렉토리 생성
│   │   ├── AgentDetailCard.tsx
│   │   ├── LevelUpTimeline.tsx
│   │   └── XPAwardButton.tsx
│   └── history/                   # NEW: 디렉토리 생성
│       ├── ChartContainer.tsx
│       ├── CoverageChart.tsx
│       └── XPGrowthChart.tsx
└── __tests__/
    ├── agent-detail/
    │   ├── AgentDetailCard.test.tsx
    │   ├── LevelUpTimeline.test.tsx
    │   └── XPAwardButton.test.tsx
    ├── history/
    │   ├── ChartContainer.test.tsx
    │   ├── CoverageChart.test.tsx
    │   └── XPGrowthChart.test.tsx
    └── pages/
        ├── AgentDetailPage.test.tsx
        └── AgentHistoryPage.test.tsx
```

### 4.2 라우팅 변환 매핑

| Vite (react-router-dom) | Next.js (App Router) |
|-------------------------|----------------------|
| `/agents/:id` | `/agents/[id]` |
| `/agents/:id/history` | `/agents/[id]/history` |
| `useParams<{ id: string }>()` | `params: { id: string }` (Server Component) 또는 `useParams()` (Client Component) |
| `useNavigate()` | `useRouter()` from `next/navigation` |
| `<Link to={...}>` | `<Link href={...}>` from `next/link` |
| `navigate(-1)` | `router.back()` |

### 4.3 컴포넌트 변환 패턴

#### AgentDetailPage 변환

```tsx
// Before (Vite)
import { useParams, Link, useNavigate } from 'react-router-dom'
const { id } = useParams<{ id: string }>()
const navigate = useNavigate()

// After (Next.js)
'use client'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
const params = useParams<{ id: string }>()
const router = useRouter()
```

### 4.4 마이그레이션 우선순위

| Phase | 항목 | 의존성 | 복잡도 |
|-------|------|--------|--------|
| Phase 1 | agent-detail 컴포넌트 (3개) | 기존 agent-card 컴포넌트 | Low |
| Phase 2 | history 컴포넌트 (3개) | recharts | Medium |
| Phase 3 | AgentDetailPage | Phase 1 컴포넌트 | Medium |
| Phase 4 | AgentHistoryPage | Phase 1, 2 컴포넌트 | Medium |
| Phase 5 | 통합 테스트 | 전체 | Low |

---

## 5. 추적성 (Traceability)

### 5.1 TAG 체인

```
@SPEC:FRONTEND-MIGRATION-002
├── @TEST:FRONTEND-MIGRATION-002:COMPONENTS (컴포넌트 테스트)
├── @TEST:FRONTEND-MIGRATION-002:PAGES (페이지 테스트)
├── @CODE:FRONTEND-MIGRATION-002:AGENT-DETAIL (agent-detail 컴포넌트)
├── @CODE:FRONTEND-MIGRATION-002:HISTORY (history 컴포넌트)
├── @CODE:FRONTEND-MIGRATION-002:PAGES (페이지 라우트)
└── @DOC:FRONTEND-MIGRATION-002 (문서화)
```

### 5.2 관련 SPEC

- @SPEC:FRONTEND-MIGRATION-001 (상위 SPEC - 컴포넌트 마이그레이션)
- @SPEC:FRONTEND-INIT-001 (프론트엔드 초기화)
- @SPEC:FRONTEND-INTEGRATION-001 (프론트엔드 통합)
- @SPEC:AGENT-CARD-001 (Agent Card 시스템)

---

## SUMMARY (English)

This SPEC defines the migration of Agent Detail and History pages along with their dependent components from Vite to Next.js. It is a follow-up to SPEC-FRONTEND-MIGRATION-001, which focused on component migration.

**Scope includes:**
- 2 pages: AgentDetailPage (`/agents/[id]`) and AgentHistoryPage (`/agents/[id]/history`)
- 3 agent-detail components: AgentDetailCard, LevelUpTimeline, XPAwardButton
- 3 history components: CoverageChart, ChartContainer, XPGrowthChart

**Key technical considerations:**
- Converting react-router-dom patterns to Next.js App Router
- Using "use client" directive for interactive components
- Replacing `useParams`/`useNavigate` with Next.js equivalents
- Maintaining existing hooks (`useAgent`, `useCoverageHistory`) compatibility

**Migration phases:** Components first (Phase 1-2), then pages (Phase 3-4), followed by integration testing (Phase 5).

---

_이 문서는 `/alfred:2-run SPEC-FRONTEND-MIGRATION-002` 실행 시 기준이 됩니다._
