# Acceptance Criteria: SPEC-FRONTEND-INTEGRATION-001

> Pokemon-Style Agent Card System - Backend Integration & 9 Core Features

**SPEC ID**: FRONTEND-INTEGRATION-001
**Version**: 0.0.1
**Status**: draft
**Priority**: high
**Created**: 2025-10-30
**Author**: @bridge25

---

## 📋 개요

이 문서는 SPEC-FRONTEND-INTEGRATION-001의 수락 기준을 Given-When-Then 형식으로 정의합니다. 각 Task마다 최소 1개 이상의 시나리오를 포함하며, 총 9개 Task에 대해 15개의 시나리오를 제공합니다.

---

## Phase 1: 백엔드 통합 & 환경 설정

### Task 1: Backend API Integration

#### Scenario 1.1: 환경 변수 정상 로드

**Given**: `.env` 파일에 다음 변수가 설정되어 있다:
```
VITE_API_URL=http://localhost:8000
VITE_API_KEY=test_api_key_12345
VITE_API_TIMEOUT=10000
```

**When**: 프론트엔드 앱이 시작된다

**Then**:
- [x] `env.VITE_API_URL`이 "http://localhost:8000"이다
- [x] `env.VITE_API_KEY`가 "test_api_key_12345"이다
- [x] `env.VITE_API_TIMEOUT`이 10000이다
- [x] 앱이 에러 없이 정상 실행된다

---

#### Scenario 1.2: 환경 변수 누락 시 에러

**Given**: `.env` 파일에 `VITE_API_URL`이 설정되지 않았다

**When**: 프론트엔드 앱이 시작된다

**Then**:
- [x] Zod 검증 에러가 발생한다
- [x] 에러 메시지에 "Missing environment variable VITE_API_URL"이 포함된다
- [x] 앱이 실행되지 않는다
- [x] 콘솔에 명확한 에러 가이드가 출력된다

---

#### Scenario 1.3: API 401 Unauthorized 에러 처리

**Given**: API 클라이언트가 초기화되었다

**When**: `/api/v1/agents`를 호출했을 때 401 Unauthorized 응답을 받는다

**Then**:
- [x] `APIError`가 throw된다
- [x] `error.status`가 401이다
- [x] `error.detail`이 "API 키가 유효하지 않습니다"를 포함한다
- [x] TanStack Query 에러 상태에 표시된다

---

#### Scenario 1.4: API 타임아웃 처리

**Given**: API 클라이언트가 10초 타임아웃으로 설정되었다

**When**: `/api/v1/agents`를 호출했을 때 15초 동안 응답이 없다

**Then**:
- [x] 10초 후 타임아웃 에러가 발생한다
- [x] `APIError`가 throw된다
- [x] `error.detail`에 "네트워크 연결을 확인해주세요"가 포함된다
- [x] TanStack Query retry 로직이 실행된다 (최대 3회)

---

### Task 2: useAgents Hook Update

#### Scenario 2.1: 에이전트 목록 정상 조회

**Given**: 백엔드 `/api/v1/agents`가 다음 데이터를 반환한다:
```json
{
  "agents": [
    {
      "agent_id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Test Agent 1",
      "level": 3,
      "current_xp": 450,
      "total_documents": 100,
      "total_queries": 50,
      "avg_faithfulness": 0.85,
      "coverage_percent": 75.5
    }
  ],
  "total": 1
}
```

**When**: `useAgents()` 훅을 호출한다

**Then**:
- [x] `data` 배열에 1개의 에이전트가 있다
- [x] 첫 번째 에이전트의 `name`이 "Test Agent 1"이다
- [x] 첫 번째 에이전트의 `level`이 3이다
- [x] `isLoading`이 false이다
- [x] `error`가 undefined이다

---

#### Scenario 2.2: API 에러 시 재시도 로직

**Given**: 백엔드 `/api/v1/agents`가 첫 2번은 500 에러를 반환하고, 3번째는 성공한다

**When**: `useAgents()` 훅을 호출한다

**Then**:
- [x] 첫 번째 요청 실패 후 1초 대기
- [x] 두 번째 요청 실패 후 2초 대기
- [x] 세 번째 요청 성공
- [x] 최종적으로 `data`에 에이전트 목록이 있다
- [x] `error`가 undefined이다

---

#### Scenario 2.3: 캐싱 동작 확인

**Given**: `useAgents()` 훅으로 데이터를 한 번 조회했다

**When**: 30초 이내에 다시 `useAgents()` 훅을 호출한다

**Then**:
- [x] 새로운 네트워크 요청이 발생하지 않는다
- [x] 캐시된 데이터가 즉시 반환된다
- [x] `isLoading`이 false이다
- [x] `isFetching`이 false이다

---

## Phase 2: 라우팅 & 상세 페이지

### Task 3: Routing System

#### Scenario 3.1: 홈 페이지 라우팅

**Given**: 사용자가 브라우저 주소창에 "http://localhost:5173/"를 입력한다

**When**: 페이지가 로드된다

**Then**:
- [x] `HomePage` 컴포넌트가 렌더링된다
- [x] 에이전트 카드 그리드가 표시된다
- [x] 주소창 URL이 "/"이다

---

#### Scenario 3.2: 에이전트 상세 페이지 라우팅

**Given**: 사용자가 홈 페이지에서 에이전트 카드를 클릭한다

**When**: 에이전트 ID가 "123e4567-e89b-12d3-a456-426614174000"인 카드를 클릭한다

**Then**:
- [x] 주소창 URL이 "/agents/123e4567-e89b-12d3-a456-426614174000"로 변경된다
- [x] `AgentDetailPage` 컴포넌트가 렌더링된다
- [x] 에이전트 상세 정보가 표시된다

---

#### Scenario 3.3: 404 Not Found 처리

**Given**: 사용자가 브라우저 주소창에 존재하지 않는 경로를 입력한다

**When**: "http://localhost:5173/invalid-path"를 입력한다

**Then**:
- [x] `NotFoundPage` 컴포넌트가 렌더링된다
- [x] "페이지를 찾을 수 없습니다" 메시지가 표시된다
- [x] "홈으로 돌아가기" 링크가 있다
- [x] 링크 클릭 시 "/"로 이동한다

---

### Task 4: Data Synchronization Strategy

#### Scenario 4.1: Optimistic Update 성공

**Given**: 에이전트 상세 페이지에서 현재 XP가 450이다

**When**: 사용자가 "긍정 피드백 (+50 XP)" 버튼을 클릭한다

**Then**:
- [x] 즉시 UI에 XP가 500으로 표시된다 (Optimistic update)
- [x] 네트워크 요청이 백그라운드에서 전송된다
- [x] 서버 응답 성공 시 UI가 그대로 유지된다
- [x] Query가 invalidate되어 최신 데이터를 refetch한다

---

#### Scenario 4.2: Optimistic Update 실패 시 롤백

**Given**: 에이전트 상세 페이지에서 현재 XP가 450이다

**When**: 사용자가 "긍정 피드백 (+50 XP)" 버튼을 클릭했지만 서버가 500 에러를 반환한다

**Then**:
- [x] 즉시 UI에 XP가 500으로 표시된다 (Optimistic update)
- [x] 서버 응답 에러 시 UI가 450으로 롤백된다
- [x] 에러 메시지가 표시된다 ("XP 증가에 실패했습니다")
- [x] 사용자가 재시도 버튼을 클릭할 수 있다

---

### Task 5: Agent Detail Page

#### Scenario 5.1: 에이전트 상세 정보 표시

**Given**: 사용자가 "/agents/123e4567-e89b-12d3-a456-426614174000"에 접근한다

**When**: `useAgent()` 훅이 다음 데이터를 반환한다:
```json
{
  "agent_id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Breast Cancer Specialist",
  "level": 5,
  "current_xp": 1200,
  "total_documents": 250,
  "total_queries": 150,
  "avg_faithfulness": 0.92,
  "coverage_percent": 85.3
}
```

**Then**:
- [x] 에이전트 이름 "Breast Cancer Specialist"가 표시된다
- [x] 레벨 "Lv.5"가 표시된다
- [x] 희귀도 "EPIC"가 표시된다
- [x] XP 진행 바가 "1200 / 1500 XP" (80%)로 표시된다
- [x] 지식 "250개", 대화 "150회", 품질 "92%"가 표시된다
- [x] "히스토리 보기" 링크가 있다

---

#### Scenario 5.2: 에이전트 없음 (404)

**Given**: 사용자가 "/agents/non-existent-id"에 접근한다

**When**: `useAgent()` 훅이 404 에러를 반환한다

**Then**:
- [x] "에이전트를 찾을 수 없습니다" 메시지가 표시된다
- [x] "목록으로 돌아가기" 버튼이 있다
- [x] 버튼 클릭 시 "/"로 이동한다

---

## Phase 3: 인터랙션 시스템

### Task 6: XP Interaction System

#### Scenario 6.1: XP 증가 (대화 완료)

**Given**: 에이전트 상세 페이지에서 "Award XP" 섹션이 있다

**When**: 사용자가 "대화 완료 (+10 XP)" 버튼을 클릭한다

**Then**:
- [x] `useXPAward` mutation이 실행된다
- [x] 요청 body에 `{ "agentId": "...", "amount": 10, "reason": "chat" }`가 포함된다
- [x] Optimistic update로 즉시 UI에 반영된다
- [x] 플로팅 텍스트 "+10 XP"가 1초 동안 표시된다 (선택적)

---

#### Scenario 6.2: XP 증가 (RAGAS 보너스)

**Given**: 에이전트 상세 페이지에서 "Award XP" 섹션이 있다

**When**: 사용자가 "RAGAS 보너스 (+100 XP)" 버튼을 클릭한다

**Then**:
- [x] `useXPAward` mutation이 실행된다
- [x] 요청 body에 `{ "agentId": "...", "amount": 100, "reason": "ragas_bonus" }`가 포함된다
- [x] Optimistic update로 즉시 UI에 반영된다
- [x] 플로팅 텍스트 "+100 XP"가 1초 동안 표시된다 (선택적)
- [x] 특수 효과가 표시된다 (선택적)

---

### Task 7: Level-up Notifications

#### Scenario 7.1: 레벨업 감지 및 모달 표시

**Given**: 에이전트 상세 페이지에서 현재 레벨이 4이고 XP가 590이다

**When**: 5초 Polling 후 `/agents/:id`가 레벨 5, XP 610을 반환한다

**Then**:
- [x] 레벨 변경 감지 (4 → 5)
- [x] `LevelUpModal`이 표시된다
- [x] 모달에 "축하합니다! Lv.5 달성!" 메시지가 있다
- [x] 희귀도 변경 (Rare → Epic) 메시지가 있다
- [x] react-confetti 애니메이션이 3초 동안 표시된다
- [x] "확인" 버튼 클릭 시 모달이 닫힌다

---

#### Scenario 7.2: 레벨업 없이 XP만 증가

**Given**: 에이전트 상세 페이지에서 현재 레벨이 4이고 XP가 450이다

**When**: 5초 Polling 후 `/agents/:id`가 레벨 4, XP 460을 반환한다

**Then**:
- [x] 레벨 변경 없음 (4 → 4)
- [x] `LevelUpModal`이 표시되지 않는다
- [x] XP 진행 바만 업데이트된다 (450 → 460)

---

## Phase 4: 히스토리 & 분석

### Task 8: History Dashboard

#### Scenario 8.1: 커버리지 히스토리 차트 표시

**Given**: 사용자가 "/agents/123e4567-e89b-12d3-a456-426614174000/history"에 접근한다

**When**: `useCoverageHistory()` 훅이 다음 데이터를 반환한다:
```json
{
  "history": [
    { "date": "2025-10-01T00:00:00Z", "coverage": 70.5, "xp": 1000 },
    { "date": "2025-10-02T00:00:00Z", "coverage": 72.3, "xp": 1050 },
    { "date": "2025-10-03T00:00:00Z", "coverage": 75.0, "xp": 1150 }
  ]
}
```

**Then**:
- [x] `CoverageChart` 선 그래프가 렌더링된다
- [x] X축에 "10월 1일", "10월 2일", "10월 3일"이 표시된다
- [x] Y축에 "Coverage (%)" 레이블이 있다
- [x] 선 그래프가 70.5% → 72.3% → 75.0% 추세를 보인다
- [x] Tooltip에 마우스 오버 시 정확한 값이 표시된다

---

#### Scenario 8.2: XP 증가량 차트 표시

**Given**: 사용자가 히스토리 페이지에 접근한다

**When**: `useCoverageHistory()` 훅이 다음 데이터를 반환한다:
```json
{
  "history": [
    { "date": "2025-10-01T00:00:00Z", "coverage": 70.5, "xp": 1000 },
    { "date": "2025-10-02T00:00:00Z", "coverage": 72.3, "xp": 1050 },
    { "date": "2025-10-03T00:00:00Z", "coverage": 75.0, "xp": 1150 }
  ]
}
```

**Then**:
- [x] `XPGrowthChart` 막대 그래프가 렌더링된다
- [x] X축에 "10월 1일", "10월 2일", "10월 3일"이 표시된다
- [x] Y축에 "XP 증가량" 레이블이 있다
- [x] 막대 높이가 0 XP, +50 XP, +100 XP를 나타낸다 (일별 증가량)
- [x] Tooltip에 "+50 XP", "+100 XP" 형식으로 표시된다

---

#### Scenario 8.3: 기간 필터 변경

**Given**: 사용자가 히스토리 페이지에서 기본적으로 "30일" 필터가 선택되어 있다

**When**: 사용자가 "7일" 버튼을 클릭한다

**Then**:
- [x] "7일" 버튼이 활성화된다 (파란색 배경)
- [x] `useCoverageHistory` 훅이 `interval: 'daily'` 파라미터로 재호출된다
- [x] 차트가 최근 7일 데이터로 업데이트된다
- [x] 네트워크 요청이 새로 전송된다

---

## Phase 5: 성능 최적화

### Task 9: Performance Optimization

#### Scenario 9.1: 가상 스크롤 활성화 (100+ 에이전트)

**Given**: 백엔드가 150개의 에이전트를 반환한다

**When**: 홈 페이지가 렌더링된다

**Then**:
- [x] `VITE_VIRTUAL_SCROLL_THRESHOLD` (100)을 초과한다
- [x] `VirtualList` 컴포넌트가 사용된다
- [x] 화면에 보이는 카드만 렌더링된다 (약 12개)
- [x] 스크롤 시 부드럽게 새로운 카드가 렌더링된다
- [x] 메모리 사용량이 일반 그리드 대비 감소한다

---

#### Scenario 9.2: 일반 그리드 유지 (100 미만 에이전트)

**Given**: 백엔드가 50개의 에이전트를 반환한다

**When**: 홈 페이지가 렌더링된다

**Then**:
- [x] `VITE_VIRTUAL_SCROLL_THRESHOLD` (100) 미만이다
- [x] 일반 CSS 그리드 레이아웃이 사용된다
- [x] 모든 50개 카드가 한 번에 렌더링된다
- [x] 반응형 그리드 (1/2/3/4열)가 적용된다

---

#### Scenario 9.3: React.memo 불필요한 리렌더링 방지

**Given**: 홈 페이지에 50개의 `AgentCard`가 렌더링되어 있다

**When**: 첫 번째 에이전트의 XP가 450에서 460으로 변경된다

**Then**:
- [x] 첫 번째 `AgentCard`만 리렌더링된다
- [x] 나머지 49개 카드는 리렌더링되지 않는다
- [x] React DevTools Profiler에서 1개 컴포넌트 업데이트만 확인된다

---

#### Scenario 9.4: Code Splitting 동작 확인

**Given**: 사용자가 홈 페이지를 방문한다

**When**: 페이지가 로드된다

**Then**:
- [x] `HomePage` 번들만 로드된다 (약 120KB gzipped)
- [x] `AgentDetailPage` 번들은 로드되지 않는다
- [x] 사용자가 에이전트 카드를 클릭할 때 `AgentDetailPage` 번들이 동적으로 로드된다
- [x] Network 탭에서 lazy loading 확인된다

---

#### Scenario 9.5: Lighthouse 성능 점수

**Given**: 프로덕션 빌드가 완료되었다

**When**: Lighthouse CI를 실행한다

**Then**:
- [x] Performance 점수가 90 이상이다
- [x] First Contentful Paint (FCP)가 1.5초 미만이다
- [x] Time to Interactive (TTI)가 3.5초 미만이다
- [x] Largest Contentful Paint (LCP)가 2.5초 미만이다
- [x] Total Bundle Size (gzipped)가 200KB 미만이다

---

## 📊 Definition of Done (DoD)

각 시나리오는 다음 조건을 모두 충족해야 완료로 간주됩니다:

### 코드 품질
- [x] TypeScript 에러 없음 (`npm run type-check` 통과)
- [x] ESLint 경고 없음 (`npm run lint` 통과)
- [x] Prettier 포맷팅 적용 (`npm run format` 실행)

### 테스트
- [x] 단위 테스트 작성 및 통과 (Vitest)
- [x] 컴포넌트 테스트 작성 및 통과 (React Testing Library)
- [x] 테스트 커버리지 85% 이상

### 기능
- [x] 시나리오의 모든 "Then" 조건 충족
- [x] UI가 디자인과 일치
- [x] 반응형 디자인 동작 (Mobile/Tablet/Desktop)
- [x] 접근성 기준 충족 (ARIA 레이블, 키보드 네비게이션)

### 성능
- [x] Lighthouse Performance 점수 90 이상
- [x] 번들 크기 목표 달성 (< 200KB gzipped)
- [x] 60 FPS 유지 (100+ 에이전트 렌더링)

### 문서
- [x] 코드 주석 작성 (복잡한 로직)
- [x] @CODE TAG 추가
- [x] Git 커밋 메시지 작성 (Conventional Commits)

---

## 🧪 테스트 실행 방법

### 단위 테스트
```bash
npm run test:unit
```

### 컴포넌트 테스트
```bash
npm run test:component
```

### E2E 테스트 (선택적)
```bash
npm run test:e2e
```

### Lighthouse CI
```bash
npm run build
npm run lighthouse
```

### 커버리지 리포트
```bash
npm run test:coverage
```

---

## 📝 수동 검증 체크리스트

각 Phase 완료 후 다음 항목을 수동으로 검증합니다:

### Phase 1 체크리스트
- [ ] `.env` 파일 누락 시 명확한 에러 메시지 표시
- [ ] API 401/404/500 에러 시 적절한 메시지 표시
- [ ] 네트워크 에러 시 재시도 로직 동작
- [ ] 에이전트 목록 정상 조회 및 렌더링

### Phase 2 체크리스트
- [ ] 모든 라우트 정상 작동 (`/`, `/agents/:id`, `/agents/:id/history`, `*`)
- [ ] 에이전트 카드 클릭 시 상세 페이지 이동
- [ ] 상세 페이지에서 "목록으로 돌아가기" 링크 동작
- [ ] 404 페이지 정상 표시

### Phase 3 체크리스트
- [ ] "Award XP" 버튼 3개 모두 동작
- [ ] Optimistic update 즉시 반영
- [ ] 서버 에러 시 롤백 동작
- [ ] 레벨업 시 모달 표시 및 confetti 애니메이션

### Phase 4 체크리스트
- [ ] 커버리지 히스토리 차트 정상 렌더링
- [ ] XP 증가량 차트 정상 렌더링
- [ ] 기간 필터 (7일/30일/전체) 동작
- [ ] 차트 반응형 크기 조정

### Phase 5 체크리스트
- [ ] 100+ 에이전트 시 가상 스크롤 활성화
- [ ] 100 미만 시 일반 그리드 유지
- [ ] React.memo 불필요한 리렌더링 방지
- [ ] Code splitting 동작 (lazy loading)
- [ ] Lighthouse Performance 점수 90+ 달성

---

## 🔗 관련 문서

- **SPEC**: `spec.md` (EARS 요구사항)
- **Plan**: `plan.md` (구현 계획)
- **Backend API**: `SPEC-AGENT-GROWTH-002` (백엔드 API 명세)
- **UI Components**: `SPEC-AGENT-CARD-001` (기존 UI 컴포넌트)

---

**작성일**: 2025-10-30
**작성자**: @bridge25
**버전**: 0.0.1 (INITIAL)
