---
id: SPEC-FRONTEND-MIGRATION-002-ACCEPTANCE
version: 1.0.0
status: draft
created: 2025-11-23
updated: 2025-11-23
author: "@spec-builder"
spec_ref: SPEC-FRONTEND-MIGRATION-002
---

# @ACCEPTANCE:FRONTEND-MIGRATION-002 수락 기준

> **English**: Acceptance Criteria for Agent Detail/History Pages Migration

## 1. 테스트 시나리오 (Test Scenarios)

### 1.1 AgentDetailCard 컴포넌트

#### TC-001: 기본 렌더링

```gherkin
Given 에이전트 데이터가 제공되면
When AgentDetailCard 컴포넌트가 렌더링되면
Then 에이전트 이름, 레벨, 희귀도가 표시되어야 한다
And 경험치 진행바가 표시되어야 한다
And 통계 정보 (문서 수, 쿼리 수, 품질 점수)가 표시되어야 한다
```

#### TC-002: 커버리지 통계 표시

```gherkin
Given 커버리지 데이터가 로딩되면
When 커버리지 데이터가 존재하면
Then 커버리지 퍼센트와 진행바가 표시되어야 한다
And 커버된 문서 수가 표시되어야 한다
```

#### TC-003: 희귀도별 테두리 스타일

```gherkin
Given 에이전트 희귀도가 "Common"이면
When 컴포넌트가 렌더링되면
Then 회색 테두리가 적용되어야 한다

Given 에이전트 희귀도가 "Rare"이면
When 컴포넌트가 렌더링되면
Then 파란색 테두리가 적용되어야 한다

Given 에이전트 희귀도가 "Epic"이면
When 컴포넌트가 렌더링되면
Then 보라색 테두리가 적용되어야 한다

Given 에이전트 희귀도가 "Legendary"이면
When 컴포넌트가 렌더링되면
Then 금색 테두리가 적용되어야 한다
```

### 1.2 LevelUpTimeline 컴포넌트

#### TC-004: 타임라인 렌더링

```gherkin
Given 에이전트 데이터가 제공되면
When LevelUpTimeline 컴포넌트가 렌더링되면
Then 레벨업 히스토리가 시간순으로 표시되어야 한다
```

### 1.3 XPAwardButton 컴포넌트

#### TC-005: XP 수여 기능

```gherkin
Given XP Award 버튼이 표시되면
When 사용자가 버튼을 클릭하면
Then XP가 에이전트에게 부여되어야 한다
And 성공 메시지가 표시되어야 한다
```

#### TC-006: 레벨업 트리거

```gherkin
Given 에이전트가 레벨업 직전 XP 상태이면
When XP를 부여하여 레벨업 조건을 충족하면
Then onLevelUp 콜백이 호출되어야 한다
And 이전 레벨과 새 레벨이 전달되어야 한다
```

### 1.4 CoverageChart 컴포넌트

#### TC-007: 차트 렌더링

```gherkin
Given 커버리지 히스토리 데이터가 제공되면
When CoverageChart 컴포넌트가 렌더링되면
Then 라인 차트가 표시되어야 한다
And X축에 날짜가 표시되어야 한다
And Y축에 커버리지 퍼센트 (0-100)가 표시되어야 한다
```

#### TC-008: 툴팁 표시

```gherkin
Given 차트가 렌더링되면
When 사용자가 데이터 포인트에 호버하면
Then 해당 날짜의 커버리지 값이 툴팁으로 표시되어야 한다
```

### 1.5 ChartContainer 컴포넌트

#### TC-009: 기간 필터 기능

```gherkin
Given ChartContainer가 렌더링되면
When 사용자가 기간 필터 (7일, 30일, 90일)를 선택하면
Then onPeriodChange 콜백이 선택된 일수와 함께 호출되어야 한다
```

### 1.6 XPGrowthChart 컴포넌트

#### TC-010: XP 성장 차트 렌더링

```gherkin
Given XP 히스토리 데이터가 제공되면
When XPGrowthChart 컴포넌트가 렌더링되면
Then XP 성장 라인 차트가 표시되어야 한다
```

### 1.7 AgentDetailPage

#### TC-011: 페이지 로딩 상태

```gherkin
Given 에이전트 데이터가 로딩 중이면
When AgentDetailPage가 렌더링되면
Then 스켈레톤 UI가 표시되어야 한다
```

#### TC-012: 에러 상태 처리

```gherkin
Given 에이전트 데이터 로딩이 실패하면
When AgentDetailPage가 렌더링되면
Then 에러 메시지가 표시되어야 한다
And 재시도 버튼이 표시되어야 한다
When 재시도 버튼을 클릭하면
Then 데이터 로딩이 재시도되어야 한다
```

#### TC-013: 존재하지 않는 에이전트

```gherkin
Given 요청한 ID의 에이전트가 존재하지 않으면
When AgentDetailPage가 렌더링되면
Then "Agent not found" 메시지가 표시되어야 한다
And 홈으로 돌아가는 링크가 표시되어야 한다
```

#### TC-014: 네비게이션 기능

```gherkin
Given AgentDetailPage가 정상 렌더링되면
When "Back" 버튼을 클릭하면
Then 이전 페이지로 이동해야 한다

When "View History" 버튼을 클릭하면
Then /agents/[id]/history 페이지로 이동해야 한다
```

#### TC-015: 레벨업 모달 표시

```gherkin
Given 에이전트 상세 페이지가 표시되면
When 에이전트가 레벨업하면
Then LevelUpModal이 표시되어야 한다
And 이전 레벨과 새 레벨이 표시되어야 한다
```

### 1.8 AgentHistoryPage

#### TC-016: 히스토리 페이지 로딩

```gherkin
Given 에이전트 ID가 유효하면
When AgentHistoryPage가 렌더링되면
Then 에이전트 이름과 레벨이 헤더에 표시되어야 한다
And 커버리지 차트가 표시되어야 한다
And XP 성장 차트가 표시되어야 한다
And 요약 통계가 표시되어야 한다
```

#### TC-017: 기간 필터 적용

```gherkin
Given 히스토리 데이터가 로딩되면
When 사용자가 기간을 7일로 선택하면
Then 최근 7일 데이터만 차트에 표시되어야 한다

When 사용자가 기간을 90일로 선택하면
Then 최근 90일 데이터가 차트에 표시되어야 한다
```

#### TC-018: 빈 히스토리 상태

```gherkin
Given 히스토리 데이터가 없으면
When AgentHistoryPage가 렌더링되면
Then "No history data available" 메시지가 표시되어야 한다
```

#### TC-019: 히스토리 페이지 네비게이션

```gherkin
Given AgentHistoryPage가 렌더링되면
When "Back" 버튼을 클릭하면
Then 이전 페이지로 이동해야 한다

When "View Details" 버튼을 클릭하면
Then /agents/[id] 페이지로 이동해야 한다
```

---

## 2. 품질 게이트 기준 (Quality Gate Criteria)

### 2.1 코드 품질

| 기준 | 목표값 | 측정 방법 |
|------|--------|-----------|
| TypeScript 컴파일 | 에러 0개 | `npm run type-check` |
| ESLint | 에러 0개, 경고 최소화 | `npm run lint` |
| 테스트 커버리지 | 80% 이상 | `npm run test:coverage` |

### 2.2 기능 요구사항

| 요구사항 ID | 검증 항목 | 합격 기준 |
|-------------|-----------|-----------|
| REQ-U-001 | 에이전트 상세 페이지 | 모든 정보 표시 |
| REQ-U-002 | 히스토리 페이지 | 차트 및 통계 표시 |
| REQ-U-003 | XP 수여 기능 | 버튼 클릭 시 XP 부여 |
| REQ-U-004 | 차트 시각화 | 커버리지, XP 차트 렌더링 |
| REQ-E-001~006 | 이벤트 처리 | 모든 이벤트 핸들러 동작 |
| REQ-S-001~003 | 상태 관리 | 로딩/에러 상태 표시 |
| REQ-C-001~005 | 제약사항 준수 | 모든 제약사항 충족 |

### 2.3 브라우저 호환성

| 브라우저 | 버전 | 상태 |
|----------|------|------|
| Chrome | 최신 | 필수 |
| Firefox | 최신 | 필수 |
| Safari | 최신 | 권장 |
| Edge | 최신 | 권장 |

---

## 3. 검증 방법 및 도구 (Verification Methods)

### 3.1 자동화 테스트

```bash
# 단위 테스트 실행
npm run test

# 특정 컴포넌트 테스트
npm run test -- AgentDetailCard

# 커버리지 리포트
npm run test:coverage
```

### 3.2 수동 검증 체크리스트

- [ ] `/agents` 페이지에서 에이전트 클릭 시 상세 페이지로 이동
- [ ] 상세 페이지에서 에이전트 정보가 올바르게 표시됨
- [ ] "View History" 버튼 클릭 시 히스토리 페이지로 이동
- [ ] 히스토리 페이지에서 차트가 올바르게 렌더링됨
- [ ] 기간 필터 변경 시 차트 데이터가 업데이트됨
- [ ] 뒤로 가기 버튼이 정상 동작함
- [ ] XP Award 버튼 클릭 시 XP가 부여됨
- [ ] 레벨업 시 모달이 표시됨

---

## 4. Definition of Done

### 4.1 컴포넌트 완료 기준

- [ ] 소스 코드 마이그레이션 완료
- [ ] "use client" 지시어 적용 (필요시)
- [ ] TypeScript 타입 정의 완료
- [ ] 단위 테스트 작성 및 통과
- [ ] ESLint 에러 없음

### 4.2 페이지 완료 기준

- [ ] 라우팅 설정 완료 (`app/(dashboard)/agents/[id]/...`)
- [ ] react-router-dom → next/navigation 변환 완료
- [ ] 모든 컴포넌트 통합 완료
- [ ] 통합 테스트 통과
- [ ] 네비게이션 플로우 검증 완료

### 4.3 전체 SPEC 완료 기준

- [ ] 모든 6개 컴포넌트 마이그레이션 완료
- [ ] 2개 페이지 라우트 동작 확인
- [ ] 모든 테스트 시나리오 (TC-001 ~ TC-019) 통과
- [ ] 품질 게이트 기준 충족
- [ ] 코드 리뷰 완료 (해당 시)
- [ ] 문서 동기화 완료 (`/alfred:3-sync`)

---

_이 문서는 `/alfred:2-run SPEC-FRONTEND-MIGRATION-002` 완료 검증 시 사용됩니다._
