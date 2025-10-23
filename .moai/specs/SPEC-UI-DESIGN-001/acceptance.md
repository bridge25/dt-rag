# Acceptance Criteria: SPEC-UI-DESIGN-001

## Overview

SPEC-UI-DESIGN-001의 수락 기준을 Given-When-Then 형식으로 정의합니다. 모든 시나리오는 구현 완료 후 검증되어야 합니다.

---

## AC1: Button Shine 효과

### Scenario 1.1: Primary Button Shine 애니메이션

**Given**: 사용자가 Primary Button이 있는 페이지를 열었을 때
**When**: 사용자가 마우스를 Button 위에 올리면
**Then**:
- Shine 애니메이션(왼쪽→오른쪽 그라데이션 이동)이 1초 동안 재생된다
- 애니메이션은 `linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)` 형태다
- 애니메이션 완료 후 원래 상태로 돌아간다

**검증 방법**:
- Storybook에서 Button Primary Story 열기
- 마우스 호버 시 Shine 효과 육안 확인
- DevTools Animation Inspector로 duration 1000ms 확인

---

### Scenario 1.2: prefers-reduced-motion에서 Shine 비활성화

**Given**: 사용자의 OS 설정이 `prefers-reduced-motion: reduce`일 때
**When**: 사용자가 Primary Button에 마우스를 올리면
**Then**:
- Shine 애니메이션이 재생되지 않는다
- 정적 그라데이션만 표시된다 (애니메이션 없음)

**검증 방법**:
- Chrome DevTools → Rendering → Emulate CSS media feature `prefers-reduced-motion: reduce` 활성화
- Button 호버 시 `animation: none` 확인

---

## AC2: Toast Confetti 효과

### Scenario 2.1: 성공 Toast Confetti 트리거

**Given**: 사용자가 폼 제출 성공 시
**When**: `toast.success('저장되었습니다!')` 호출되면
**Then**:
- Toast 메시지가 화면 우측 상단에 나타난다
- Confetti 애니메이션이 2초 동안 재생된다 (50개 파티클)
- Toast는 4초 후 자동으로 사라진다

**검증 방법**:
- Storybook Toast Success Story 실행
- Confetti 파티클 개수 육안 확인 (약 50개)
- 4초 카운트 후 Toast 자동 제거 확인

---

### Scenario 2.2: prefers-reduced-motion에서 Confetti 비활성화

**Given**: 사용자의 OS 설정이 `prefers-reduced-motion: reduce`일 때
**When**: `toast.success()` 호출되면
**Then**:
- Toast 메시지만 표시된다 (Confetti 없음)
- 4초 후 자동 제거는 동일하게 작동한다

**검증 방법**:
- `prefers-reduced-motion: reduce` 설정
- Toast Success 트리거 시 Confetti 미발생 확인

---

## AC3: Card Lift 효과

### Scenario 3.1: Card 호버 시 Elevation 변화

**Given**: 사용자가 Card 컴포넌트가 있는 페이지를 열었을 때
**When**: 사용자가 Card에 마우스를 올리면
**Then**:
- Card의 boxShadow가 Elevation 1 → 2로 변한다
- Card가 Y축으로 -2px 이동한다 (`transform: translateY(-2px)`)
- Transition은 300ms ease-out으로 부드럽게 진행된다

**검증 방법**:
- Storybook Card Hoverable Story 열기
- DevTools에서 hover 상태의 `box-shadow` 값 확인 (Elevation 2와 일치)
- `transform: translateY(-2px)` 확인

---

### Scenario 3.2: prefers-reduced-motion에서 Transform 제거

**Given**: 사용자의 OS 설정이 `prefers-reduced-motion: reduce`일 때
**When**: 사용자가 Card에 마우스를 올리면
**Then**:
- boxShadow만 변경된다 (Elevation 1 → 2)
- `transform` 속성은 적용되지 않는다 (Y축 이동 없음)

**검증 방법**:
- `prefers-reduced-motion: reduce` 설정
- Card 호버 시 `transform: none` 확인

---

## AC4: Lighthouse 점수 검증

### Scenario 4.1: Performance 90점 이상

**Given**: 프로덕션 빌드가 완료되었을 때
**When**: Lighthouse Performance 테스트를 실행하면
**Then**:
- Performance 점수가 90점 이상이다
- First Contentful Paint (FCP)이 1.8초 이하다
- Total Blocking Time (TBT)이 200ms 이하다
- Cumulative Layout Shift (CLS)가 0.1 이하다

**검증 방법**:
```bash
npm run build
npm run start
lighthouse http://localhost:3000 --output html --output-path .moai/reports/lighthouse-ui-design-001.html
```
- 보고서에서 Performance 점수 확인
- Core Web Vitals 메트릭 확인

---

### Scenario 4.2: Accessibility 100점

**Given**: 모든 컴포넌트가 구현되었을 때
**When**: Lighthouse Accessibility 테스트를 실행하면
**Then**:
- Accessibility 점수가 100점이다
- ARIA 속성 누락 경고가 없다
- 색상 대비가 WCAG AAA 기준(7:1)을 충족한다

**검증 방법**:
- Lighthouse Accessibility 섹션 확인
- WebAIM Contrast Checker로 Primary/Accent 색상 검증
- Storybook A11y Addon에서 경고 없음 확인

---

## AC5: 첫인상 테스트 4.5/5

### Scenario 5.1: 전문성 평가

**Given**: 참가자 20명에게 랜딩 페이지를 5초 노출했을 때
**When**: "이 제품이 전문적으로 보입니까?" 질문에 응답하면
**Then**:
- 평균 점수가 4.5/5 이상이다
- 5점 응답자가 50% 이상이다

**검증 방법**:
- `.moai/reports/first-impression-ui-design-001.csv` 데이터 분석
- 질문 1번 평균 계산: `SUM(scores) / 20 >= 4.5`

---

### Scenario 5.2: 구독 의향 평가

**Given**: 참가자 20명에게 랜딩 페이지를 5초 노출했을 때
**When**: "이 제품을 구독하고 싶습니까?" 질문에 응답하면
**Then**:
- 평균 점수가 4.5/5 이상이다
- 4점 이하 응답자가 20% 미만이다

**검증 방법**:
- 질문 2번 평균 계산
- 4점 이하 응답자 비율 확인: `COUNT(score <= 4) / 20 < 0.2`

---

### Scenario 5.3: 매력도 평가

**Given**: 참가자 20명에게 랜딩 페이지를 5초 노출했을 때
**When**: "디자인이 매력적입니까?" 질문에 응답하면
**Then**:
- 평균 점수가 4.5/5 이상이다
- 표준편차가 0.7 이하다 (일관된 평가)

**검증 방법**:
- 질문 3번 평균 및 표준편차 계산
- Excel/Python으로 분석: `STDEV(scores) <= 0.7`

---

## AC6: NPS 50점 이상

### Scenario 6.1: NPS 계산

**Given**: 베타 사용자 30명에게 NPS 설문을 발송했을 때
**When**: "이 제품을 동료에게 추천하시겠습니까?" (0-10점) 응답을 수집하면
**Then**:
- NPS 점수가 50점 이상이다
- 추천자(9-10점) 비율이 60% 이상이다
- 비추천자(0-6점) 비율이 10% 이하다

**검증 방법**:
- 응답 분류:
  - Promoter (9-10점): 추천자
  - Passive (7-8점): 중립자
  - Detractor (0-6점): 비추천자
- NPS 계산: `(Promoter % - Detractor %) >= 50`

**예시**:
- Promoter: 18명 (60%)
- Passive: 9명 (30%)
- Detractor: 3명 (10%)
- NPS = 60 - 10 = 50 ✅

---

## AC7: 심미성 평가 4.0/5

### Scenario 7.1: Attrakdiff 미니 설문

**Given**: 베타 사용자 30명에게 심미성 설문을 발송했을 때
**When**: 5개 질문(아름답다, 창의적이다, 세련되었다, 조화롭다, 매력적이다)에 응답하면
**Then**:
- 5개 질문 평균이 4.0/5 이상이다
- 각 질문별 점수가 3.8/5 이상이다 (최하 질문 기준)

**검증 방법**:
- `.moai/reports/aesthetic-ui-design-001.csv` 데이터 분석
- 전체 평균: `SUM(all_scores) / (30 * 5) >= 4.0`
- 최저 질문 평균: `MIN(avg_per_question) >= 3.8`

---

## AC8: 반응형 Grid 컬럼 조정

### Scenario 8.1: Mobile 뷰포트

**Given**: 사용자가 Mobile 기기(너비 375px)로 접속했을 때
**When**: Grid 컴포넌트가 렌더링되면
**Then**:
- Grid 컬럼 수가 4개다
- 각 컬럼 너비가 동일하다 (`grid-template-columns: repeat(4, 1fr)`)

**검증 방법**:
- Chrome DevTools → Device Toolbar → iPhone SE (375x667)
- Grid 컴포넌트 검사: `grid-template-columns` 값 확인

---

### Scenario 8.2: Tablet 뷰포트

**Given**: 사용자가 Tablet 기기(너비 768px)로 접속했을 때
**When**: Grid 컴포넌트가 렌더링되면
**Then**:
- Grid 컬럼 수가 8개다

**검증 방법**:
- DevTools → iPad (768x1024)
- `grid-template-columns: repeat(8, 1fr)` 확인

---

### Scenario 8.3: Desktop 뷰포트

**Given**: 사용자가 Desktop 브라우저(너비 1440px)로 접속했을 때
**When**: Grid 컴포넌트가 렌더링되면
**Then**:
- Grid 컬럼 수가 12개다

**검증 방법**:
- DevTools → Responsive → 1440px
- `grid-template-columns: repeat(12, 1fr)` 확인

---

## AC9: Modal 키보드 접근성

### Scenario 9.1: ESC 키로 Modal 닫기

**Given**: 사용자가 Modal을 열었을 때
**When**: ESC 키를 누르면
**Then**:
- Modal이 닫힌다
- `onClose` 콜백이 호출된다
- 포커스가 Modal 트리거 버튼으로 돌아간다

**검증 방법**:
- Storybook Modal Story 열기
- Open 버튼 클릭 → ESC 키 누르기
- Modal 닫힘 + 포커스 위치 확인

---

### Scenario 9.2: Focus Trap 작동

**Given**: 사용자가 Modal을 열었을 때
**When**: Tab 키를 반복해서 누르면
**Then**:
- 포커스가 Modal 내부 요소들 사이에서만 순환한다
- Modal 외부 요소로 포커스가 이동하지 않는다

**검증 방법**:
- Modal 열기
- Tab 키 10회 연속 누르기
- 포커스가 Modal 내부에 갇혀 있는지 확인 (react-focus-lock)

---

## AC10: Storybook 문서 완성도

### Scenario 10.1: 모든 컴포넌트에 Story 존재

**Given**: 15개 컴포넌트가 구현되었을 때
**When**: Storybook을 실행하면
**Then**:
- 15개 컴포넌트 각각에 최소 3개 Story가 있다 (총 45개 이상)
- Story 제목:
  - Default
  - Interactive (호버, 클릭 등)
  - Edge Case (에러, 로딩, 비활성화 등)

**검증 방법**:
```bash
npm run storybook
```
- Storybook 사이드바에서 컴포넌트 목록 확인
- 각 컴포넌트 클릭하여 Story 개수 확인

---

### Scenario 10.2: Props Table 존재

**Given**: 각 컴포넌트 Story를 열었을 때
**When**: "Controls" 탭을 클릭하면
**Then**:
- Props Table이 표시된다
- 각 Prop의 타입, 기본값, 설명이 있다
- Controls를 통해 실시간 Prop 변경이 가능하다

**검증 방법**:
- Button Story → Controls 탭
- `variant` Prop을 'primary' → 'secondary'로 변경
- 버튼 스타일 즉시 변경 확인

---

## AC11: Color Contrast 검증

### Scenario 11.1: Primary 색상 대비

**Given**: Primary Button (#1e293b 배경 + 흰색 텍스트)일 때
**When**: WebAIM Contrast Checker로 검증하면
**Then**:
- 대비 비율이 7:1 이상이다 (WCAG AAA 통과)

**검증 방법**:
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- Foreground: #ffffff
- Background: #1e293b
- 결과: 대비 비율 확인

---

### Scenario 11.2: Accent 색상 대비

**Given**: Accent Button (#8b5cf6 배경 + 흰색 텍스트)일 때
**When**: WebAIM Contrast Checker로 검증하면
**Then**:
- 대비 비율이 7:1 이상이다

**검증 방법**:
- Foreground: #ffffff
- Background: #8b5cf6
- 대비 비율 7:1+ 확인

---

## AC12: Storybook A11y Addon 경고 없음

### Scenario 12.1: 접근성 자동 검증

**Given**: Storybook A11y Addon이 설치되었을 때
**When**: 각 Story를 렌더링하면
**Then**:
- A11y 탭에 Violations가 0개다
- ARIA 속성 누락 경고가 없다
- 색상 대비 경고가 없다

**검증 방법**:
- Storybook → Button Story → Accessibility 탭
- "Violations" 섹션이 비어 있는지 확인
- 15개 컴포넌트 모두 반복 검증

---

## Definition of Done (완료 조건)

### 문서 작성
- ✅ spec.md 작성 완료
- ✅ plan.md 작성 완료
- ✅ acceptance.md 작성 완료 (본 문서)

### 구현 완료
- ✅ 15개 컴포넌트 구현 완료
- ✅ Storybook Stories 45개 이상 작성
- ✅ 디자인 토큰 4개 파일 생성

### 검증 완료
- ✅ Lighthouse Performance 90+
- ✅ Lighthouse Accessibility 100
- ✅ 첫인상 테스트 4.5/5 (n=20)
- ✅ NPS 50+ (n=30)
- ✅ 심미성 평가 4.0/5 (n=30)
- ✅ Storybook A11y 경고 0개
- ✅ WebAIM Contrast Checker 통과 (7:1+)

### 테스트 완료
- ✅ Unit Test (각 컴포넌트)
- ✅ Integration Test (Modal + Toast 등)
- ✅ E2E Test (주요 사용자 플로우)

### 문서화 완료
- ✅ Storybook 문서 완성 (Props Table, Usage 예시)
- ✅ README 업데이트 (디자인 시스템 섹션 추가)

---

**작성일**: 2025-10-10
**작성자**: @sonheungmin
**추적 태그**: @SPEC:UI-DESIGN-001
