---
id: FRONTEND-INTEGRATION-001
version: 0.0.1
status: draft
created: 2025-10-30
updated: 2025-10-30
author: @bridge25
priority: high
category: feature
labels:
  - frontend
  - backend-integration
  - react
  - tanstack-query
  - routing
  - performance
depends_on:
  - AGENT-CARD-001
  - AGENT-GROWTH-002
scope:
  packages:
    - frontend/src/hooks
    - frontend/src/pages
    - frontend/src/lib/api
    - frontend/src/components
---

# @SPEC:FRONTEND-INTEGRATION-001 Pokemon-Style Agent Card System - Backend Integration & 9 Core Features

## 개요

Pokemon 스타일 에이전트 카드 시스템의 백엔드 API 통합과 9가지 핵심 기능을 구현합니다. SPEC-AGENT-CARD-001에서 구축한 UI 컴포넌트를 기반으로, 실제 백엔드 API와 연동하고 라우팅, 인터랙션, 히스토리 분석, 성능 최적화를 완성합니다.

이 SPEC은 5단계 구현 계획을 포함합니다:
- **Phase 1**: 백엔드 통합 & 환경 설정 (Tasks 1-2)
- **Phase 2**: 라우팅 & 상세 페이지 (Tasks 3-5)
- **Phase 3**: 인터랙션 시스템 (Tasks 6-7)
- **Phase 4**: 히스토리 & 분석 (Task 8)
- **Phase 5**: 성능 최적화 (Task 9)

## 환경 (Environment)

### 기술 스택

#### Frontend Framework
- **React**: 19.1.1
- **TypeScript**: 5.9.3
- **Styling**: Tailwind CSS 4.1.16
- **Build Tool**: Vite 6.3.6

#### 상태 관리 & 데이터 페칭
- **TanStack Query**: 5.90.5 (서버 상태 관리)
- **Zustand**: 5.0.8 (클라이언트 상태 관리)
- **React Router DOM**: 7.9.5 (라우팅)

#### 검증 & 타입 안전성
- **Zod**: 4.1.12 (런타임 스키마 검증)
- **TypeScript Strict Mode**: 활성화

#### 성능 최적화
- **react-window**: ^1.8.10 (가상 스크롤링)
- **React.memo**: 컴포넌트 메모이제이션
- **Code Splitting**: React.lazy + Suspense

#### 차트 라이브러리 (NEW - 설치 필요)
- **Recharts**: ^2.14.1 또는 **Chart.js**: ^4.5.0 + react-chartjs-2: ^5.3.0

### 백엔드 API 엔드포인트

#### 에이전트 관리 API (SPEC-AGENT-GROWTH-002)
- `GET /api/v1/agents` - 에이전트 목록 조회 (필터링 지원)
  - Query params: `level`, `min_coverage`, `max_results`
- `GET /api/v1/agents/{agent_id}` - 단일 에이전트 상세 조회
- `POST /api/v1/agents/from-taxonomy` - 에이전트 생성
- `GET /api/v1/agents/{agent_id}/coverage` - 커버리지 계산
- `GET /api/v1/agents/{agent_id}/gaps` - 지식 갭 탐지
- `POST /api/v1/agents/{agent_id}/query` - 에이전트 쿼리 실행

#### XP 관리 API (구현 필요 - 백엔드 추가)
- `POST /api/v1/agents/{agent_id}/xp` - XP 증가
  - Request body: `{ "amount": number, "reason": string }`
  - Response: `{ "agent_id": UUID, "current_xp": number, "new_level": number }`

#### 히스토리 API (구현 필요 - 백엔드 추가)
- `GET /api/v1/agents/{agent_id}/coverage/history` - 커버리지 히스토리
  - Query params: `start_date`, `end_date`, `interval` (daily/weekly/monthly)
  - Response: `{ "history": [{ "date": string, "coverage": number, "xp": number }] }`

### 환경 변수 (.env 파일 구성)

```bash
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_API_KEY=your_api_key_here
VITE_API_TIMEOUT=10000

# Feature Flags
VITE_ENABLE_POLLING=true
VITE_POLLING_INTERVAL=5000
VITE_ENABLE_VIRTUAL_SCROLL=true
VITE_VIRTUAL_SCROLL_THRESHOLD=100

# Development
VITE_DEBUG=false
VITE_LOG_LEVEL=info
```

### 디렉토리 구조

```
frontend/src/
├── hooks/
│   ├── useAgents.ts              # ✅ 기존 (업데이트 필요)
│   ├── useAgent.ts               # 🆕 단일 에이전트 조회
│   ├── useAgentQuery.ts          # 🆕 에이전트 쿼리 실행
│   ├── useXPAward.ts             # 🆕 XP 증가 mutation
│   ├── useCoverageHistory.ts    # 🆕 히스토리 데이터
│   └── useInterval.ts            # 🆕 Polling 유틸리티
├── pages/
│   ├── HomePage.tsx              # ✅ 기존 (업데이트 필요)
│   ├── AgentDetailPage.tsx       # 🆕 에이전트 상세
│   └── AgentHistoryPage.tsx      # 🆕 히스토리 대시보드
├── lib/
│   ├── api/
│   │   ├── client.ts             # ✅ 기존 API 클라이언트
│   │   ├── types.ts              # ✅ 기존 (타입 추가)
│   │   ├── agents.ts             # 🆕 에이전트 API 함수
│   │   ├── xp.ts                 # 🆕 XP API 함수
│   │   └── history.ts            # 🆕 히스토리 API 함수
│   └── config/
│       └── env.ts                # 🆕 환경 변수 검증
├── components/
│   ├── agent-card/               # ✅ 기존 컴포넌트들
│   ├── agent-detail/
│   │   ├── AgentDetailCard.tsx   # 🆕 상세 카드
│   │   ├── LevelUpTimeline.tsx   # 🆕 타임라인
│   │   └── XPAwardButton.tsx     # 🆕 XP 버튼
│   ├── history/
│   │   ├── CoverageChart.tsx     # 🆕 커버리지 차트
│   │   ├── XPGrowthChart.tsx     # 🆕 XP 증가 차트
│   │   └── ChartContainer.tsx    # 🆕 차트 래퍼
│   └── common/
│       ├── ErrorBoundary.tsx     # 🆕 에러 경계
│       ├── LoadingSpinner.tsx    # 🆕 로딩 스피너
│       └── VirtualList.tsx       # 🆕 가상 스크롤
└── App.tsx                       # ✅ 기존 (라우팅 추가)
```

## 가정 (Assumptions)

### 백엔드 API 가정

1. **API 안정성**: `/api/v1/agents` 엔드포인트가 정상 작동하며 CORS 설정 완료
2. **인증 방식**: API Key 기반 인증 (Authorization 헤더 또는 Query param)
3. **에러 응답 포맷**: RFC 7807 Problem Details 형식
   ```json
   {
     "type": "https://api.example.com/errors/not-found",
     "title": "Agent Not Found",
     "status": 404,
     "detail": "Agent with ID 123 does not exist"
   }
   ```
4. **페이지네이션**: `max_results` 파라미터로 제한 (기본값 50, 최대 100)
5. **Rate Limiting**: 초당 100 requests (429 Too Many Requests 응답)

### XP 시스템 가정

1. **XP 엔드포인트 미구현**: 초기 버전에서는 클라이언트 사이드 Optimistic UI 업데이트
2. **향후 백엔드 추가**: `POST /agents/{id}/xp` 엔드포인트 추가 시 서버 동기화
3. **레벨업 감지**: Polling 방식으로 5초마다 `/agents/{id}` 조회하여 레벨 변경 확인

### 히스토리 시스템 가정

1. **히스토리 엔드포인트 미구현**: Phase 4에서 백엔드 추가 필요
2. **데이터 저장**: 백엔드에 `coverage_history` 테이블 추가 예정
3. **Time-series 데이터**: ISO 8601 형식 날짜 + 수치 값
   ```json
   {
     "history": [
       { "date": "2025-10-01T00:00:00Z", "coverage": 75.5, "xp": 1200 },
       { "date": "2025-10-02T00:00:00Z", "coverage": 78.3, "xp": 1350 }
     ]
   }
   ```

### 성능 가정

1. **에이전트 수량**: 초기 100개 미만, 최대 1000개 지원 목표
2. **가상 스크롤 임계값**: 100개 이상일 때 react-window 활성화
3. **메모이제이션**: AgentCard 컴포넌트는 React.memo로 래핑
4. **Code Splitting**: 상세 페이지와 히스토리 페이지는 lazy loading

### UI/UX 가정

1. **라우팅 전략**: React Router DOM 사용, URL 기반 네비게이션
2. **페이지 전환 애니메이션**: framer-motion 사용 (선택적)
3. **접근성**: ARIA 레이블, 키보드 네비게이션 완전 지원
4. **반응형**: Mobile-first 디자인, 모든 디바이스 지원

## 요구사항 (Requirements)

### Phase 1: 백엔드 통합 & 환경 설정

#### @REQ:FRONTEND-INTEGRATION-001-R01 Backend API Integration
**WHEN** 프론트엔드 앱이 시작되면, **THEN** 시스템은 다음을 수행해야 한다:
- `.env` 파일에서 `VITE_API_URL`, `VITE_API_KEY`, `VITE_API_TIMEOUT` 로드
- Zod 스키마로 환경 변수 검증 (`lib/config/env.ts`)
- `lib/api/client.ts`에 API 클라이언트 초기화 (axios 또는 fetch wrapper)
- API 클라이언트에 인증 헤더 자동 추가 (`Authorization: Bearer {API_KEY}`)

**IF** 환경 변수가 누락되면, **THEN** 시스템은 명확한 에러 메시지를 표시해야 한다:
```
Error: Missing environment variable VITE_API_URL.
Please copy .env.example to .env and configure it.
```

**WHILE** API 요청 중, **THEN** 시스템은 타임아웃을 적용해야 한다 (기본값 10초).

#### @REQ:FRONTEND-INTEGRATION-001-R02 useAgents 훅 업데이트
**WHEN** `useAgents` 훅이 호출되면, **THEN** 시스템은 다음을 수행해야 한다:
- `GET /api/v1/agents` 엔드포인트 호출
- TanStack Query를 사용하여 데이터 캐싱
- Zod 스키마로 응답 검증 (`AgentResponse[]`)
- 에러 발생 시 재시도 로직 (최대 3회, exponential backoff)

**TanStack Query 설정**:
```typescript
useQuery({
  queryKey: ['agents'],
  queryFn: fetchAgents,
  staleTime: 30_000,        // 30초
  cacheTime: 300_000,       // 5분
  refetchOnWindowFocus: true,
  retry: 3,
  retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000)
})
```

**IF** API 호출이 실패하면, **THEN** 시스템은 다음 에러를 처리해야 한다:
- 401 Unauthorized: "API 키가 유효하지 않습니다"
- 404 Not Found: "에이전트를 찾을 수 없습니다"
- 429 Too Many Requests: "요청이 너무 많습니다. 잠시 후 다시 시도해주세요"
- 500 Internal Server Error: "서버 오류가 발생했습니다"
- Network Error: "네트워크 연결을 확인해주세요"

### Phase 2: 라우팅 & 상세 페이지

#### @REQ:FRONTEND-INTEGRATION-001-R03 Routing System
**WHEN** 앱이 렌더링되면, **THEN** 시스템은 다음 라우트를 제공해야 한다:
- `/` - 홈 페이지 (에이전트 리스트)
- `/agents/:id` - 에이전트 상세 페이지
- `/agents/:id/history` - 히스토리 대시보드
- `*` - 404 Not Found 페이지

**React Router DOM 설정**:
```typescript
const router = createBrowserRouter([
  {
    path: "/",
    element: <HomePage />,
  },
  {
    path: "/agents/:id",
    element: <AgentDetailPage />,
  },
  {
    path: "/agents/:id/history",
    element: <AgentHistoryPage />,
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
]);
```

**WHILE** 라우트가 변경되는 동안, **THEN** 시스템은 부드러운 전환 애니메이션을 제공해야 한다 (선택적).

#### @REQ:FRONTEND-INTEGRATION-001-R04 Data Synchronization
**WHEN** TanStack Query가 데이터를 페칭하면, **THEN** 시스템은 다음 전략을 사용해야 한다:

**캐싱 전략**:
- `staleTime`: 30초 (데이터가 신선하다고 간주되는 시간)
- `cacheTime`: 5분 (메모리에 캐시를 유지하는 시간)
- `refetchOnWindowFocus`: true (창 포커스 시 재페칭)
- `refetchInterval`: 60초 (백그라운드 자동 재페칭, 선택적)

**Optimistic Updates**:
- XP 증가 시 즉시 UI 업데이트 (서버 응답 전)
- 서버 응답 실패 시 롤백
- `onMutate`, `onError`, `onSettled` 콜백 활용

**예시 코드**:
```typescript
const mutation = useMutation({
  mutationFn: awardXP,
  onMutate: async (newXP) => {
    await queryClient.cancelQueries({ queryKey: ['agent', agentId] });
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
    queryClient.invalidateQueries({ queryKey: ['agent', agentId] });
  },
});
```

#### @REQ:FRONTEND-INTEGRATION-001-R05 Agent Detail Page
**WHEN** 사용자가 `/agents/:id`에 접근하면, **THEN** 시스템은 다음을 표시해야 한다:
- `useAgent(id)` 훅으로 단일 에이전트 데이터 조회
- 에이전트 상세 정보 카드 (이름, 레벨, XP, 커버리지, 품질 점수)
- 스탯 섹션 (지식 개수, 대화 횟수, 성공률)
- Level-up 히스토리 타임라인 (최근 5개 레벨업 이벤트)
- "Award XP" 버튼 (Phase 3에서 구현)
- "히스토리 보기" 링크 (`/agents/:id/history`로 이동)

**IF** 에이전트가 존재하지 않으면, **THEN** 시스템은 404 에러 페이지를 표시해야 한다.

**WHILE** 데이터 로딩 중, **THEN** 시스템은 스켈레톤 UI를 표시해야 한다.

### Phase 3: 인터랙션 시스템

#### @REQ:FRONTEND-INTEGRATION-001-R06 XP Interaction System
**WHEN** 사용자가 "Award XP" 버튼을 클릭하면, **THEN** 시스템은 다음을 수행해야 한다:
1. `useXPAward` 훅으로 `POST /agents/{id}/xp` 호출 (백엔드 구현 시)
2. Optimistic UI 업데이트 (즉시 XP 증가 표시)
3. 플로팅 텍스트 애니메이션 (+10 XP, +50 XP 등)
4. Progress Bar 애니메이션 (0.3초 ease-out)

**IF** 백엔드 XP 엔드포인트가 미구현이면, **THEN** 시스템은 다음 대체 방식을 사용해야 한다:
- 클라이언트 사이드에서 XP 증가 계산
- Zustand 스토어에 임시 저장
- 서버 데이터와의 동기화는 다음 refetch 시점까지 대기

**Award XP 버튼 UI**:
```tsx
<button
  onClick={() => awardXP({ agentId, amount: 50, reason: 'positive_feedback' })}
  disabled={isLoading}
  className="px-4 py-2 bg-blue-600 text-white rounded-lg"
>
  {isLoading ? 'Awarding...' : 'Award +50 XP'}
</button>
```

#### @REQ:FRONTEND-INTEGRATION-001-R07 Level-up Notifications
**WHEN** 에이전트의 레벨이 변경되면, **THEN** 시스템은 레벨업 모달을 표시해야 한다:
- `useInterval` 커스텀 훅으로 5초마다 `/agents/{id}` 폴링
- 이전 레벨과 현재 레벨 비교
- 레벨 증가 감지 시 `LevelUpModal` 표시
- react-confetti 애니메이션 (화면 전체, 3초 동안)
- 희귀도 변경 시 "진화!" 메시지 추가

**Polling 로직**:
```typescript
const { data: agent } = useQuery({
  queryKey: ['agent', agentId],
  queryFn: () => fetchAgent(agentId),
  refetchInterval: 5000, // 5초마다 폴링
});

useEffect(() => {
  if (previousLevel && agent.level > previousLevel) {
    setShowLevelUpModal(true);
  }
  setPreviousLevel(agent.level);
}, [agent.level]);
```

**WHILE** 레벨업 모달이 표시되는 동안, **THEN** 시스템은 배경 클릭으로 닫을 수 없어야 한다 (명시적 "확인" 버튼 클릭 필요).

### Phase 4: 히스토리 & 분석

#### @REQ:FRONTEND-INTEGRATION-001-R08 History Dashboard
**WHEN** 사용자가 `/agents/:id/history`에 접근하면, **THEN** 시스템은 다음을 표시해야 한다:
- `useCoverageHistory(id)` 훅으로 히스토리 데이터 조회
- Coverage 히스토리 차트 (선 그래프, 시간에 따른 커버리지 변화)
- XP 증가 차트 (막대 그래프, 일별/주별/월별 XP 증가량)
- 주요 이벤트 타임라인 (레벨업, 커버리지 증가, 주요 쿼리)
- 필터 옵션 (기간 선택: 7일, 30일, 전체)

**차트 라이브러리 선택**:
- **Recharts**: 선언적 API, React 네이티브 (권장)
- **Chart.js**: 더 많은 차트 타입, 커스터마이징 가능

**Coverage 히스토리 차트 예시 (Recharts)**:
```tsx
<LineChart width={600} height={300} data={historyData}>
  <CartesianGrid strokeDasharray="3 3" />
  <XAxis dataKey="date" />
  <YAxis />
  <Tooltip />
  <Legend />
  <Line type="monotone" dataKey="coverage" stroke="#8884d8" strokeWidth={2} />
</LineChart>
```

**IF** 히스토리 데이터가 없으면, **THEN** 시스템은 "아직 히스토리 데이터가 없습니다" 메시지를 표시해야 한다.

**WHILE** 차트가 렌더링되는 동안, **THEN** 시스템은 반응형으로 크기를 조정해야 한다 (컨테이너 너비에 맞춰).

### Phase 5: 성능 최적화

#### @REQ:FRONTEND-INTEGRATION-001-R09 Performance Optimization
**WHEN** 에이전트 카드 수가 100개를 초과하면, **THEN** 시스템은 다음 최적화를 적용해야 한다:

**1. React.memo 래핑**:
```typescript
export const AgentCard = React.memo(({ agent, onChatClick, onHistoryClick }) => {
  // 컴포넌트 로직
}, (prevProps, nextProps) => {
  // 커스텀 비교 함수
  return prevProps.agent.agent_id === nextProps.agent.agent_id &&
         prevProps.agent.current_xp === nextProps.agent.current_xp &&
         prevProps.agent.level === nextProps.agent.level;
});
```

**2. 가상 스크롤링 (react-window)**:
```typescript
import { FixedSizeGrid } from 'react-window';

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
      <div style={style}>
        <AgentCard agent={agent} />
      </div>
    ) : null;
  }}
</FixedSizeGrid>
```

**3. Code Splitting**:
```typescript
const AgentDetailPage = React.lazy(() => import('./pages/AgentDetailPage'));
const AgentHistoryPage = React.lazy(() => import('./pages/AgentHistoryPage'));

<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route path="/agents/:id" element={<AgentDetailPage />} />
    <Route path="/agents/:id/history" element={<AgentHistoryPage />} />
  </Routes>
</Suspense>
```

**4. 이미지 최적화** (해당되는 경우):
- Lazy loading: `<img loading="lazy" />`
- WebP 포맷 사용
- Responsive images: `srcset`, `sizes` 속성

**5. 번들 크기 최적화**:
- Tree shaking: 사용하지 않는 코드 제거
- Minification: Vite 자동 처리
- Gzip/Brotli 압축: 프로덕션 빌드

**성능 목표**:
- First Contentful Paint (FCP): < 1.5초
- Time to Interactive (TTI): < 3.5초
- Largest Contentful Paint (LCP): < 2.5초
- Total Bundle Size (gzipped): < 200KB (초기 로드)

## 명세 (Specifications)

### 1. API 클라이언트 구현

#### `lib/config/env.ts` - 환경 변수 검증
```typescript
import { z } from 'zod';

const envSchema = z.object({
  VITE_API_URL: z.string().url(),
  VITE_API_KEY: z.string().min(1),
  VITE_API_TIMEOUT: z.coerce.number().positive().default(10000),
  VITE_ENABLE_POLLING: z.coerce.boolean().default(true),
  VITE_POLLING_INTERVAL: z.coerce.number().positive().default(5000),
  VITE_ENABLE_VIRTUAL_SCROLL: z.coerce.boolean().default(true),
  VITE_VIRTUAL_SCROLL_THRESHOLD: z.coerce.number().positive().default(100),
});

export type Env = z.infer<typeof envSchema>;

export const env = envSchema.parse({
  VITE_API_URL: import.meta.env.VITE_API_URL,
  VITE_API_KEY: import.meta.env.VITE_API_KEY,
  VITE_API_TIMEOUT: import.meta.env.VITE_API_TIMEOUT,
  VITE_ENABLE_POLLING: import.meta.env.VITE_ENABLE_POLLING,
  VITE_POLLING_INTERVAL: import.meta.env.VITE_POLLING_INTERVAL,
  VITE_ENABLE_VIRTUAL_SCROLL: import.meta.env.VITE_ENABLE_VIRTUAL_SCROLL,
  VITE_VIRTUAL_SCROLL_THRESHOLD: import.meta.env.VITE_VIRTUAL_SCROLL_THRESHOLD,
});
```

#### `lib/api/client.ts` - API 클라이언트
```typescript
import axios, { AxiosInstance, AxiosError } from 'axios';
import { env } from '../config/env';

export class APIError extends Error {
  constructor(
    public status: number,
    public title: string,
    public detail: string,
    public type?: string
  ) {
    super(detail);
    this.name = 'APIError';
  }
}

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: env.VITE_API_URL,
      timeout: env.VITE_API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${env.VITE_API_KEY}`,
      },
    });

    this.client.interceptors.response.use(
      response => response,
      (error: AxiosError) => {
        if (error.response) {
          const { status, data } = error.response;
          const problemDetails = data as any;
          throw new APIError(
            status,
            problemDetails.title || 'Request Failed',
            problemDetails.detail || error.message,
            problemDetails.type
          );
        } else if (error.request) {
          throw new APIError(0, 'Network Error', '네트워크 연결을 확인해주세요');
        } else {
          throw new APIError(0, 'Unknown Error', error.message);
        }
      }
    );
  }

  async get<T>(url: string, params?: any): Promise<T> {
    const response = await this.client.get<T>(url, { params });
    return response.data;
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.post<T>(url, data);
    return response.data;
  }

  async patch<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.patch<T>(url, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete<T>(url);
    return response.data;
  }
}

export const apiClient = new APIClient();
```

#### `lib/api/agents.ts` - 에이전트 API 함수
```typescript
import { apiClient } from './client';
import { AgentResponse, AgentListResponse, CoverageResponse } from './types';

export async function fetchAgents(params?: {
  level?: number;
  min_coverage?: number;
  max_results?: number;
}): Promise<AgentResponse[]> {
  const response = await apiClient.get<AgentListResponse>('/api/v1/agents', params);
  return response.agents;
}

export async function fetchAgent(agentId: string): Promise<AgentResponse> {
  return apiClient.get<AgentResponse>(`/api/v1/agents/${agentId}`);
}

export async function calculateCoverage(agentId: string): Promise<CoverageResponse> {
  return apiClient.get<CoverageResponse>(`/api/v1/agents/${agentId}/coverage`);
}
```

#### `lib/api/xp.ts` - XP API 함수
```typescript
import { apiClient } from './client';

export interface AwardXPRequest {
  agentId: string;
  amount: number;
  reason: 'chat' | 'positive_feedback' | 'ragas_bonus';
}

export interface AwardXPResponse {
  agent_id: string;
  current_xp: number;
  new_level: number;
  leveled_up: boolean;
}

export async function awardXP(request: AwardXPRequest): Promise<AwardXPResponse> {
  return apiClient.post<AwardXPResponse>(
    `/api/v1/agents/${request.agentId}/xp`,
    { amount: request.amount, reason: request.reason }
  );
}
```

#### `lib/api/history.ts` - 히스토리 API 함수
```typescript
import { apiClient } from './client';

export interface CoverageHistoryItem {
  date: string; // ISO 8601
  coverage: number;
  xp: number;
}

export interface CoverageHistoryResponse {
  agent_id: string;
  history: CoverageHistoryItem[];
  interval: 'daily' | 'weekly' | 'monthly';
}

export async function fetchCoverageHistory(
  agentId: string,
  params?: {
    start_date?: string;
    end_date?: string;
    interval?: 'daily' | 'weekly' | 'monthly';
  }
): Promise<CoverageHistoryResponse> {
  return apiClient.get<CoverageHistoryResponse>(
    `/api/v1/agents/${agentId}/coverage/history`,
    params
  );
}
```

### 2. React Query 훅 구현

#### `hooks/useAgents.ts` - 업데이트 버전
```typescript
import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { fetchAgents } from '../lib/api/agents';
import { AgentResponse } from '../lib/api/types';

export function useAgents(params?: {
  level?: number;
  min_coverage?: number;
  max_results?: number;
}): UseQueryResult<AgentResponse[], Error> {
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

#### `hooks/useAgent.ts` - 단일 에이전트 조회
```typescript
import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { fetchAgent } from '../lib/api/agents';
import { AgentResponse } from '../lib/api/types';
import { env } from '../lib/config/env';

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

#### `hooks/useXPAward.ts` - XP 증가 mutation
```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { awardXP, AwardXPRequest, AwardXPResponse } from '../lib/api/xp';
import { AgentResponse } from '../lib/api/types';

export function useXPAward() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: awardXP,
    onMutate: async (request: AwardXPRequest) => {
      await queryClient.cancelQueries({ queryKey: ['agent', request.agentId] });
      const previousAgent = queryClient.getQueryData<AgentResponse>(['agent', request.agentId]);

      if (previousAgent) {
        queryClient.setQueryData<AgentResponse>(['agent', request.agentId], {
          ...previousAgent,
          current_xp: previousAgent.current_xp + request.amount,
        });
      }

      return { previousAgent };
    },
    onError: (err, request, context) => {
      if (context?.previousAgent) {
        queryClient.setQueryData(['agent', request.agentId], context.previousAgent);
      }
    },
    onSettled: (data, error, request) => {
      queryClient.invalidateQueries({ queryKey: ['agent', request.agentId] });
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}
```

#### `hooks/useCoverageHistory.ts` - 히스토리 데이터
```typescript
import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { fetchCoverageHistory, CoverageHistoryResponse } from '../lib/api/history';

export function useCoverageHistory(
  agentId: string,
  params?: {
    start_date?: string;
    end_date?: string;
    interval?: 'daily' | 'weekly' | 'monthly';
  }
): UseQueryResult<CoverageHistoryResponse, Error> {
  return useQuery({
    queryKey: ['coverageHistory', agentId, params],
    queryFn: () => fetchCoverageHistory(agentId, params),
    staleTime: 60_000,
    cacheTime: 600_000,
    enabled: !!agentId,
  });
}
```

#### `hooks/useInterval.ts` - Polling 유틸리티
```typescript
import { useEffect, useRef } from 'react';

export function useInterval(callback: () => void, delay: number | null) {
  const savedCallback = useRef<() => void>();

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (delay === null) return;

    const id = setInterval(() => {
      savedCallback.current?.();
    }, delay);

    return () => clearInterval(id);
  }, [delay]);
}
```

### 3. 페이지 구현

#### `pages/AgentDetailPage.tsx`
```typescript
import { useParams, Link } from 'react-router-dom';
import { useAgent } from '../hooks/useAgent';
import { useXPAward } from '../hooks/useXPAward';
import { AgentDetailCard } from '../components/agent-detail/AgentDetailCard';
import { LevelUpTimeline } from '../components/agent-detail/LevelUpTimeline';
import { XPAwardButton } from '../components/agent-detail/XPAwardButton';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';

export function AgentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: agent, isLoading, error } = useAgent(id!);
  const { mutate: awardXPMutation, isLoading: isAwarding } = useXPAward();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!agent) return <div>에이전트를 찾을 수 없습니다</div>;

  const handleAwardXP = (amount: number, reason: string) => {
    awardXPMutation({
      agentId: id!,
      amount,
      reason: reason as any,
    });
  };

  return (
    <div className="container mx-auto p-6">
      <div className="mb-4">
        <Link to="/" className="text-blue-600 hover:underline">← 목록으로 돌아가기</Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <AgentDetailCard agent={agent} />
        </div>

        <div>
          <XPAwardButton
            onAward={handleAwardXP}
            isLoading={isAwarding}
          />
          <Link
            to={`/agents/${id}/history`}
            className="mt-4 block text-center py-2 bg-gray-200 rounded-lg hover:bg-gray-300"
          >
            히스토리 보기
          </Link>
        </div>
      </div>

      <div className="mt-8">
        <LevelUpTimeline agentId={id!} />
      </div>
    </div>
  );
}
```

#### `pages/AgentHistoryPage.tsx`
```typescript
import { useParams, Link } from 'react-router-dom';
import { useState } from 'react';
import { useAgent } from '../hooks/useAgent';
import { useCoverageHistory } from '../hooks/useCoverageHistory';
import { CoverageChart } from '../components/history/CoverageChart';
import { XPGrowthChart } from '../components/history/XPGrowthChart';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';

type Period = '7d' | '30d' | 'all';

export function AgentHistoryPage() {
  const { id } = useParams<{ id: string }>();
  const [period, setPeriod] = useState<Period>('30d');
  const { data: agent, isLoading: agentLoading } = useAgent(id!);
  const { data: history, isLoading: historyLoading } = useCoverageHistory(id!, {
    interval: period === '7d' ? 'daily' : period === '30d' ? 'daily' : 'weekly',
  });

  if (agentLoading || historyLoading) return <LoadingSpinner />;
  if (!agent || !history) return <div>데이터를 찾을 수 없습니다</div>;

  return (
    <div className="container mx-auto p-6">
      <div className="mb-4 flex items-center justify-between">
        <Link to={`/agents/${id}`} className="text-blue-600 hover:underline">
          ← {agent.name} 상세로 돌아가기
        </Link>

        <div className="flex gap-2">
          <button
            onClick={() => setPeriod('7d')}
            className={`px-4 py-2 rounded ${period === '7d' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            7일
          </button>
          <button
            onClick={() => setPeriod('30d')}
            className={`px-4 py-2 rounded ${period === '30d' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            30일
          </button>
          <button
            onClick={() => setPeriod('all')}
            className={`px-4 py-2 rounded ${period === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            전체
          </button>
        </div>
      </div>

      <h1 className="text-2xl font-bold mb-6">{agent.name} 성장 히스토리</h1>

      <div className="space-y-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">커버리지 변화</h2>
          <CoverageChart data={history.history} />
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">XP 증가량</h2>
          <XPGrowthChart data={history.history} />
        </div>
      </div>
    </div>
  );
}
```

### 4. 컴포넌트 구현

#### `components/agent-detail/XPAwardButton.tsx`
```typescript
interface XPAwardButtonProps {
  onAward: (amount: number, reason: string) => void;
  isLoading: boolean;
}

export function XPAwardButton({ onAward, isLoading }: XPAwardButtonProps) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="font-semibold mb-3">XP 부여</h3>
      <div className="space-y-2">
        <button
          onClick={() => onAward(10, 'chat')}
          disabled={isLoading}
          className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400"
        >
          대화 완료 (+10 XP)
        </button>
        <button
          onClick={() => onAward(50, 'positive_feedback')}
          disabled={isLoading}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
        >
          긍정 피드백 (+50 XP)
        </button>
        <button
          onClick={() => onAward(100, 'ragas_bonus')}
          disabled={isLoading}
          className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400"
        >
          RAGAS 보너스 (+100 XP)
        </button>
      </div>
    </div>
  );
}
```

#### `components/history/CoverageChart.tsx`
```typescript
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { CoverageHistoryItem } from '../../lib/api/history';

interface CoverageChartProps {
  data: CoverageHistoryItem[];
}

export function CoverageChart({ data }: CoverageChartProps) {
  const chartData = data.map(item => ({
    date: new Date(item.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
    coverage: item.coverage,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis domain={[0, 100]} label={{ value: 'Coverage (%)', angle: -90, position: 'insideLeft' }} />
        <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
        <Legend />
        <Line type="monotone" dataKey="coverage" stroke="#8884d8" strokeWidth={2} name="커버리지" />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

#### `components/history/XPGrowthChart.tsx`
```typescript
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { CoverageHistoryItem } from '../../lib/api/history';

interface XPGrowthChartProps {
  data: CoverageHistoryItem[];
}

export function XPGrowthChart({ data }: XPGrowthChartProps) {
  const chartData = data.map((item, index) => {
    const previousXP = index > 0 ? data[index - 1].xp : 0;
    const xpGain = item.xp - previousXP;
    return {
      date: new Date(item.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
      xpGain: xpGain > 0 ? xpGain : 0,
    };
  });

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis label={{ value: 'XP 증가량', angle: -90, position: 'insideLeft' }} />
        <Tooltip formatter={(value: number) => `+${value} XP`} />
        <Legend />
        <Bar dataKey="xpGain" fill="#82ca9d" name="XP 증가" />
      </BarChart>
    </ResponsiveContainer>
  );
}
```

#### `components/common/VirtualList.tsx`
```typescript
import { FixedSizeGrid } from 'react-window';
import { AgentResponse } from '../../lib/api/types';
import { AgentCard } from '../agent-card/AgentCard';

interface VirtualListProps {
  agents: AgentResponse[];
  columnCount: number;
  columnWidth: number;
  rowHeight: number;
  height: number;
  width: number;
}

export function VirtualList({
  agents,
  columnCount,
  columnWidth,
  rowHeight,
  height,
  width,
}: VirtualListProps) {
  const rowCount = Math.ceil(agents.length / columnCount);

  return (
    <FixedSizeGrid
      columnCount={columnCount}
      columnWidth={columnWidth}
      height={height}
      rowCount={rowCount}
      rowHeight={rowHeight}
      width={width}
    >
      {({ columnIndex, rowIndex, style }) => {
        const index = rowIndex * columnCount + columnIndex;
        const agent = agents[index];
        return agent ? (
          <div style={style} className="p-2">
            <AgentCard agent={agent} />
          </div>
        ) : null;
      }}
    </FixedSizeGrid>
  );
}
```

### 5. 라우팅 설정

#### `App.tsx` - 업데이트 버전
```typescript
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Suspense, lazy } from 'react';
import HomePage from './pages/HomePage';
import { LoadingSpinner } from './components/common/LoadingSpinner';
import { ErrorBoundary } from './components/common/ErrorBoundary';

const AgentDetailPage = lazy(() => import('./pages/AgentDetailPage'));
const AgentHistoryPage = lazy(() => import('./pages/AgentHistoryPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 30_000,
      cacheTime: 300_000,
    },
  },
});

const router = createBrowserRouter([
  {
    path: '/',
    element: <HomePage />,
  },
  {
    path: '/agents/:id',
    element: (
      <Suspense fallback={<LoadingSpinner />}>
        <AgentDetailPage />
      </Suspense>
    ),
  },
  {
    path: '/agents/:id/history',
    element: (
      <Suspense fallback={<LoadingSpinner />}>
        <AgentHistoryPage />
      </Suspense>
    ),
  },
  {
    path: '*',
    element: (
      <Suspense fallback={<LoadingSpinner />}>
        <NotFoundPage />
      </Suspense>
    ),
  },
]);

export default function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
```

## 추적성 (Traceability)

### 연관 SPEC
- `SPEC-AGENT-CARD-001` (v0.1.0, completed): Pokemon 스타일 에이전트 카드 UI
- `SPEC-AGENT-GROWTH-002` (v0.1.0, draft): 백엔드 Agent Growth API
- `SPEC-FRONTEND-INIT-001` (v0.1.0, completed): 프론트엔드 초기화

### TAG 체인
```
@SPEC:FRONTEND-INTEGRATION-001
  ├─> Phase 1: 백엔드 통합
  │   ├─> @CODE:FRONTEND-INTEGRATION-001:API-CLIENT (lib/api/client.ts)
  │   ├─> @CODE:FRONTEND-INTEGRATION-001:ENV-CONFIG (lib/config/env.ts)
  │   ├─> @CODE:FRONTEND-INTEGRATION-001:AGENTS-API (lib/api/agents.ts)
  │   ├─> @CODE:FRONTEND-INTEGRATION-001:XP-API (lib/api/xp.ts)
  │   └─> @CODE:FRONTEND-INTEGRATION-001:HISTORY-API (lib/api/history.ts)
  │
  ├─> Phase 2: 라우팅
  │   ├─> @CODE:FRONTEND-INTEGRATION-001:ROUTING (App.tsx)
  │   ├─> @CODE:FRONTEND-INTEGRATION-001:AGENT-HOOK (hooks/useAgent.ts)
  │   └─> @CODE:FRONTEND-INTEGRATION-001:DETAIL-PAGE (pages/AgentDetailPage.tsx)
  │
  ├─> Phase 3: 인터랙션
  │   ├─> @CODE:FRONTEND-INTEGRATION-001:XP-HOOK (hooks/useXPAward.ts)
  │   ├─> @CODE:FRONTEND-INTEGRATION-001:XP-BUTTON (components/agent-detail/XPAwardButton.tsx)
  │   └─> @CODE:FRONTEND-INTEGRATION-001:INTERVAL-HOOK (hooks/useInterval.ts)
  │
  ├─> Phase 4: 히스토리
  │   ├─> @CODE:FRONTEND-INTEGRATION-001:HISTORY-HOOK (hooks/useCoverageHistory.ts)
  │   ├─> @CODE:FRONTEND-INTEGRATION-001:HISTORY-PAGE (pages/AgentHistoryPage.tsx)
  │   ├─> @CODE:FRONTEND-INTEGRATION-001:COVERAGE-CHART (components/history/CoverageChart.tsx)
  │   └─> @CODE:FRONTEND-INTEGRATION-001:XP-CHART (components/history/XPGrowthChart.tsx)
  │
  └─> Phase 5: 성능 최적화
      ├─> @CODE:FRONTEND-INTEGRATION-001:VIRTUAL-LIST (components/common/VirtualList.tsx)
      ├─> @CODE:FRONTEND-INTEGRATION-001:ERROR-BOUNDARY (components/common/ErrorBoundary.tsx)
      └─> @CODE:FRONTEND-INTEGRATION-001:MEMO-CARDS (components/agent-card/AgentCard.tsx)

@TEST:FRONTEND-INTEGRATION-001 (테스트 파일)
  ├─> @TEST:FRONTEND-INTEGRATION-001:API-CLIENT
  ├─> @TEST:FRONTEND-INTEGRATION-001:HOOKS
  ├─> @TEST:FRONTEND-INTEGRATION-001:PAGES
  └─> @TEST:FRONTEND-INTEGRATION-001:COMPONENTS
```

## 제약사항 (Constraints)

### 기술적 제약

1. **백엔드 API 의존성**:
   - XP 엔드포인트 미구현 → 클라이언트 사이드 임시 처리
   - 히스토리 엔드포인트 미구현 → Phase 4에서 백엔드 추가 필요
   - 실시간 알림 미구현 → Polling 방식으로 대체

2. **CORS 설정**:
   - 백엔드에서 `Access-Control-Allow-Origin` 헤더 설정 필요
   - Preflight 요청 처리 (OPTIONS 메서드)

3. **인증 방식**:
   - API Key 기반 인증 (Bearer Token)
   - 환경 변수로 관리 (프론트엔드 노출 주의)

### 성능 제약

1. **Polling 간격**:
   - 5초 간격 (너무 짧으면 서버 부하)
   - 환경 변수로 조정 가능 (`VITE_POLLING_INTERVAL`)

2. **가상 스크롤 임계값**:
   - 100개 이상일 때 활성화
   - 환경 변수로 조정 가능 (`VITE_VIRTUAL_SCROLL_THRESHOLD`)

3. **번들 크기**:
   - Recharts 또는 Chart.js 추가로 번들 크기 증가 예상
   - Tree shaking으로 최소화

### 보안 제약

1. **API Key 노출**:
   - 프론트엔드 환경 변수는 클라이언트에 노출됨
   - 백엔드에서 Rate Limiting 필수
   - IP 기반 접근 제어 권장

2. **XSS 방어**:
   - React의 기본 XSS 방어 활용
   - `dangerouslySetInnerHTML` 사용 금지

3. **CSRF 방어**:
   - SameSite Cookie 설정 (백엔드)
   - CSRF Token 사용 (향후 추가)

## 향후 확장성

### Phase 6: 고급 기능 (백엔드 추가 후)

1. **실시간 알림**:
   - WebSocket 또는 Server-Sent Events (SSE)
   - 레벨업, 커버리지 증가 알림

2. **에이전트 비교**:
   - 여러 에이전트 선택하여 비교
   - 병렬 차트 표시

3. **필터링 & 정렬**:
   - 레벨, 희귀도, 품질 점수별 필터
   - 커버리지, XP, 생성일 기준 정렬

### Phase 7: UX 개선

1. **다크 모드**:
   - Tailwind CSS 다크 모드 지원
   - 사용자 선호도 저장

2. **애니메이션 개선**:
   - framer-motion을 활용한 페이지 전환
   - 스켈레톤 UI 개선

3. **접근성 향상**:
   - WCAG 2.1 AAA 준수
   - 스크린 리더 최적화

---

**작성일**: 2025-10-30
**작성자**: @bridge25
**버전**: 0.0.1 (INITIAL)

## HISTORY

### v0.0.1 - 2025-10-30 - SPEC 초안 작성

#### 작성 내용
- ✅ 5단계 구현 계획 (Phase 1-5)
- ✅ 9개 핵심 기능 정의
- ✅ 백엔드 API 연동 명세
- ✅ TanStack Query 통합 전략
- ✅ 라우팅 시스템 설계
- ✅ 성능 최적화 방안
- ✅ EARS 요구사항 9개 작성
- ✅ 상세 명세 (API 클라이언트, 훅, 페이지, 컴포넌트)

#### 기술 스택
- React 19.1.1
- TypeScript 5.9.3
- TanStack Query 5.90.5
- React Router DOM 7.9.5
- Recharts 2.14.1 (또는 Chart.js 4.5.0)
- react-window 1.8.10

#### 다음 단계
- `/alfred:2-run SPEC-FRONTEND-INTEGRATION-001` 실행
- TDD 구현 (RED → GREEN → REFACTOR)
- 백엔드 XP/히스토리 API 추가 (별도 SPEC)
