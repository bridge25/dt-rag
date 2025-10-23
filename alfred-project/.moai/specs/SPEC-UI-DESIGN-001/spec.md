---
id: UI-DESIGN-001
version: 0.1.0
status: draft
created: 2025-10-10
updated: 2025-10-10
author: @sonheungmin
priority: high
category: feature
labels:
  - ui
  - design-system
  - saas
  - component-library
scope:
  packages:
    - src/components/ui
    - src/styles/tokens
---

# SPEC-UI-DESIGN-001: SaaS-Grade UI Design System

## HISTORY

### v0.1.0 (2025-10-10) - INITIAL
- SaaS 제품 디자인 시스템 명세 초안 작성
- 15개 컴포넌트 + 디자인 토큰 정의
- 감성 디자인 목표 설정 (Don Norman 3-Level)
- 측정 지표 정의 (Lighthouse, NPS, 첫인상 테스트)

---

## Environment (환경 및 맥락)

### 기술 스택
- **프레임워크**: Next.js 14 (App Router)
- **스타일링**: Tailwind CSS 3.4+ + CSS-in-JS (Emotion/Stitches)
- **애니메이션**: Framer Motion 10+
- **문서화**: Storybook 7+
- **접근성**: Radix UI Primitives

### 경쟁 환경
- **벤치마크 제품**: Linear, Notion, Figma, Vercel
- **SaaS 제품 요구사항**: "구독하고 싶다"는 첫인상
- **감성 목표**:
  - Visceral Level: 4.5/5 (매력 + 전문성)
  - Behavioral Level: 4.2/5 (효율성 + 즐거움)
  - Reflective Level: NPS 50+, 심미성 4.0/5+

### 제약사항
- **성능**: Lighthouse Performance 90+ 유지
- **접근성**: WCAG AAA 기준 (대비 7:1+)
- **모션**: prefers-reduced-motion 필수 지원
- **브라우저**: Chrome/Edge/Safari 최신 3버전

---

## Assumptions (전제 조건)

### A1: 기본 제공 원칙
**모든 UI 효과는 기본으로 제공되며, 프리미엄/베이직 분리 없음**
- Shine, Lift, Confetti 등 모든 효과는 표준 컴포넌트에 포함
- 유일한 조건부 로직: prefers-reduced-motion
- 이유: SaaS 제품의 일관된 UX 제공

### A2: 점진적 마이그레이션
**기존 컴포넌트를 단계적으로 교체**
- Phase 1: 디자인 토큰 우선 적용
- Phase 2: 핵심 컴포넌트 교체 (Button, Input, Card)
- Phase 3: 보조 컴포넌트 추가
- Phase 4: 일러스트 및 검증

### A3: Storybook 기반 개발
**모든 컴포넌트는 Storybook에서 먼저 개발 및 문서화**
- 각 컴포넌트당 최소 3개 Story (Default, Interactive, Edge Case)
- Controls를 통한 실시간 Props 조작
- A11y Addon으로 접근성 자동 검증

---

## Requirements (요구사항)

### R1: Ubiquitous Requirements (보편 요구사항)

#### R1.1: 15개 핵심 컴포넌트 제공
**시스템은 다음 15개 컴포넌트를 제공해야 한다**:

**인터랙션 (5개)**:
- Button: Shine 효과, 4가지 variant (primary, secondary, ghost, danger)
- Input: Focus Ring, 검증 상태 (error, success)
- Card: Lift 효과 (hover 시 elevation 변화)
- Badge: 8가지 색상 (info, success, warning, error 등)
- Toast: Confetti 효과 (성공 시), 4초 자동 닫기

**피드백 (3개)**:
- Progress: Gradient 진행률 표시
- Spinner: 3가지 크기 (sm, md, lg)
- Modal: Backdrop Blur, ESC 키 닫기

**네비게이션 (3개)**:
- Tooltip: 200ms 지연 표시
- Breadcrumb: 경로 축약 (3단계 이상 시)
- Pagination: 첫/끝 페이지 바로가기

**레이아웃 (4개)**:
- Container: Glass Morphism 선택 가능
- Grid: 12컬럼 그리드 시스템
- Stack: 간격 조정 (xs, sm, md, lg, xl)
- Tabs: 언더라인 애니메이션

#### R1.2: 디자인 토큰 시스템
**시스템은 다음 토큰을 정의해야 한다**:

**컬러**:
- Primary: Deep Blue (#1e293b, #334155, #475569)
- Accent: Electric Purple (#8b5cf6, #a78bfa, #c4b5fd)
- Gradient: 135deg, Purple → Blue
- Semantic: Success (#10b981), Warning (#f59e0b), Error (#ef4444)

**Elevation** (5단계):
- Level 0: shadow-none
- Level 1: shadow-sm (카드 기본)
- Level 2: shadow-md (카드 호버)
- Level 3: shadow-lg (모달)
- Level 4: shadow-xl (드롭다운)

**Motion**:
- Duration: Fast 200ms, Normal 300ms
- Easing: ease-out (진입), ease-in-out (변환)
- prefers-reduced-motion: duration 0ms

#### R1.3: Storybook 문서화
**각 컴포넌트는 Storybook 문서를 포함해야 한다**:
- Props Table (타입, 기본값, 설명)
- 최소 3개 Story (기본, 인터랙티브, 엣지케이스)
- A11y 검증 결과
- Design Token 사용 예시

---

### R2: Event-driven Requirements (이벤트 기반 요구사항)

#### R2.1: Confetti 효과
**사용자가 성공 Toast를 트리거하면, 시스템은 Confetti 애니메이션을 표시해야 한다**:
- Trigger: `toast.success()` 호출
- Duration: 2초
- Particle 수: 50개
- prefers-reduced-motion: 효과 비활성화

#### R2.2: Shine 효과
**사용자가 Primary Button에 마우스를 올리면, 시스템은 Shine 애니메이션을 표시해야 한다**:
- Trigger: mouseenter 이벤트
- Animation: 왼쪽→오른쪽 그라데이션 이동 (1초)
- prefers-reduced-motion: 정적 그라데이션 표시

#### R2.3: Lift 효과
**사용자가 Card에 마우스를 올리면, 시스템은 Elevation을 Level 1→2로 변경해야 한다**:
- Trigger: hover 상태
- Transition: 300ms ease-out
- Transform: translateY(-2px)
- prefers-reduced-motion: shadow만 변경 (transform 없음)

---

### R3: State-driven Requirements (상태 기반 요구사항)

#### R3.1: prefers-reduced-motion 처리
**사용자의 모션 설정이 'reduce'이면, 시스템은 모든 애니메이션을 비활성화해야 한다**:
- CSS 미디어 쿼리: `@media (prefers-reduced-motion: reduce)`
- 대응:
  - transition-duration: 0ms
  - animation: none
  - transform 제거 (shadow, opacity만 유지)

#### R3.2: 다크 모드 지원
**사용자가 다크 모드를 활성화하면, 시스템은 토큰을 자동 전환해야 한다**:
- Trigger: `prefers-color-scheme: dark` 또는 토글
- Primary 색상 반전: #1e293b → #f8fafc
- Contrast 유지: 7:1 이상

#### R3.3: 반응형 레이아웃
**뷰포트 크기에 따라 Grid 컬럼 수를 조정해야 한다**:
- Mobile (<640px): 4컬럼
- Tablet (640-1024px): 8컬럼
- Desktop (>1024px): 12컬럼

---

### R4: Constraints (제약사항)

#### R4.1: 성능 제약
- Lighthouse Performance: 90점 이상
- First Contentful Paint: 1.8초 이하
- Total Blocking Time: 200ms 이하
- Cumulative Layout Shift: 0.1 이하

#### R4.2: 접근성 제약
- WCAG AAA 준수 (대비 7:1+)
- 키보드 내비게이션 100% 지원
- 스크린 리더 테스트 통과 (NVDA, JAWS)
- Lighthouse Accessibility: 100점

#### R4.3: 감성 제약
- 첫인상 테스트: 4.5/5 이상 (n=20)
- NPS: 50점 이상
- 심미성 평가: 4.0/5 이상

---

## Specifications (상세 명세)

### Phase 1: 디자인 토큰 구축

#### 1.1 토큰 파일 생성
**위치**: `src/styles/tokens/`
- `colors.ts`: 컬러 팔레트 (Primary, Accent, Semantic)
- `elevation.ts`: 5단계 그림자 정의
- `motion.ts`: Duration, Easing 함수
- `typography.ts`: 폰트 크기, 행간, 자간

#### 1.2 Tailwind 확장
**파일**: `tailwind.config.js`
```javascript
theme: {
  extend: {
    colors: {
      primary: {...},
      accent: {...}
    },
    boxShadow: {
      'elevation-1': '...',
      // ...
    }
  }
}
```

#### 1.3 CSS 변수 생성
**파일**: `src/styles/globals.css`
```css
:root {
  --color-primary-500: #1e293b;
  --shadow-elevation-1: 0 1px 3px rgba(0,0,0,0.12);
  /* ... */
}
```

---

### Phase 2: 15개 컴포넌트 구현

#### Group 1: 인터랙션 (5개)

**2.1 Button 컴포넌트**
- Props:
  - variant: 'primary' | 'secondary' | 'ghost' | 'danger'
  - size: 'sm' | 'md' | 'lg'
  - disabled: boolean
  - loading: boolean (Spinner 표시)
- Shine 효과 구현:
  ```css
  .button-primary::after {
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    animation: shine 1s ease-out;
  }
  ```

**2.2 Input 컴포넌트**
- Props:
  - state: 'default' | 'error' | 'success'
  - icon: ReactNode (접두사/접미사)
- Focus Ring: `ring-2 ring-accent-500 ring-offset-2`

**2.3 Card 컴포넌트**
- Lift 효과:
  ```css
  .card:hover {
    box-shadow: var(--shadow-elevation-2);
    transform: translateY(-2px);
  }
  ```

**2.4 Badge 컴포넌트**
- 8가지 색상: info, success, warning, error, purple, blue, gray, dark
- Pill/Square 형태 선택 가능

**2.5 Toast 컴포넌트**
- Confetti 효과 (canvas-confetti 라이브러리)
- 4초 자동 닫기, X 버튼 수동 닫기

#### Group 2: 피드백 (3개)

**2.6 Progress**
- Gradient 진행률: Purple → Blue
- 애니메이션: 진행 시 부드러운 transition

**2.7 Spinner**
- 3가지 크기 (16px, 24px, 32px)
- 색상: Primary/White

**2.8 Modal**
- Backdrop Blur: `backdrop-blur-sm`
- ESC 키, 외부 클릭 닫기
- Trap Focus (react-focus-lock)

#### Group 3: 네비게이션 + 레이아웃 (7개)

**2.9~2.15**: Tooltip, Breadcrumb, Pagination, Container, Grid, Stack, Tabs
- 각 컴포넌트 Props 정의
- Storybook Stories 작성

---

### Phase 3: 일러스트 제작

#### 3.1 Empty State Illustration
- 용도: 검색 결과 없음, 빈 리스트
- 스타일: Flat 2.5D, Purple/Blue 톤

#### 3.2 Onboarding Illustration
- 용도: 첫 방문 사용자 가이드
- 3단계 슬라이드 일러스트

#### 3.3 404 Error Illustration
- 용도: 페이지 없음 오류
- 친근한 톤 (로봇 캐릭터)

---

### Phase 4: 측정 및 검증

#### 4.1 Lighthouse 검증
- 테스트 환경: Chrome Incognito, Slow 4G
- 목표:
  - Performance: 90+
  - Accessibility: 100
  - Best Practices: 95+
  - SEO: 90+

#### 4.2 첫인상 테스트
- 방법: 5초 노출 후 설문 (1-5점)
- 질문:
  1. "이 제품이 전문적으로 보입니까?"
  2. "이 제품을 구독하고 싶습니까?"
  3. "디자인이 매력적입니까?"
- 목표: 평균 4.5/5 이상 (n=20)

#### 4.3 NPS 조사
- 방법: "이 제품을 동료에게 추천하시겠습니까?" (0-10점)
- 계산: (추천자% - 비추천자%)
- 목표: NPS 50+ (추천자 60%, 비추천자 10%)

#### 4.4 심미성 평가
- 방법: Attrakdiff 미니 설문
- 질문: "디자인이 아름답다" (1-5점)
- 목표: 4.0/5 이상

---

## Traceability (추적성)

### TAG System
- **@SPEC:UI-DESIGN-001**: 본 명세 참조
- **@IMPL:UI-DESIGN-001**: 구현 브랜치/PR 참조
- **@TEST:UI-DESIGN-001**: 테스트 케이스 참조

### Related Artifacts
- Storybook: `http://localhost:6006/?path=/docs/ui-button--docs`
- Lighthouse Report: `.moai/reports/lighthouse-ui-design-001.html`
- 첫인상 테스트 결과: `.moai/reports/first-impression-ui-design-001.csv`

### Dependencies
- 없음 (독립 실행 가능)

### Acceptance Criteria
- 상세 시나리오는 `acceptance.md` 참조
- 구현 계획은 `plan.md` 참조
