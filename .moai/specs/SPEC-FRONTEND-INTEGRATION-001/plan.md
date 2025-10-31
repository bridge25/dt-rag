# Implementation Plan: SPEC-FRONTEND-INTEGRATION-001

> Pokemon-Style Agent Card System - Backend Integration & 9 Core Features

**SPEC ID**: FRONTEND-INTEGRATION-001
**Version**: 0.0.1
**Status**: draft
**Priority**: high
**Created**: 2025-10-30
**Author**: @bridge25

---

## 📋 구현 개요

이 구현 계획은 Pokemon 스타일 에이전트 카드 시스템의 백엔드 API 통합과 9가지 핵심 기능을 5단계 Phase로 나누어 구현합니다.

### 주요 목표

1. **백엔드 API 통합**: `/api/v1/agents` 엔드포인트와 완전 연동
2. **라우팅 시스템**: React Router DOM 기반 페이지 네비게이션
3. **인터랙션 시스템**: XP 증가 및 레벨업 알림
4. **히스토리 분석**: Coverage/XP 히스토리 차트
5. **성능 최적화**: 가상 스크롤, 메모이제이션, Code Splitting

### 기술 스택

- **Frontend**: React 19.1.1 + TypeScript 5.9.3
- **데이터 페칭**: TanStack Query 5.90.5
- **라우팅**: React Router DOM 7.9.5
- **차트**: Recharts 2.14.1 (또는 Chart.js 4.5.0)
- **가상 스크롤**: react-window 1.8.10

---

## 🗓️ Phase 1: 백엔드 통합 & 환경 설정

**목표**: API 클라이언트 구축 및 환경 변수 설정

### Task 1: Backend API Integration

**우선순위**: 최우선

#### 구현 범위
1. `.env` 파일 구성 (VITE_API_URL, VITE_API_KEY, VITE_API_TIMEOUT)
2. 환경 변수 검증 (`lib/config/env.ts` - Zod 스키마)
3. API 클라이언트 구현 (`lib/api/client.ts` - axios wrapper)
4. 에러 처리 클래스 (`APIError`)
5. Request/Response 인터셉터

#### 구현 단계
1. **환경 변수 스키마 정의**:
   ```typescript
   // lib/config/env.ts
   const envSchema = z.object({
     VITE_API_URL: z.string().url(),
     VITE_API_KEY: z.string().min(1),
     VITE_API_TIMEOUT: z.coerce.number().positive().default(10000),
     // ...
   });
   ```

2. **API 클라이언트 초기화**:
   ```typescript
   // lib/api/client.ts
   class APIClient {
     private client: AxiosInstance;
     constructor() {
       this.client = axios.create({
         baseURL: env.VITE_API_URL,
         timeout: env.VITE_API_TIMEOUT,
         headers: {
           'Authorization': `Bearer ${env.VITE_API_KEY}`,
         },
       });
     }
   }
   ```

3. **에러 핸들링**:
   - 401 Unauthorized → "API 키가 유효하지 않습니다"
   - 404 Not Found → "리소스를 찾을 수 없습니다"
   - 429 Too Many Requests → "요청이 너무 많습니다"
   - 500 Internal Server Error → "서버 오류가 발생했습니다"
   - Network Error → "네트워크 연결을 확인해주세요"

#### 테스트 전략
- ✅ 환경 변수 검증 테스트 (유효/무효 시나리오)
- ✅ API 클라이언트 인터셉터 테스트
- ✅ 에러 변환 테스트 (axios error → APIError)
- ✅ Timeout 테스트

#### 완료 조건
- [x] `.env.example` 파일 생성
- [x] `lib/config/env.ts` 구현 및 테스트 통과
- [x] `lib/api/client.ts` 구현 및 테스트 통과
- [x] 5가지 에러 시나리오 처리 확인

---

### Task 2: useAgents Hook Update

**우선순위**: 최우선

#### 구현 범위
1. `/api/v1/agents` 엔드포인트 연동
2. TanStack Query 설정 (staleTime, cacheTime, retry)
3. Zod 스키마 검증 (`AgentResponse[]`)
4. 에러 재시도 로직 (exponential backoff)

#### 구현 단계
1. **API 함수 구현**:
   ```typescript
   // lib/api/agents.ts
   export async function fetchAgents(params?: {
     level?: number;
     min_coverage?: number;
     max_results?: number;
   }): Promise<AgentResponse[]> {
     const response = await apiClient.get<AgentListResponse>('/api/v1/agents', params);
     return response.agents;
   }
   ```

2. **useAgents 훅 업데이트**:
   ```typescript
   // hooks/useAgents.ts
   export function useAgents(params?: { ... }): UseQueryResult<AgentResponse[], Error> {
     return useQuery({
       queryKey: ['agents', params],
       queryFn: () => fetchAgents(params),
       staleTime: 30_000,
       cacheTime: 300_000,
       refetchOnWindowFocus: true,
       retry: 3,
       retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
     });
   }
   ```

3. **기존 컴포넌트 연동**:
   - `HomePage.tsx`에서 `useAgents()` 호출
   - 로딩 상태: 스켈레톤 카드 표시
   - 에러 상태: 에러 메시지 표시

#### 테스트 전략
- ✅ `fetchAgents` 함수 단위 테스트 (성공/실패)
- ✅ `useAgents` 훅 테스트 (react-hooks-testing-library)
- ✅ 재시도 로직 테스트 (3회 재시도 확인)
- ✅ 캐싱 동작 테스트 (staleTime, cacheTime)

#### 완료 조건
- [x] `lib/api/agents.ts` 구현 및 테스트 통과
- [x] `hooks/useAgents.ts` 업데이트 및 테스트 통과
- [x] `HomePage.tsx`에서 실제 API 데이터 렌더링 확인
- [x] 로딩/에러 상태 UI 확인

---

## 🗓️ Phase 2: 라우팅 & 상세 페이지

**목표**: React Router DOM 설정 및 에이전트 상세 페이지 구현

### Task 3: Routing System

**우선순위**: 주요 목표

#### 구현 범위
1. React Router DOM 설치 및 설정
2. 라우트 정의 (`/`, `/agents/:id`, `/agents/:id/history`, `*`)
3. NotFoundPage 컴포넌트
4. 페이지 전환 애니메이션 (선택적)

#### 구현 단계
1. **라우터 설정**:
   ```typescript
   // App.tsx
   const router = createBrowserRouter([
     { path: "/", element: <HomePage /> },
     { path: "/agents/:id", element: <AgentDetailPage /> },
     { path: "/agents/:id/history", element: <AgentHistoryPage /> },
     { path: "*", element: <NotFoundPage /> },
   ]);
   ```

2. **Lazy Loading 적용**:
   ```typescript
   const AgentDetailPage = React.lazy(() => import('./pages/AgentDetailPage'));
   const AgentHistoryPage = React.lazy(() => import('./pages/AgentHistoryPage'));
   ```

3. **네비게이션 링크 추가**:
   - AgentCard에 클릭 → `/agents/:id` 이동
   - 상세 페이지에서 "목록으로 돌아가기" 링크
   - 상세 페이지에서 "히스토리 보기" 링크

#### 테스트 전략
- ✅ 라우트 테스트 (각 경로별 컴포넌트 렌더링)
- ✅ 404 페이지 테스트
- ✅ 네비게이션 테스트 (Link 클릭 시 경로 변경)

#### 완료 조건
- [x] React Router DOM 설치 (`npm install react-router-dom`)
- [x] 라우터 설정 완료
- [x] 4개 라우트 모두 정상 작동
- [x] Lazy loading 적용 (Suspense + LoadingSpinner)

---

### Task 4: Data Synchronization Strategy

**우선순위**: 주요 목표

#### 구현 범위
1. TanStack Query 캐싱 전략 최적화
2. Optimistic Updates 구현 (XP 증가 시)
3. Background Refetch 설정
4. Query Invalidation 전략

#### 구현 단계
1. **캐싱 전략 문서화**:
   - `staleTime`: 30초 (신선한 데이터 기준)
   - `cacheTime`: 5분 (메모리 캐시 유지)
   - `refetchOnWindowFocus`: true
   - `refetchInterval`: 60초 (선택적)

2. **Optimistic Updates 패턴**:
   ```typescript
   // hooks/useXPAward.ts
   const mutation = useMutation({
     mutationFn: awardXP,
     onMutate: async (newXP) => {
       await queryClient.cancelQueries(['agent', agentId]);
       const previousAgent = queryClient.getQueryData(['agent', agentId]);
       queryClient.setQueryData(['agent', agentId], (old) => ({
         ...old,
         current_xp: old.current_xp + newXP
       }));
       return { previousAgent };
     },
     onError: (err, newXP, context) => {
       queryClient.setQueryData(['agent', agentId], context.previousAgent);
     },
     onSettled: () => {
       queryClient.invalidateQueries(['agent', agentId]);
     },
   });
   ```

3. **Query Invalidation 규칙**:
   - XP 증가 시 → `['agent', agentId]`, `['agents']` invalidate
   - 레벨업 시 → `['agent', agentId]`, `['agents']`, `['coverageHistory', agentId]` invalidate
   - 커버리지 계산 시 → `['agent', agentId]`, `['agents']` invalidate

#### 테스트 전략
- ✅ Optimistic update 테스트 (성공 시나리오)
- ✅ Rollback 테스트 (실패 시나리오)
- ✅ Query invalidation 테스트
- ✅ 캐시 타임아웃 테스트

#### 완료 조건
- [x] 캐싱 전략 문서화 (plan.md 또는 ARCHITECTURE.md)
- [x] Optimistic updates 구현 및 테스트 통과
- [x] Query invalidation 규칙 적용

---

### Task 5: Agent Detail Page

**우선순위**: 주요 목표

#### 구현 범위
1. `useAgent(id)` 훅 구현 (단일 에이전트 조회)
2. `AgentDetailPage` 컴포넌트
3. `AgentDetailCard` 컴포넌트 (상세 정보 표시)
4. `LevelUpTimeline` 컴포넌트 (레벨업 히스토리)
5. 스켈레톤 UI 및 404 에러 처리

#### 구현 단계
1. **useAgent 훅 구현**:
   ```typescript
   // hooks/useAgent.ts
   export function useAgent(agentId: string): UseQueryResult<AgentResponse, Error> {
     return useQuery({
       queryKey: ['agent', agentId],
       queryFn: () => fetchAgent(agentId),
       staleTime: 30_000,
       cacheTime: 300_000,
       refetchOnWindowFocus: true,
       refetchInterval: env.VITE_ENABLE_POLLING ? env.VITE_POLLING_INTERVAL : false,
       enabled: !!agentId,
     });
   }
   ```

2. **AgentDetailPage 레이아웃**:
   - 좌측: AgentDetailCard (에이전트 정보, 스탯, 커버리지)
   - 우측: XPAwardButton, "히스토리 보기" 링크
   - 하단: LevelUpTimeline (최근 5개 레벨업 이벤트)

3. **로딩/에러 처리**:
   - 로딩 중: 스켈레톤 UI
   - 에러: 에러 메시지 + "목록으로 돌아가기" 버튼
   - 404: "에이전트를 찾을 수 없습니다" 페이지

#### 테스트 전략
- ✅ `useAgent` 훅 테스트 (성공/실패/로딩)
- ✅ AgentDetailPage 렌더링 테스트
- ✅ 404 에러 처리 테스트
- ✅ 네비게이션 링크 테스트

#### 완료 조건
- [x] `hooks/useAgent.ts` 구현 및 테스트 통과
- [x] `pages/AgentDetailPage.tsx` 구현
- [x] `components/agent-detail/AgentDetailCard.tsx` 구현
- [x] 로딩/에러/404 상태 모두 확인

---

## 🗓️ Phase 3: 인터랙션 시스템

**목표**: XP 증가 및 레벨업 알림 기능 구현

### Task 6: XP Interaction System

**우선순위**: 주요 목표

#### 구현 범위
1. `useXPAward` 훅 구현 (mutation)
2. `XPAwardButton` 컴포넌트 (3가지 버튼: 대화, 피드백, RAGAS)
3. Optimistic UI 업데이트
4. 플로팅 텍스트 애니메이션 (선택적)

#### 구현 단계
1. **XP API 함수 구현**:
   ```typescript
   // lib/api/xp.ts
   export async function awardXP(request: AwardXPRequest): Promise<AwardXPResponse> {
     // 백엔드 미구현 시 임시 처리
     return apiClient.post<AwardXPResponse>(
       `/api/v1/agents/${request.agentId}/xp`,
       { amount: request.amount, reason: request.reason }
     );
   }
   ```

2. **useXPAward 훅 구현**:
   - Optimistic update (즉시 UI 반영)
   - 실패 시 롤백
   - 성공 시 Query invalidation

3. **XPAwardButton UI**:
   - "대화 완료 (+10 XP)" 버튼
   - "긍정 피드백 (+50 XP)" 버튼
   - "RAGAS 보너스 (+100 XP)" 버튼
   - 로딩 상태 표시

#### 테스트 전략
- ✅ `useXPAward` mutation 테스트
- ✅ Optimistic update 테스트
- ✅ 롤백 테스트 (에러 시나리오)
- ✅ XPAwardButton 클릭 테스트

#### 완료 조건
- [x] `lib/api/xp.ts` 구현
- [x] `hooks/useXPAward.ts` 구현 및 테스트 통과
- [x] `components/agent-detail/XPAwardButton.tsx` 구현
- [x] Optimistic UI 동작 확인

**⚠️ 주의**: 백엔드 XP 엔드포인트가 미구현인 경우, 클라이언트 사이드 임시 처리 후 백엔드 추가 시 연동

---

### Task 7: Level-up Notifications

**우선순위**: 주요 목표

#### 구현 범위
1. `useInterval` 커스텀 훅 구현 (Polling 유틸리티)
2. 레벨업 감지 로직 (5초마다 `/agents/:id` 폴링)
3. `LevelUpModal` 표시 (기존 SPEC-AGENT-CARD-001 컴포넌트 활용)
4. react-confetti 애니메이션

#### 구현 단계
1. **useInterval 훅 구현**:
   ```typescript
   // hooks/useInterval.ts
   export function useInterval(callback: () => void, delay: number | null) {
     const savedCallback = useRef<() => void>();
     useEffect(() => {
       savedCallback.current = callback;
     }, [callback]);
     useEffect(() => {
       if (delay === null) return;
       const id = setInterval(() => savedCallback.current?.(), delay);
       return () => clearInterval(id);
     }, [delay]);
   }
   ```

2. **레벨업 감지 로직**:
   ```typescript
   // AgentDetailPage.tsx
   const { data: agent } = useAgent(id, { refetchInterval: 5000 });
   useEffect(() => {
     if (previousLevel && agent.level > previousLevel) {
       setShowLevelUpModal(true);
     }
     setPreviousLevel(agent.level);
   }, [agent.level]);
   ```

3. **LevelUpModal 통합**:
   - 기존 SPEC-AGENT-CARD-001의 `LevelUpModal` 컴포넌트 재사용
   - 희귀도 변경 감지 및 "진화!" 메시지 추가
   - "확인" 버튼 클릭 시 모달 닫기

#### 테스트 전략
- ✅ `useInterval` 훅 테스트
- ✅ 레벨업 감지 테스트 (레벨 변경 시나리오)
- ✅ LevelUpModal 표시/닫기 테스트

#### 완료 조건
- [x] `hooks/useInterval.ts` 구현 및 테스트 통과
- [x] 레벨업 감지 로직 구현
- [x] LevelUpModal 통합 및 애니메이션 확인
- [x] Polling 동작 확인 (5초 간격)

---

## 🗓️ Phase 4: 히스토리 & 분석

**목표**: Coverage/XP 히스토리 차트 구현

### Task 8: History Dashboard

**우선순위**: 보조 목표

#### 구현 범위
1. `useCoverageHistory` 훅 구현
2. `AgentHistoryPage` 컴포넌트
3. `CoverageChart` 컴포넌트 (Recharts 선 그래프)
4. `XPGrowthChart` 컴포넌트 (Recharts 막대 그래프)
5. 기간 필터 (7일, 30일, 전체)

#### 구현 단계
1. **Recharts 설치**:
   ```bash
   npm install recharts
   ```

2. **히스토리 API 함수 구현**:
   ```typescript
   // lib/api/history.ts
   export async function fetchCoverageHistory(
     agentId: string,
     params?: { start_date?: string; end_date?: string; interval?: string }
   ): Promise<CoverageHistoryResponse> {
     return apiClient.get<CoverageHistoryResponse>(
       `/api/v1/agents/${agentId}/coverage/history`,
       params
     );
   }
   ```

3. **CoverageChart 구현**:
   ```typescript
   // components/history/CoverageChart.tsx
   <LineChart width={600} height={300} data={historyData}>
     <CartesianGrid strokeDasharray="3 3" />
     <XAxis dataKey="date" />
     <YAxis domain={[0, 100]} />
     <Tooltip />
     <Legend />
     <Line type="monotone" dataKey="coverage" stroke="#8884d8" strokeWidth={2} />
   </LineChart>
   ```

4. **XPGrowthChart 구현**:
   - 막대 그래프 (일별/주별 XP 증가량)
   - 이전 날짜와 비교하여 증가량 계산

5. **기간 필터 UI**:
   - 버튼: "7일", "30일", "전체"
   - 선택 시 `interval` 파라미터 변경

#### 테스트 전략
- ✅ `useCoverageHistory` 훅 테스트
- ✅ CoverageChart 렌더링 테스트
- ✅ XPGrowthChart 렌더링 테스트
- ✅ 기간 필터 테스트

#### 완료 조건
- [x] Recharts 설치 및 설정
- [x] `lib/api/history.ts` 구현
- [x] `hooks/useCoverageHistory.ts` 구현
- [x] `pages/AgentHistoryPage.tsx` 구현
- [x] `components/history/CoverageChart.tsx` 구현
- [x] `components/history/XPGrowthChart.tsx` 구현
- [x] 기간 필터 동작 확인

**⚠️ 주의**: 백엔드 히스토리 엔드포인트가 미구현인 경우, 더미 데이터로 UI 먼저 구현 후 백엔드 추가 시 연동

---

## 🗓️ Phase 5: 성능 최적화

**목표**: 대규모 에이전트 목록 성능 최적화

### Task 9: Performance Optimization

**우선순위**: 최종 목표

#### 구현 범위
1. React.memo 래핑 (AgentCard)
2. 가상 스크롤링 (react-window)
3. Code Splitting (lazy loading)
4. 번들 크기 최적화

#### 구현 단계
1. **React.memo 적용**:
   ```typescript
   // components/agent-card/AgentCard.tsx
   export const AgentCard = React.memo(({ agent, onChatClick, onHistoryClick }) => {
     // 컴포넌트 로직
   }, (prevProps, nextProps) => {
     return prevProps.agent.agent_id === nextProps.agent.agent_id &&
            prevProps.agent.current_xp === nextProps.agent.current_xp &&
            prevProps.agent.level === nextProps.agent.level;
   });
   ```

2. **react-window 설치 및 구현**:
   ```bash
   npm install react-window
   ```
   ```typescript
   // components/common/VirtualList.tsx
   <FixedSizeGrid
     columnCount={3}
     columnWidth={300}
     height={800}
     rowCount={Math.ceil(agents.length / 3)}
     rowHeight={400}
     width={1000}
   >
     {({ columnIndex, rowIndex, style }) => {
       const index = rowIndex * 3 + columnIndex;
       const agent = agents[index];
       return agent ? (
         <div style={style}><AgentCard agent={agent} /></div>
       ) : null;
     }}
   </FixedSizeGrid>
   ```

3. **조건부 가상 스크롤**:
   ```typescript
   // pages/HomePage.tsx
   const agents = useAgents().data || [];
   const enableVirtualScroll = env.VITE_ENABLE_VIRTUAL_SCROLL &&
                                agents.length > env.VITE_VIRTUAL_SCROLL_THRESHOLD;

   return enableVirtualScroll ? (
     <VirtualList agents={agents} ... />
   ) : (
     <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
       {agents.map(agent => <AgentCard key={agent.agent_id} agent={agent} />)}
     </div>
   );
   ```

4. **번들 크기 분석**:
   ```bash
   npm run build
   npx vite-bundle-visualizer
   ```

#### 테스트 전략
- ✅ React.memo 효과 테스트 (불필요한 리렌더링 방지)
- ✅ VirtualList 렌더링 테스트
- ✅ 대규모 데이터 성능 테스트 (100+, 500+, 1000+ 에이전트)
- ✅ Lighthouse 성능 점수 측정

#### 완료 조건
- [x] AgentCard React.memo 적용
- [x] react-window 설치 및 VirtualList 구현
- [x] 조건부 가상 스크롤 로직 적용
- [x] Code splitting 적용 (AgentDetailPage, AgentHistoryPage)
- [x] 번들 크기 < 200KB (gzipped)
- [x] Lighthouse Performance 점수 > 90

---

## 📊 성능 목표

### 로딩 성능
- **First Contentful Paint (FCP)**: < 1.5초
- **Time to Interactive (TTI)**: < 3.5초
- **Largest Contentful Paint (LCP)**: < 2.5초

### 번들 크기
- **초기 로드**: < 200KB (gzipped)
- **AgentDetailPage (lazy)**: < 50KB (gzipped)
- **AgentHistoryPage (lazy)**: < 80KB (gzipped, Recharts 포함)

### 런타임 성능
- **에이전트 카드 렌더링**: 60 FPS 유지 (100개 카드)
- **가상 스크롤 활성화**: 1000개 카드 지원
- **API 응답 시간**: < 500ms (평균)

---

## 🧪 테스트 전략

### 단위 테스트 (Unit Tests)
- **API 함수**: `lib/api/*.ts` (성공/실패 시나리오)
- **훅**: `hooks/use*.ts` (react-hooks-testing-library)
- **유틸리티**: `lib/utils/*.ts`, `lib/config/*.ts`

### 컴포넌트 테스트 (Component Tests)
- **페이지**: `pages/*.tsx` (렌더링, 네비게이션)
- **컴포넌트**: `components/**/*.tsx` (props, 이벤트 핸들러)
- **차트**: `components/history/*.tsx` (데이터 시각화)

### 통합 테스트 (Integration Tests)
- **API 연동**: 실제 백엔드 API 호출 (E2E)
- **라우팅**: 페이지 간 네비게이션 흐름
- **XP 시스템**: XP 증가 → 레벨업 → 알림 전체 흐름

### 성능 테스트 (Performance Tests)
- **Lighthouse CI**: 성능, 접근성, SEO 점수
- **번들 분석**: vite-bundle-visualizer
- **대규모 데이터**: 1000+ 에이전트 렌더링 테스트

---

## 🔧 기술적 의사결정

### 차트 라이브러리 선택

#### Recharts (권장)
**장점**:
- React 네이티브, 선언적 API
- TypeScript 지원 우수
- 반응형 디자인 기본 제공
- 커스터마이징 용이

**단점**:
- 번들 크기 (gzipped: ~40KB)
- 차트 타입 제한적

#### Chart.js (대안)
**장점**:
- 더 많은 차트 타입 지원
- 성능 최적화 (Canvas 기반)
- 커뮤니티 크기

**단점**:
- React 래퍼 필요 (react-chartjs-2)
- 명령형 API (React 스타일과 부조화)

**결정**: Recharts 사용 (React 네이티브 API + TypeScript 지원)

---

### 가상 스크롤 임계값

**기준**: 100개 에이전트
**근거**:
- 100개 미만: 일반 그리드 렌더링 충분 (성능 저하 없음)
- 100개 이상: react-window 가상 스크롤 활성화 (렌더링 최적화)

**설정 가능**: `VITE_VIRTUAL_SCROLL_THRESHOLD` 환경 변수로 조정

---

### Polling vs WebSocket

**Phase 1-5**: Polling 방식 (5초 간격)
**근거**:
- 구현 단순 (TanStack Query `refetchInterval`)
- 백엔드 WebSocket 미구현
- 실시간성 요구사항 낮음 (레벨업 알림)

**Phase 6 (향후)**: WebSocket 전환 고려
- 실시간 알림 (레벨업, 커버리지 증가)
- 서버 부하 감소 (Polling 대비)

---

## 🚧 위험 요소 및 대응 방안

### 위험 1: 백엔드 XP/히스토리 엔드포인트 미구현

**대응 방안**:
- 클라이언트 사이드 임시 처리 (Zustand 스토어)
- 더미 데이터로 UI 먼저 구현
- 백엔드 추가 시 연동 (API 함수만 수정)

---

### 위험 2: CORS 설정 누락

**대응 방안**:
- 백엔드 `.env` 파일에 `CORS_ORIGINS=http://localhost:5173` 추가
- FastAPI CORS 미들웨어 확인 (`app.add_middleware(CORSMiddleware)`)
- 프론트엔드에서 Preflight 요청 테스트

---

### 위험 3: API Key 노출

**대응 방안**:
- `.env` 파일을 `.gitignore`에 추가
- `.env.example` 파일 제공 (키 값은 비움)
- 백엔드에서 Rate Limiting 설정 (초당 100 requests)
- IP 기반 접근 제어 (프로덕션 환경)

---

### 위험 4: 번들 크기 초과

**대응 방안**:
- Tree shaking 활성화 (Vite 기본 제공)
- Code splitting (lazy loading)
- Recharts 대신 경량 차트 라이브러리 고려 (nivo, victory)
- 번들 분석 (vite-bundle-visualizer)

---

## 📅 구현 순서 요약

| Phase | Tasks | 우선순위 | 예상 복잡도 |
|-------|-------|---------|------------|
| Phase 1 | Task 1-2 | 최우선 | 중간 |
| Phase 2 | Task 3-5 | 주요 목표 | 높음 |
| Phase 3 | Task 6-7 | 주요 목표 | 중간 |
| Phase 4 | Task 8 | 보조 목표 | 중간 |
| Phase 5 | Task 9 | 최종 목표 | 높음 |

**총 Task 수**: 9개
**예상 구현 기간**: TDD 방식으로 순차 진행

---

## 🔗 관련 문서

- **SPEC**: `spec.md` (EARS 요구사항)
- **Acceptance**: `acceptance.md` (Given-When-Then 시나리오)
- **Backend API**: `SPEC-AGENT-GROWTH-002` (백엔드 API 명세)
- **UI Components**: `SPEC-AGENT-CARD-001` (기존 UI 컴포넌트)

---

**작성일**: 2025-10-30
**작성자**: @bridge25
**버전**: 0.0.1 (INITIAL)
