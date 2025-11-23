---
id: SPEC-FRONTEND-MIGRATION-001-ACCEPTANCE
version: 1.0.0
status: draft
created: 2025-11-21
updated: 2025-11-21
author: "@spec-builder"
parent_spec: SPEC-FRONTEND-MIGRATION-001
---

# @SPEC:FRONTEND-MIGRATION-001 수락 기준

> **English**: Acceptance Criteria for Vite to Next.js Migration

## HISTORY

### v1.0.0 (2025-11-21)

- **INITIAL**: 수락 기준 초안 작성
- **AUTHOR**: @spec-builder
- **SECTIONS**: 테스트 시나리오, 품질 게이트, 검증 방법, DoD

---

## 1. 테스트 시나리오 (Given-When-Then)

### 1.1 유틸리티 함수 테스트

#### TC-UTIL-001: Level Calculator

```gherkin
Feature: Level Calculator
  레벨 계산 유틸리티가 정확하게 동작해야 한다.

  Scenario: XP로 레벨 계산
    Given 에이전트의 XP가 1500인 경우
    When levelCalculator.calculateLevel(1500)을 호출하면
    Then 레벨 5가 반환되어야 한다

  Scenario: 다음 레벨까지 필요 XP 계산
    Given 현재 레벨이 3인 경우
    When levelCalculator.xpToNextLevel(3)을 호출하면
    Then 다음 레벨까지 필요한 XP가 반환되어야 한다

  Scenario: 레벨 진행률 계산
    Given 현재 XP가 1200이고 레벨이 4인 경우
    When levelCalculator.levelProgress(1200, 4)를 호출하면
    Then 0과 1 사이의 진행률이 반환되어야 한다
```

#### TC-UTIL-002: XP Calculator

```gherkin
Feature: XP Calculator
  XP 계산 유틸리티가 정확하게 동작해야 한다.

  Scenario: 작업 완료 시 XP 계산
    Given 작업 유형이 "task_complete"인 경우
    When xpCalculator.calculateXP("task_complete")를 호출하면
    Then 해당 작업 유형에 맞는 XP가 반환되어야 한다

  Scenario: 품질 보너스 XP 계산
    Given 품질 점수가 95%인 경우
    When xpCalculator.qualityBonus(0.95)를 호출하면
    Then 보너스 XP가 반환되어야 한다
```

#### TC-UTIL-003: Rarity Resolver

```gherkin
Feature: Rarity Resolver
  희귀도 결정 유틸리티가 정확하게 동작해야 한다.

  Scenario: 레벨 기반 희귀도 결정
    Given 에이전트 레벨이 10인 경우
    When rarityResolver.resolveRarity(10)을 호출하면
    Then "rare" 희귀도가 반환되어야 한다

  Scenario: 희귀도별 색상 반환
    Given 희귀도가 "legendary"인 경우
    When rarityResolver.getRarityColor("legendary")를 호출하면
    Then 해당 희귀도의 색상 코드가 반환되어야 한다
```

#### TC-UTIL-004: Quality Score Calculator

```gherkin
Feature: Quality Score Calculator
  품질 점수 계산이 정확하게 동작해야 한다.

  Scenario: 에이전트 품질 점수 계산
    Given 에이전트 성능 메트릭이 제공된 경우
    When qualityScoreCalculator.calculate(metrics)를 호출하면
    Then 0-100 사이의 품질 점수가 반환되어야 한다
```

---

### 1.2 Agent Card 컴포넌트 테스트

#### TC-AC-001: AgentCard 렌더링

```gherkin
Feature: Agent Card Component
  Agent Card가 올바르게 렌더링되어야 한다.

  Scenario: 기본 카드 렌더링
    Given 에이전트 데이터가 제공된 경우
    When AgentCard 컴포넌트가 렌더링되면
    Then 에이전트 이름, 레벨, XP가 표시되어야 한다
    And 희귀도 뱃지가 표시되어야 한다
    And 아바타 이미지가 표시되어야 한다

  Scenario: 애니메이션 동작
    Given AgentCard가 마운트되는 경우
    When framer-motion 애니메이션이 적용되면
    Then 페이드인 애니메이션이 재생되어야 한다
```

#### TC-AC-002: ProgressBar 동작

```gherkin
Feature: Progress Bar Component
  경험치 바가 올바르게 동작해야 한다.

  Scenario: 진행률 표시
    Given 현재 XP 진행률이 75%인 경우
    When ProgressBar 컴포넌트가 렌더링되면
    Then 바가 75% 채워져 표시되어야 한다

  Scenario: 애니메이션 업데이트
    Given XP가 증가하는 경우
    When 진행률이 변경되면
    Then 부드러운 애니메이션으로 바가 업데이트되어야 한다
```

#### TC-AC-003: LevelUpModal 동작

```gherkin
Feature: Level Up Modal
  레벨업 모달이 올바르게 동작해야 한다.

  Scenario: 모달 표시
    Given 에이전트가 레벨업한 경우
    When LevelUpModal이 표시되면
    Then 모달이 화면 중앙에 나타나야 한다
    And confetti 효과가 재생되어야 한다

  Scenario: 모달 닫기
    Given LevelUpModal이 표시된 상태에서
    When 사용자가 닫기 버튼을 클릭하면
    Then 모달이 페이드아웃 애니메이션과 함께 닫혀야 한다
```

---

### 1.3 Taxonomy 컴포넌트 테스트

#### TC-TX-001: TaxonomyTreeView 렌더링

```gherkin
Feature: Taxonomy Tree View
  택소노미 트리 뷰가 올바르게 렌더링되어야 한다.

  Scenario: 트리 초기 렌더링
    Given 택소노미 데이터가 로드된 경우
    When TaxonomyTreeView가 렌더링되면
    Then 노드들이 그래프 형태로 표시되어야 한다
    And 엣지가 노드들을 연결해야 한다

  Scenario: SSR 호환성
    Given Next.js SSR 환경에서
    When 페이지가 서버에서 렌더링될 때
    Then @xyflow/react가 클라이언트에서만 로드되어야 한다
    And 하이드레이션 에러가 발생하지 않아야 한다
```

#### TC-TX-002: TaxonomyNode 상호작용

```gherkin
Feature: Taxonomy Node Interaction
  택소노미 노드 상호작용이 올바르게 동작해야 한다.

  Scenario: 노드 선택
    Given 택소노미 트리가 표시된 상태에서
    When 사용자가 노드를 클릭하면
    Then 노드가 선택 상태로 변경되어야 한다
    And TaxonomyDetailPanel이 표시되어야 한다

  Scenario: 노드 확장/축소
    Given 자식 노드가 있는 부모 노드가 있는 경우
    When 사용자가 확장 아이콘을 클릭하면
    Then 자식 노드들이 표시되거나 숨겨져야 한다
```

#### TC-TX-003: TaxonomySearchFilter 동작

```gherkin
Feature: Taxonomy Search Filter
  택소노미 검색 필터가 올바르게 동작해야 한다.

  Scenario: 검색어 입력
    Given 택소노미 트리가 표시된 상태에서
    When 사용자가 검색어를 입력하면
    Then 검색어와 일치하는 노드만 하이라이트되어야 한다

  Scenario: 필터 초기화
    Given 검색 필터가 적용된 상태에서
    When 사용자가 초기화 버튼을 클릭하면
    Then 모든 노드가 다시 표시되어야 한다
```

#### TC-TX-004: Zustand Store 동작

```gherkin
Feature: Taxonomy Store
  택소노미 Zustand 스토어가 올바르게 동작해야 한다.

  Scenario: 노드 선택 상태 관리
    Given useTaxonomyStore가 초기화된 경우
    When setSelectedNode("node-1")을 호출하면
    Then selectedNode가 "node-1"으로 설정되어야 한다

  Scenario: 확장된 노드 관리
    Given 확장된 노드 목록이 비어있는 경우
    When toggleExpandedNode("node-1")을 호출하면
    Then expandedNodes에 "node-1"이 추가되어야 한다
```

---

### 1.4 통합 테스트

#### TC-INT-001: Agent 페이지 통합

```gherkin
Feature: Agents Page Integration
  Agent 페이지에서 AgentCard가 통합되어야 한다.

  Scenario: 에이전트 목록 표시
    Given /agents 페이지에 접근한 경우
    When 에이전트 목록이 로드되면
    Then VirtualList를 통해 AgentCard들이 렌더링되어야 한다
    And 스크롤 성능이 저하되지 않아야 한다

  Scenario: 에이전트 상세 보기
    Given 에이전트 카드가 표시된 상태에서
    When 사용자가 카드를 클릭하면
    Then AgentDetailCard가 표시되어야 한다
```

#### TC-INT-002: Taxonomy 페이지 통합

```gherkin
Feature: Taxonomy Page Integration
  Taxonomy 페이지에서 모든 컴포넌트가 통합되어야 한다.

  Scenario: 택소노미 페이지 로드
    Given /taxonomy 페이지에 접근한 경우
    When 페이지가 로드되면
    Then TaxonomyTreeView가 표시되어야 한다
    And TaxonomySearchFilter가 동작해야 한다
    And TaxonomyLayoutToggle이 레이아웃을 변경할 수 있어야 한다
```

#### TC-INT-003: 대시보드 홈 통합

```gherkin
Feature: Dashboard Home Integration
  대시보드 홈에서 StatCard와 RecommendationPanel이 통합되어야 한다.

  Scenario: 대시보드 홈 로드
    Given / 페이지에 접근한 경우
    When 페이지가 로드되면
    Then StatCard들이 통계를 표시해야 한다
    And RecommendationPanel이 추천 에이전트를 표시해야 한다
```

---

## 2. 품질 게이트 기준

### 2.1 테스트 커버리지

| 카테고리 | 최소 커버리지 | 목표 커버리지 |
|----------|--------------|--------------|
| 유틸리티 함수 | 90% | 100% |
| 컴포넌트 (단위) | 80% | 90% |
| 컴포넌트 (통합) | 70% | 80% |
| 전체 | 80% | 85% |

### 2.2 성능 기준

| 메트릭 | 기준값 | 측정 방법 |
|--------|--------|----------|
| 번들 크기 증가 | < 30% | `npm run build` 출력 비교 |
| First Contentful Paint | < 1.5s | Lighthouse |
| Time to Interactive | < 3.5s | Lighthouse |
| Cumulative Layout Shift | < 0.1 | Lighthouse |
| VirtualList 60fps | 유지 | Chrome DevTools Performance |

### 2.3 호환성 기준

| 항목 | 기준 |
|------|------|
| SSR 호환성 | 하이드레이션 에러 0건 |
| 브라우저 지원 | Chrome 90+, Firefox 88+, Safari 14+, Edge 90+ |
| 반응형 | 320px ~ 2560px 해상도 지원 |
| 접근성 | WCAG 2.1 AA 준수 |

### 2.4 코드 품질 기준

| 검사 항목 | 기준 |
|----------|------|
| ESLint 에러 | 0건 |
| TypeScript 에러 | 0건 |
| "use client" 누락 | 0건 |
| 미사용 의존성 | 0건 |

---

## 3. 검증 방법 및 도구

### 3.1 자동화 테스트

```bash
# 단위 테스트 실행
cd apps/frontend
npm test

# 커버리지 리포트
npm run test:coverage

# 타입 검사
npm run type-check

# 린트 검사
npm run lint
```

### 3.2 빌드 검증

```bash
# 프로덕션 빌드
npm run build

# 빌드 결과 분석
npx @next/bundle-analyzer
```

### 3.3 성능 테스트

```bash
# Lighthouse CI
npx lighthouse http://localhost:3000 --output=json --output-path=./lighthouse-report.json

# 번들 크기 비교 (마이그레이션 전후)
npm run build 2>&1 | grep "First Load JS"
```

### 3.4 SSR 호환성 테스트

```bash
# 개발 서버 시작
npm run dev

# 브라우저 콘솔에서 하이드레이션 에러 확인
# Chrome DevTools > Console > Filter: "Hydration"
```

### 3.5 시각적 회귀 테스트

1. 마이그레이션 전 Vite 앱 스크린샷 캡처
2. 마이그레이션 후 Next.js 앱 스크린샷 캡처
3. 시각적 차이 비교 (수동 또는 자동화 도구)

---

## 4. Definition of Done (DoD)

### 4.1 Phase 1 완료 조건

- [ ] 모든 의존성이 설치되고 버전 충돌이 없음
- [ ] 4개 유틸리티 함수가 마이그레이션됨
- [ ] 4개 유틸리티 테스트가 통과함
- [ ] 유틸리티 커버리지 90% 이상

### 4.2 Phase 2 완료 조건

- [ ] 3개 Common 컴포넌트가 마이그레이션됨
- [ ] "use client" 지시어가 올바르게 적용됨
- [ ] Tailwind 스타일이 정상 동작함
- [ ] Common 컴포넌트 테스트가 통과함

### 4.3 Phase 3 완료 조건

- [ ] 11개 Agent Card 컴포넌트가 마이그레이션됨
- [ ] framer-motion 애니메이션이 동작함
- [ ] react-confetti가 LevelUpModal에서 동작함
- [ ] Agent Card 컴포넌트 테스트가 통과함

### 4.4 Phase 4 완료 조건

- [ ] 8개 Taxonomy 컴포넌트가 마이그레이션됨
- [ ] Zustand 스토어가 동작함
- [ ] @xyflow/react가 SSR 환경에서 동작함
- [ ] 키보드 네비게이션이 동작함
- [ ] Taxonomy 컴포넌트 테스트가 통과함

### 4.5 Phase 5 완료 조건

- [ ] 2개 Home 컴포넌트가 마이그레이션됨
- [ ] Agents 페이지에 AgentCard가 통합됨
- [ ] 대시보드 홈에 StatCard/RecommendationPanel이 통합됨
- [ ] 페이지 레벨 통합 테스트가 통과함

### 4.6 Phase 6 (최종) 완료 조건

- [ ] 전체 테스트 커버리지 80% 이상
- [ ] ESLint/TypeScript 에러 0건
- [ ] 빌드 성공
- [ ] 번들 크기 증가 30% 미만
- [ ] Lighthouse 성능 점수 80점 이상
- [ ] 하이드레이션 에러 0건
- [ ] 모든 기존 기능이 동일하게 동작함

### 4.7 전체 SPEC 완료 조건

- [ ] 25개 컴포넌트 마이그레이션 완료
- [ ] 4개 유틸리티 마이그레이션 완료
- [ ] 1개 Zustand 스토어 마이그레이션 완료
- [ ] 모든 DoD 항목 충족
- [ ] 코드 리뷰 완료
- [ ] 문서화 완료 (@DOC:FRONTEND-MIGRATION-001)

---

## 5. 롤백 기준

다음 조건 중 하나라도 해당되면 롤백을 고려:

1. **치명적 버그**: 주요 기능이 동작하지 않음
2. **성능 저하**: 번들 크기 50% 이상 증가 또는 Lighthouse 점수 60점 미만
3. **호환성 문제**: SSR 에러가 지속적으로 발생
4. **일정 초과**: 예상 일정의 200% 초과

---

## SUMMARY (English)

The acceptance criteria define comprehensive test scenarios using Given-When-Then format across utilities (4 scenarios), Agent Card components (3 scenarios), Taxonomy components (4 scenarios), and integration tests (3 scenarios). Quality gates specify minimum 80% overall test coverage, bundle size increase under 30%, Lighthouse performance score above 80, and zero hydration errors.

Verification methods include automated testing with Jest, build analysis with Next.js bundle analyzer, performance testing with Lighthouse CI, and visual regression testing. The Definition of Done outlines specific completion criteria for each of the 6 phases, with the final phase requiring all 25 components migrated, zero ESLint/TypeScript errors, and full documentation.

Rollback criteria are established for critical bugs, significant performance degradation (50%+ bundle increase or Lighthouse below 60), persistent SSR compatibility issues, or schedule overrun beyond 200%.

---

_이 문서는 `/alfred:3-sync SPEC-FRONTEND-MIGRATION-001` 실행 시 검증 기준으로 사용됩니다._
