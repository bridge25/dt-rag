# Implementation Plan: SPEC-UI-DESIGN-001

## Overview

SaaS-Grade UI Design System 구현 계획입니다. 4개 Phase로 구성되며, 각 Phase는 이전 Phase 완료 후 시작합니다.

**중요**: 이 계획은 우선순위와 순서를 정의하며, 시간 예측은 포함하지 않습니다.

---

## Phase 1: 디자인 토큰 구축 (Foundation)

**우선순위**: High (모든 컴포넌트의 기반)

### 1.1 토큰 파일 생성

**목표**: 일관된 디자인 언어를 위한 토큰 정의

**작업**:
- `src/styles/tokens/colors.ts` 생성
  - Primary: Deep Blue (#1e293b, #334155, #475569)
  - Accent: Electric Purple (#8b5cf6, #a78bfa, #c4b5fd)
  - Semantic: Success, Warning, Error
  - Gradient 정의 (135deg, Purple → Blue)

- `src/styles/tokens/elevation.ts` 생성
  - 5단계 boxShadow 정의
  - Level 0~4까지 구체적 픽셀값

- `src/styles/tokens/motion.ts` 생성
  - Duration: fast (200ms), normal (300ms)
  - Easing: easeOut, easeInOut
  - prefers-reduced-motion 처리 함수

- `src/styles/tokens/typography.ts` 생성
  - Font Size: xs, sm, md, lg, xl, 2xl
  - Line Height, Letter Spacing

**기술적 접근**:
- TypeScript 타입 안전성 확보
- CSS-in-JS 객체로 export
- Tailwind extend에 주입 가능한 형태

**완료 조건**:
- 4개 토큰 파일 생성 완료
- TypeScript 타입 에러 없음
- Storybook에서 토큰 Preview 페이지 작성

---

### 1.2 Tailwind 확장

**목표**: Tailwind CSS에 커스텀 토큰 주입

**작업**:
- `tailwind.config.js` 수정
  - theme.extend.colors에 Primary, Accent 추가
  - theme.extend.boxShadow에 Elevation 추가
  - theme.extend.transitionDuration에 Motion 추가

**검증**:
- Tailwind Intellisense에서 `bg-primary-500` 자동완성 확인
- `shadow-elevation-2` 클래스 사용 가능 확인

---

### 1.3 CSS 변수 생성

**목표**: 런타임 테마 전환 지원 (다크 모드)

**작업**:
- `src/styles/globals.css` 수정
  - `:root`에 Light 모드 변수 정의
  - `.dark`에 Dark 모드 변수 정의
  - Color Contrast 7:1 검증

**검증**:
- 다크 모드 토글 시 색상 전환 확인
- WebAIM Contrast Checker로 대비 검증

---

## Phase 2: 15개 컴포넌트 구현

**우선순위**: High → Medium (그룹별 차등)

**전략**: 3그룹으로 분할 (인터랙션 → 피드백 → 네비게이션/레이아웃)

---

### Group 1: 인터랙션 컴포넌트 (5개)

**우선순위**: High (핵심 UX)

#### 2.1 Button 컴포넌트

**파일**: `src/components/ui/Button.tsx`

**Props 인터페이스**:
```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'ghost' | 'danger';
  size: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  children: ReactNode;
  onClick?: () => void;
}
```

**Shine 효과 구현**:
- CSS `::after` pseudo-element
- `linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)`
- `@keyframes shine`: translateX(-100% → 100%)
- Trigger: `onMouseEnter`
- prefers-reduced-motion: 정적 그라데이션

**Storybook Stories**:
- Default (모든 variant)
- Loading 상태
- Disabled 상태
- With Icon

**A11y**:
- `aria-disabled` 속성
- `role="button"` (div 사용 시)
- 키보드 포커스 visible

---

#### 2.2 Input 컴포넌트

**파일**: `src/components/ui/Input.tsx`

**Props**:
```typescript
interface InputProps {
  state?: 'default' | 'error' | 'success';
  label?: string;
  helperText?: string;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
}
```

**Focus Ring**:
- Tailwind: `focus:ring-2 focus:ring-accent-500 focus:ring-offset-2`
- prefers-reduced-motion: ring-offset 제거

**검증 상태**:
- Error: 붉은 테두리 + 에러 메시지
- Success: 초록 체크마크

**Storybook**:
- Default, Error, Success
- With Icon (Search, Email)
- Label + Helper Text

---

#### 2.3 Card 컴포넌트

**파일**: `src/components/ui/Card.tsx`

**Lift 효과**:
```css
.card {
  box-shadow: var(--shadow-elevation-1);
  transition: box-shadow 300ms ease-out, transform 300ms ease-out;
}

.card:hover {
  box-shadow: var(--shadow-elevation-2);
  transform: translateY(-2px);
}

@media (prefers-reduced-motion: reduce) {
  .card:hover {
    transform: none; /* shadow만 변경 */
  }
}
```

**Props**:
- `elevation`: 0 | 1 | 2 (기본 Elevation)
- `hoverable`: boolean (Lift 효과 활성화)

---

#### 2.4 Badge 컴포넌트

**파일**: `src/components/ui/Badge.tsx`

**Props**:
```typescript
interface BadgeProps {
  color: 'info' | 'success' | 'warning' | 'error' | 'purple' | 'blue' | 'gray' | 'dark';
  variant: 'solid' | 'outline';
  shape: 'pill' | 'square';
}
```

**스타일**:
- Pill: `border-radius: 9999px`
- Square: `border-radius: 4px`
- Solid: 배경색 + 흰색 텍스트
- Outline: 테두리 + 배경 투명

---

#### 2.5 Toast 컴포넌트

**파일**: `src/components/ui/Toast.tsx`

**Confetti 효과**:
- 라이브러리: `canvas-confetti`
- Trigger: `toast.success()` 호출 시
- 설정:
  - particleCount: 50
  - spread: 70
  - origin: { y: 0.6 }
  - duration: 2000ms
- prefers-reduced-motion: Confetti 비활성화

**API**:
```typescript
toast.success('저장되었습니다!');
toast.error('오류가 발생했습니다.');
toast.info('알림 메시지');
```

**자동 닫기**:
- 4초 후 자동 제거
- X 버튼 클릭 시 즉시 제거

---

### Group 2: 피드백 컴포넌트 (3개)

**우선순위**: Medium

#### 2.6 Progress 컴포넌트

**파일**: `src/components/ui/Progress.tsx`

**Gradient 진행률**:
```css
.progress-bar {
  background: linear-gradient(90deg, #8b5cf6, #1e293b);
}
```

**Props**:
- `value`: 0~100
- `showLabel`: boolean (퍼센트 표시)

**애니메이션**:
- `transition: width 300ms ease-out`

---

#### 2.7 Spinner 컴포넌트

**파일**: `src/components/ui/Spinner.tsx`

**크기**:
- sm: 16px
- md: 24px
- lg: 32px

**색상**:
- primary: Deep Blue
- white: 흰색 (다크 배경용)

**애니메이션**:
- `@keyframes spin`: rotate(0deg → 360deg)
- duration: 1000ms linear infinite

---

#### 2.8 Modal 컴포넌트

**파일**: `src/components/ui/Modal.tsx`

**Backdrop Blur**:
- `backdrop-blur-sm` (Tailwind)
- 배경: rgba(0,0,0,0.5)

**닫기 트리거**:
- ESC 키 (`useEffect` + keydown listener)
- 외부 클릭 (Backdrop onClick)
- X 버튼 클릭

**Focus Trap**:
- 라이브러리: `react-focus-lock`
- Modal 열림 시 첫 번째 focusable 요소로 이동

**Props**:
```typescript
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
}
```

---

### Group 3: 네비게이션 + 레이아웃 (7개)

**우선순위**: Medium → Low

#### 2.9 Tooltip
- 200ms 지연 표시
- 4방향 위치 (top, bottom, left, right)

#### 2.10 Breadcrumb
- 경로 축약 (3단계 이상 시 "... > 현재")
- 마지막 항목 볼드 처리

#### 2.11 Pagination
- 첫/끝 페이지 버튼
- 현재 페이지 ±2 범위 표시

#### 2.12 Container
- Glass Morphism 옵션: `glass` prop
  - `backdrop-filter: blur(10px)`
  - `background: rgba(255,255,255,0.1)`

#### 2.13 Grid
- 12컬럼 그리드
- 반응형: Mobile 4, Tablet 8, Desktop 12

#### 2.14 Stack
- 수직/수평 스택
- 간격: xs(4px), sm(8px), md(16px), lg(24px), xl(32px)

#### 2.15 Tabs
- 언더라인 애니메이션 (active tab)
- `transition: transform 300ms ease-out`

---

## Phase 3: 일러스트 제작

**우선순위**: Low (기능 완성 후)

### 3.1 Empty State Illustration

**용도**: 검색 결과 없음, 빈 리스트

**스타일**:
- Flat 2.5D (약간의 그림자)
- 색상: Purple (#8b5cf6) + Blue (#1e293b)
- 요소: 빈 박스 + 돋보기

**크기**: 240x240px (SVG)

**파일**: `public/illustrations/empty-state.svg`

---

### 3.2 Onboarding Illustration

**용도**: 첫 방문 사용자 가이드

**구성**: 3단계 슬라이드
- Step 1: 환영 메시지 (손 흔드는 캐릭터)
- Step 2: 주요 기능 소개 (대시보드 화면)
- Step 3: 시작하기 (로켓 발사)

**크기**: 320x240px (SVG)

**파일**: `public/illustrations/onboarding-{1,2,3}.svg`

---

### 3.3 404 Error Illustration

**용도**: 페이지 없음 오류

**스타일**: 친근한 톤 (로봇 캐릭터)
- 로봇이 "404" 간판 들고 있는 모습
- 말풍선: "길을 잃으셨나요?"

**크기**: 320x240px (SVG)

**파일**: `public/illustrations/404-error.svg`

---

## Phase 4: 측정 및 검증

**우선순위**: Critical (출시 전 필수)

### 4.1 Lighthouse 검증

**테스트 환경**:
- Chrome Incognito Mode
- Slow 4G Network Throttling
- Mobile Viewport (375x667)

**실행 명령**:
```bash
lighthouse http://localhost:3000 --output html --output-path .moai/reports/lighthouse-ui-design-001.html
```

**목표 점수**:
- Performance: 90+
- Accessibility: 100
- Best Practices: 95+
- SEO: 90+

**분석**:
- Performance 미달 시: 이미지 최적화, Code Splitting
- Accessibility 미달 시: ARIA 속성 추가, 대비 조정

---

### 4.2 첫인상 테스트 (First Impression Test)

**방법**:
1. 참가자 20명 모집 (SaaS 제품 사용 경험자)
2. 랜딩 페이지 5초 노출
3. 설문 응답 (1-5점 Likert)

**질문**:
1. "이 제품이 전문적으로 보입니까?"
2. "이 제품을 구독하고 싶습니까?"
3. "디자인이 매력적입니까?"

**목표**: 평균 4.5/5 이상 (각 질문별)

**데이터 저장**: `.moai/reports/first-impression-ui-design-001.csv`

---

### 4.3 NPS 조사 (Net Promoter Score)

**방법**:
1. 베타 사용자 30명에게 이메일 발송
2. 질문: "이 제품을 동료에게 추천하시겠습니까?" (0-10점)

**계산**:
- 추천자 (9-10점): Promoter
- 중립자 (7-8점): Passive
- 비추천자 (0-6점): Detractor
- NPS = (Promoter % - Detractor %)

**목표**: NPS 50+
- 예시: 추천자 60%, 비추천자 10% → NPS = 50

---

### 4.4 심미성 평가 (Aesthetic Assessment)

**방법**: Attrakdiff 미니 설문 (5개 항목)

**질문** (1-5점):
1. "디자인이 아름답다"
2. "디자인이 창의적이다"
3. "디자인이 세련되었다"
4. "디자인이 조화롭다"
5. "디자인이 매력적이다"

**목표**: 평균 4.0/5 이상

**데이터 저장**: `.moai/reports/aesthetic-ui-design-001.csv`

---

## 아키텍처 설계 방향

### 컴포넌트 구조

```
src/components/ui/
├── Button/
│   ├── Button.tsx          # 컴포넌트 로직
│   ├── Button.styles.ts    # CSS-in-JS 스타일
│   ├── Button.stories.tsx  # Storybook
│   └── Button.test.tsx     # Unit Test
├── Input/
├── Card/
└── ...
```

### 스타일링 전략

**Hybrid 접근**:
- Tailwind CSS: 레이아웃, 간격, 반응형
- CSS-in-JS (Emotion): 복잡한 애니메이션 (Shine, Lift)

**이유**:
- Tailwind: 빠른 프로토타이핑, 일관성
- CSS-in-JS: 동적 스타일, keyframes 제어

---

## 리스크 및 대응 방안

### R1: Lighthouse Performance 90+ 미달

**원인 가능성**:
- Framer Motion 번들 크기 (>100KB)
- Confetti 라이브러리 렌더링 부하

**대응**:
- Dynamic Import로 Confetti 지연 로딩
- Framer Motion 대신 CSS 애니메이션 우선 사용

---

### R2: 첫인상 테스트 4.5/5 미달

**원인 가능성**:
- 과도한 애니메이션 (산만함)
- 색상 대비 부족

**대응**:
- 애니메이션 빈도 줄이기 (Button에만 Shine 적용)
- Contrast Checker로 재검증 (7:1 → 10:1)

---

### R3: 접근성 검증 실패

**원인 가능성**:
- Modal Focus Trap 미작동
- ARIA 속성 누락

**대응**:
- react-focus-lock 라이브러리 사용
- Storybook A11y Addon으로 자동 검증

---

## 다음 단계

**Phase 1 완료 후**:
- `/alfred:2-build SPEC-UI-DESIGN-001` 실행
- `feature/SPEC-UI-DESIGN-001` 브랜치 생성
- 토큰 파일 구현 시작

**Phase 4 완료 후**:
- `/alfred:3-sync` 실행
- Draft PR 생성
- 측정 결과 보고서 첨부

---

**작성일**: 2025-10-10
**작성자**: @sonheungmin
**추적 태그**: @SPEC:UI-DESIGN-001
