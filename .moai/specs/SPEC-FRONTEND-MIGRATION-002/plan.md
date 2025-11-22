---
id: SPEC-FRONTEND-MIGRATION-002-PLAN
version: 1.0.0
status: draft
created: 2025-11-23
updated: 2025-11-23
author: "@spec-builder"
spec_ref: SPEC-FRONTEND-MIGRATION-002
---

# @PLAN:FRONTEND-MIGRATION-002 구현 계획

> **English**: Implementation Plan for Agent Detail/History Pages Migration

## 1. 목표 (Objectives)

### 1.1 주요 목표

- Vite의 AgentDetailPage, AgentHistoryPage를 Next.js App Router로 마이그레이션
- agent-detail, history 컴포넌트 디렉토리 생성 및 마이그레이션
- 기존 기능 100% 보존 및 TDD 기반 품질 보장

### 1.2 성공 기준

- 모든 6개 컴포넌트 마이그레이션 완료
- 2개 페이지 라우트 동작 확인
- 단위 테스트 100% 통과
- 기존 Agents 페이지에서 Detail 페이지로 네비게이션 가능

---

## 2. 마일스톤 (Milestones)

### Phase 1: agent-detail 컴포넌트 마이그레이션

**우선순위**: High

**태스크**:
1. `components/agent-detail/` 디렉토리 생성
2. AgentDetailCard 마이그레이션
   - `"use client"` 지시어 추가
   - import 경로 조정
   - Tailwind CSS 스타일 검증
3. LevelUpTimeline 마이그레이션
4. XPAwardButton 마이그레이션

**검증**:
- 각 컴포넌트 단위 테스트 작성 및 통과

### Phase 2: history 컴포넌트 마이그레이션

**우선순위**: High

**태스크**:
1. `components/history/` 디렉토리 생성
2. ChartContainer 마이그레이션
3. CoverageChart 마이그레이션
   - recharts SSR 호환성 확인
   - "use client" 지시어 추가
4. XPGrowthChart 마이그레이션

**검증**:
- 차트 렌더링 테스트
- 기간 필터 동작 테스트

### Phase 3: AgentDetailPage 마이그레이션

**우선순위**: High

**태스크**:
1. `app/(dashboard)/agents/[id]/` 디렉토리 생성
2. page.tsx 생성 및 마이그레이션
   - `react-router-dom` 패턴을 Next.js로 변환
   - `useParams` → Next.js `useParams` 또는 `params` prop
   - `useNavigate` → `useRouter`
   - `Link to={...}` → `Link href={...}`
3. 레벨업 모달 통합 검증

**검증**:
- 동적 라우팅 테스트 (`/agents/[id]`)
- 에이전트 데이터 로딩 테스트
- 에러 상태 테스트

### Phase 4: AgentHistoryPage 마이그레이션

**우선순위**: High

**태스크**:
1. `app/(dashboard)/agents/[id]/history/` 디렉토리 생성
2. page.tsx 생성 및 마이그레이션
3. ChartContainer, CoverageChart, XPGrowthChart 통합

**검증**:
- 히스토리 데이터 로딩 테스트
- 차트 렌더링 테스트
- 기간 필터 기능 테스트

### Phase 5: 통합 테스트 및 네비게이션 연결

**우선순위**: Medium

**태스크**:
1. Agents 목록 페이지에서 Detail 페이지로 링크 추가
2. Detail ↔ History 간 네비게이션 검증
3. 뒤로 가기 버튼 동작 검증
4. E2E 테스트 시나리오 작성

**검증**:
- 전체 사용자 플로우 테스트
- 페이지 간 전환 테스트

---

## 3. 기술 접근 방식 (Technical Approach)

### 3.1 라우팅 변환 전략

```tsx
// Vite (Before)
import { useParams, Link, useNavigate } from 'react-router-dom'

export default function Page() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  return (
    <button onClick={() => navigate(-1)}>Back</button>
    <Link to={`/agents/${id}/history`}>History</Link>
  )
}

// Next.js (After)
'use client'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'

export default function Page() {
  const params = useParams<{ id: string }>()
  const router = useRouter()

  return (
    <button onClick={() => router.back()}>Back</button>
    <Link href={`/agents/${params.id}/history`}>History</Link>
  )
}
```

### 3.2 클라이언트 컴포넌트 패턴

```tsx
// 차트 컴포넌트 (recharts 사용)
'use client'

import { LineChart, Line, XAxis, YAxis, ... } from 'recharts'

export function CoverageChart({ data }: Props) {
  // 클라이언트 사이드에서만 렌더링
  return (
    <ResponsiveContainer>
      <LineChart data={data}>
        ...
      </LineChart>
    </ResponsiveContainer>
  )
}
```

### 3.3 훅 재사용 전략

기존 `hooks/` 디렉토리의 훅들은 수정 없이 재사용:
- `useAgent(id)` - 에이전트 데이터 조회
- `useCoverageHistory(id, options)` - 히스토리 데이터 조회

---

## 4. 아키텍처 설계 방향 (Architecture Direction)

### 4.1 컴포넌트 계층 구조

```
Pages (Server/Client Components)
├── AgentDetailPage (Client)
│   ├── AgentDetailCard (Client)
│   │   └── [기존 agent-card 컴포넌트들]
│   ├── LevelUpTimeline (Client)
│   ├── XPAwardButton (Client)
│   └── LevelUpModal (Client, 기존)
│
└── AgentHistoryPage (Client)
    ├── ChartContainer (Client)
    ├── CoverageChart (Client)
    └── XPGrowthChart (Client)
```

### 4.2 상태 관리

- **서버 상태**: @tanstack/react-query로 관리 (기존 패턴 유지)
- **로컬 상태**: React useState (레벨업 모달, 선택된 기간 등)

### 4.3 에러 처리

- 컴포넌트 레벨 에러: try-catch 및 조건부 렌더링
- 페이지 레벨 에러: Next.js error.tsx (필요시)
- 네트워크 에러: react-query의 에러 상태 활용

---

## 5. 리스크 및 대응 계획 (Risks and Mitigation)

### 5.1 기술적 리스크

| 리스크 | 가능성 | 영향 | 대응 |
|--------|--------|------|------|
| recharts SSR 호환 문제 | Medium | Medium | dynamic import 또는 "use client" |
| hooks 호환성 문제 | Low | High | 기존 hooks 코드 검증 후 마이그레이션 |
| 라우팅 파라미터 불일치 | Low | Medium | 타입 정의 및 런타임 검증 |

### 5.2 의존성 리스크

| 리스크 | 대응 |
|--------|------|
| 기존 agent-card 컴포넌트 미완료 | Phase 1 시작 전 의존성 확인 |
| API 변경 | API 계약 사전 검증 |

---

## 6. 전문가 협의 권장사항 (Expert Consultation Recommendations)

### 6.1 Frontend Expert 협의

- **범위**: 컴포넌트 아키텍처 검토, Next.js App Router 최적화
- **질문 항목**:
  - Server Component vs Client Component 경계 최적화
  - 차트 라이브러리 SSR 처리 방안
  - 동적 라우팅 성능 최적화

### 6.2 UI/UX Expert 협의 (선택)

- **범위**: 페이지 전환 UX, 로딩 상태 디자인
- **질문 항목**:
  - 스켈레톤 UI 패턴
  - 에러 상태 UX

---

## 7. 다음 단계 (Next Steps)

1. `/alfred:2-run SPEC-FRONTEND-MIGRATION-002` 실행으로 구현 시작
2. Phase 1부터 순차적 진행
3. 각 Phase 완료 시 통합 테스트 수행
4. 완료 후 `/alfred:3-sync` 실행으로 문서 동기화

---

_이 문서는 `/alfred:2-run SPEC-FRONTEND-MIGRATION-002` 실행 시 구현 가이드로 사용됩니다._
