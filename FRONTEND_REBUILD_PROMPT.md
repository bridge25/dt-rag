# DT-RAG 프론트엔드 재구현 프롬프트 (AI UI/UX 도구용)

---

## ⚡ 빠른 시작 (AI 도구에게 먼저 보여줄 요약)

### 핵심 요구사항
1. **일반 사용자 페이지 (/) - 우선순위 1번**
   - Google 스타일 간단한 검색 페이지
   - ❌ 시스템 메트릭, 응답시간, DB 상태 표시하지 말 것
   - ✅ 깔끔한 검색창 + 결과 카드만 표시

2. **관리자 페이지 (/admin) - 우선순위 2번**
   - 로그인 후에만 접근 가능
   - ✅ 여기서만 상세한 시스템 메트릭 표시
   - Dashboard 디자인 (Total Documents, Today's Searches, Avg Response Time, HITL Queue 등)

3. **기술 스택 (필수)**
   - Next.js 14, TypeScript, Tailwind CSS
   - TanStack React Query, Zod, Axios

### 구현 순서
```
1단계: app/page.tsx (메인 검색 - Google 스타일) ⭐ 가장 중요
2단계: app/upload/page.tsx (문서 업로드)
3단계: app/documents/page.tsx (문서 목록)
4단계: app/admin/login/page.tsx (관리자 로그인)
5단계: app/admin/page.tsx (관리자 Dashboard)
```

---

## 📋 프로젝트 개요

**프로젝트명**: Dynamic Taxonomy RAG System Frontend
**목적**: ML 기반 문서 분류 및 하이브리드 검색(BM25 + Vector)을 제공하는 RAG 시스템의 사용자 인터페이스
**사용자 타입**: 일반 사용자 + 시스템 관리자 (명확히 분리)

---

## 🛠️ 기술 스택 (필수 준수)

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 3.4
- **State Management**: TanStack React Query v5
- **Form Validation**: Zod v4
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **UI Components**: Radix UI + Shadcn/ui 패턴

### Backend API (이미 구현됨)
- **Base URL**: `http://localhost:8000` (API Server)
- **Orchestration URL**: `http://localhost:8001` (LangGraph Pipeline)
- **Authentication**: `X-API-Key` 헤더 (MVP는 모든 키 허용)
- **Response Format**: JSON with Pydantic 모델

---

## 🎯 구현 범위

## ⚠️ 중요: 사용자 분리

### 일반 사용자 (/)
- **목적**: 검색 및 문서 관리
- **특징**: 간단하고 직관적인 UI
- **페이지**: 검색, 문서 업로드, 문서 목록, Taxonomy 탐색
- **❌ 표시하지 않을 것**: 시스템 메트릭, 응답시간, DB 상태, API 통계

### 관리자 (/admin)
- **목적**: 시스템 모니터링 및 관리
- **특징**: 상세한 메트릭 및 시스템 상태
- **인증**: 로그인 필요 (admin 권한)
- **페이지**: Dashboard, HITL Review, Agent 관리, Monitoring
- **✅ 표시할 것**: 모든 시스템 메트릭, 통계, 로그

---

### Phase 1: 일반 사용자 인터페이스 (우선순위 1)

#### 1.1 메인 검색 페이지 (/)
**목적**: Google처럼 간단한 검색 경험 제공
**스타일**: 미니멀, 사용자 친화적

**기능 요구사항**:
- [ ] 중앙 배치된 검색창 (Google 스타일)
- [ ] 실시간 검색 결과 표시 (타이핑 중 debounce 500ms)
- [ ] 검색 모드 선택: Hybrid(기본) / BM25 only / Vector only
- [ ] Taxonomy 필터 (드롭다운으로 카테고리 선택)
- [ ] 검색 결과 카드:
  - 문서 제목 (클릭 시 원본 URL)
  - 텍스트 발췌 (highlight 적용)
  - 관련도 점수 (0.0-1.0)
  - Taxonomy 경로 뱃지 (예: AI > RAG)
  - 출처 메타데이터 (날짜, 저자)
- [ ] 무한 스크롤 또는 페이지네이션

**API 엔드포인트**:
```typescript
POST /search
Request: {
  q: string,
  filters?: { canonical_in?: string[][] },
  bm25_topk?: number,
  vector_topk?: number,
  final_topk?: number
}
Response: {
  hits: SearchHit[],
  latency: number,
  request_id: string,
  total_candidates: number
}
```

**디자인 가이드** (Google 스타일):
- 배경: 단순한 흰색 또는 연한 그라데이션
- 로고/제목: 중앙 상단 (DT-RAG 또는 서비스 명)
- 검색창: 화면 중앙, 큰 사이즈 (h-14), 부드러운 그림자
- 결과 카드: 흰색 배경, rounded-xl, hover 시 미세한 그림자
- **❌ 제외**: 시스템 상태, 응답시간 ms, DB 메트릭

**레이아웃 예시**:
```
+----------------------------------+
|        [DT-RAG Logo]             |
|                                  |
|   +------------------------+     |
|   |  🔍 Search...          |     |
|   +------------------------+     |
|   [Hybrid] [BM25] [Vector]       |
|                                  |
|   검색 결과 (간단한 카드 형태)     |
|   +--------------------------+   |
|   | 📄 문서 제목              |   |
|   | "텍스트 미리보기..."       |   |
|   | AI > RAG  ⭐ 0.92        |   |
|   +--------------------------+   |
+----------------------------------+
```

---

#### 1.2 문서 업로드 페이지 (/upload)
**목적**: 사용자가 문서를 시스템에 추가

**기능 요구사항**:
- [ ] Drag & Drop 파일 업로드 영역
- [ ] 지원 파일 형식 표시 (PDF, DOCX, TXT, MD)
- [ ] 업로드 진행률 표시 (ProgressBar)
- [ ] 업로드 후 자동 분류 시작
- [ ] 분류 결과 미리보기 (Taxonomy path, confidence)
- [ ] 분류 결과에 대한 피드백 버튼 (👍 / 👎)

**API 엔드포인트**:
```typescript
POST /ingestion/upload (multipart/form-data)
Response: {
  document_id: string,
  title: string,
  chunks_created: number,
  processing_status: string
}

POST /classify
Request: {
  text: string,
  chunk_id?: string
}
Response: {
  canonical: string[],
  confidence: number,
  reasoning: string[],
  hitl: boolean
}
```

---

#### 1.3 문서 브라우저 (/documents)
**목적**: 업로드된 문서 목록 및 관리

**기능 요구사항**:
- [ ] 문서 목록 테이블 (제목, 업로드 날짜, 청크 수, 상태)
- [ ] 필터: 상태별, 날짜 범위, Taxonomy 경로
- [ ] 정렬: 최신순, 제목순, 관련도순
- [ ] 문서 삭제 버튼 (확인 다이얼로그)
- [ ] 문서 상세보기 모달 (청크 목록, 메타데이터)
- [ ] 검색 기능 (문서 제목/내용 검색)

---

#### 1.4 Taxonomy 탐색 페이지 (/taxonomy)
**목적**: 분류 체계 시각화 및 탐색

**기능 요구사항**:
- [ ] 트리 구조 시각화 (접기/펴기 가능)
- [ ] 노드 클릭 시 해당 카테고리 문서 목록 표시
- [ ] 각 노드에 문서 개수 뱃지
- [ ] 검색 기능 (노드 이름으로 필터링)
- [ ] Breadcrumb 네비게이션

**API 엔드포인트**:
```typescript
GET /taxonomy/{version}/tree
Response: TaxonomyNode[] (재귀적 children)
```

---

### Phase 2: 관리자 대시보드 (우선순위 2)

⚠️ **중요**: 이 섹션은 `/admin` 경로 하위에만 구현됩니다. 일반 사용자는 접근 불가.

#### 2.1 관리자 인증
**필수 구현**:
- [ ] 로그인 페이지 (/admin/login)
- [ ] 세션 관리 (localStorage 또는 쿠키)
- [ ] 보호된 라우트 (middleware.ts)
- [ ] 로그아웃 기능

```typescript
// middleware.ts
export function middleware(request: NextRequest) {
  const token = request.cookies.get('admin-token')

  if (request.nextUrl.pathname.startsWith('/admin')) {
    if (!token) {
      return NextResponse.redirect(new URL('/admin/login', request.url))
    }
  }
}
```

#### 2.2 대시보드 레이아웃 (/admin/*)
**구조**:
```
+------------------+------------------------+
|                  |  Header (search, user) |
|  Sidebar (nav)   +------------------------+
|                  |                        |
|  - Dashboard     |  Main Content Area     |
|  - Search        |                        |
|  - Documents     |                        |
|  - Taxonomy      |                        |
|  - Agents        |                        |
|  - HITL Review   |                        |
|  - Monitoring    |                        |
|                  |                        |
+------------------+------------------------+
```

**Sidebar 메뉴**:
- Dashboard (LayoutDashboard icon)
- Search (Search icon)
- Documents (FileText icon)
- Taxonomy (Network icon)
- Agents (Bot icon)
- HITL Review (UserCheck icon)
- Monitoring (Activity icon)

---

#### 2.3 관리자 Dashboard (/admin)
**목적**: 시스템 전체 상태 한눈에 파악 (관리자 전용)

**⚠️ 이 페이지는 관리자만 접근 가능합니다**

**메트릭 카드** (4개 카드):
- [ ] 총 문서 수 (실제 DB 조회) - 예: "2,847" with "+12% from last month"
- [ ] 오늘 검색 횟수 (실제 로그 집계) - 예: "1,234" with "+8% from yesterday"
- [ ] 평균 검색 지연시간 (실시간 계산) - 예: "247ms" with "↓ 3% slower"
- [ ] HITL 대기 작업 수 (실제 큐 조회) - 예: "12" with "⚠️ Needs attention"

**차트**:
- [ ] 검색 트렌드 (Line Chart, 최근 7일)
- [ ] Taxonomy 분포 (Donut Chart)
- [ ] 검색 지연시간 분포 (Histogram)

**시스템 상태 섹션**:
- [ ] Database: Healthy/Warning
- [ ] Redis Cache: Healthy/Warning
- [ ] Search Engine: Healthy/Warning
- [ ] API Gateway: Healthy/Warning

**최근 활동 섹션**:
- [ ] 최근 검색 쿼리 테이블 (Query, Results, Response Time, Timestamp)
- [ ] 최근 문서 업로드
- [ ] 최근 HITL 검토 완료
- [ ] 최근 에이전트 생성

**API 엔드포인트**:
```typescript
GET /healthz
Response: {
  status: string,
  database: string,
  redis: string,
  version: string
}
```

---

#### 2.4 HITL Review 페이지 (/admin/hitl)
**목적**: 낮은 신뢰도 분류 결과를 사람이 검토

**기능 요구사항**:
- [ ] 리뷰 대기 큐 (confidence < 0.70인 항목)
- [ ] 우선순위 정렬 (confidence 낮은 순)
- [ ] 문서 내용 미리보기
- [ ] 제안된 Taxonomy 경로 표시
- [ ] 대안 경로 제시 (alternatives)
- [ ] 승인/거부/수정 버튼
- [ ] 검토자 메모 입력
- [ ] 검토 완료 후 자동 학습 반영

**API 엔드포인트**:
```typescript
GET /classify/hitl/tasks
Response: HITLTask[]

POST /classify/hitl/review
Request: {
  chunk_id: string,
  approved_path: string[],
  reviewer_notes?: string
}
```

---

#### 2.5 Agent 관리 페이지 (/admin/agents)
**목적**: LangGraph 에이전트 생성 및 모니터링

**기능 요구사항**:
- [ ] 에이전트 목록 (이름, 상태, 생성일)
- [ ] 카테고리 기반 에이전트 생성 (FromCategory)
- [ ] 에이전트 상세 정보 (allowed_category_paths, retrieval config)
- [ ] 에이전트 활성화/비활성화 토글
- [ ] 에이전트 메트릭 (사용 횟수, 성공률, 평균 응답시간)
- [ ] 에이전트 삭제 (확인 다이얼로그)

**API 엔드포인트**:
```typescript
POST /agents/from-category
Request: {
  version: string,
  node_paths: string[][],
  options?: {}
}

GET /agents/
Response: { agents: AgentStatus[] }

GET /agents/{agent_id}/metrics
Response: AgentMetrics
```

---

#### 2.6 Monitoring 페이지 (/admin/monitoring)
**목적**: 실시간 시스템 모니터링

**기능 요구사항**:
- [ ] 시스템 리소스 (CPU, Memory, Disk)
- [ ] API 응답시간 (p50, p95, p99)
- [ ] 에러율 (최근 1시간)
- [ ] 활성 세션 수
- [ ] 로그 스트림 (최근 100개 로그)
- [ ] 알림 설정 (임계값 초과 시 알림)

---

## 🎨 디자인 시스템

### 색상 팔레트
```css
/* Primary Colors */
--purple: #8B5CF6
--blue: #3B82F6
--teal: #14B8A6
--orange: #F97316
--green: #10B981

/* Background Gradients */
--bg-gradient-1: from-purple-50 via-blue-50 to-teal-50
--bg-gradient-2: from-gray-50 to-gray-100
--bg-gradient-dark: from-gray-900 via-gray-800 to-gray-900

/* Sidebar */
--sidebar-bg: #1e293b (graySidebar)

/* Semantic Colors */
--success: #10B981
--warning: #F59E0B
--error: #EF4444
--info: #3B82F6
```

### Typography
```css
/* Headings */
h1: text-4xl font-bold tracking-tight
h2: text-3xl font-bold
h3: text-2xl font-bold

/* Body */
body: text-base text-gray-900 dark:text-gray-100
small: text-sm text-gray-600 dark:text-gray-400
```

### Spacing
```css
/* Container */
.container: max-w-7xl mx-auto px-6 py-8

/* Card */
.card: p-6 rounded-2xl bg-white shadow-sm

/* Gap */
.grid-gap: gap-6
.stack-gap: space-y-4
```

### Components
```typescript
// ModernCard variants
type Variant = "default" | "dark" | "teal" | "beige" | "purple" | "green"

// IconBadge sizes
type Size = "sm" | "md" | "lg"

// IconBadge colors
type Color = "orange" | "blue" | "purple" | "teal" | "green" | "red"
```

---

## 📡 API 통합 패턴 (필수 준수)

### 1. Axios Client 설정
```typescript
// lib/api/client.ts
import axios from "axios"

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || "dev-key"
  }
})

// 에러 인터셉터
apiClient.interceptors.response.use(
  response => response,
  error => {
    console.error("API Error:", error.response?.status, error.response?.data)
    return Promise.reject(error)
  }
)
```

### 2. Zod 스키마 검증
```typescript
// lib/api/types.ts
import { z } from "zod"

export const SearchRequestSchema = z.object({
  q: z.string().min(1),
  filters: z.object({
    canonical_in: z.array(z.array(z.string())).optional()
  }).optional(),
  bm25_topk: z.number().min(1).max(100).default(12),
  vector_topk: z.number().min(1).max(100).default(12),
  final_topk: z.number().min(1).max(50).default(5)
})

export type SearchRequest = z.infer<typeof SearchRequestSchema>
```

### 3. React Query 훅
```typescript
// lib/api/index.ts
export async function search(request: SearchRequest): Promise<SearchResponse> {
  const validated = SearchRequestSchema.parse(request)
  const response = await apiClient.post("/search", validated)
  return SearchResponseSchema.parse(response.data)
}

// 사용 예시 (컴포넌트에서)
const mutation = useMutation({
  mutationFn: search,
  onSuccess: (data) => {
    console.log("검색 완료:", data.hits.length, "개 결과")
  }
})
```

---

## ✅ 필수 구현 체크리스트

### 코드 품질
- [ ] TypeScript strict mode 활성화
- [ ] 모든 API 요청/응답 Zod 검증
- [ ] 에러 바운더리 구현 (error.tsx)
- [ ] 로딩 상태 처리 (loading.tsx)
- [ ] 404 페이지 (not-found.tsx)

### 성능
- [ ] React Query 캐싱 (staleTime: 60000)
- [ ] 이미지 최적화 (next/image)
- [ ] Code splitting (dynamic import)
- [ ] Debounce 검색 입력 (500ms)

### 접근성
- [ ] Semantic HTML 사용
- [ ] ARIA 레이블 추가
- [ ] 키보드 네비게이션 지원
- [ ] 색상 대비 WCAG AA 준수

### 반응형
- [ ] Mobile first 디자인
- [ ] Tailwind breakpoints 활용 (sm, md, lg, xl)
- [ ] Touch 친화적 UI (버튼 최소 44x44px)

---

## 📁 프로젝트 구조

```
apps/frontend/
├── app/
│   ├── page.tsx           # ⭐ 메인 검색 (일반 사용자)
│   ├── upload/
│   │   └── page.tsx       # 문서 업로드
│   ├── documents/
│   │   └── page.tsx       # 문서 브라우저
│   ├── taxonomy/
│   │   └── page.tsx       # Taxonomy 탐색
│   │
│   ├── admin/             # 🔒 관리자 전용 (인증 필요)
│   │   ├── login/
│   │   │   └── page.tsx   # 로그인 페이지
│   │   ├── layout.tsx     # Sidebar + Header
│   │   ├── page.tsx       # Dashboard (메트릭)
│   │   ├── hitl/          # HITL Review
│   │   ├── agents/        # Agent 관리
│   │   └── monitoring/    # Monitoring
│   ├── api/               # Route Handlers
│   ├── layout.tsx         # 루트 레이아웃
│   ├── error.tsx
│   └── loading.tsx
├── components/
│   ├── ui/                # Shadcn/ui 컴포넌트
│   ├── layout/            # Sidebar, Header
│   ├── search/            # SearchBar, ResultCard
│   ├── taxonomy/          # TreeView
│   └── charts/            # DonutChart, LineChart
├── lib/
│   ├── api/               # API 클라이언트
│   │   ├── client.ts
│   │   ├── index.ts       # API 함수들
│   │   └── types.ts       # Zod 스키마
│   ├── env.ts             # 환경변수 검증
│   └── utils.ts           # 유틸리티 함수
└── package.json
```

---

## 🚀 개발 우선순위

### Sprint 1 (Week 1) - 핵심 사용자 기능
1. ✅ 메인 검색 페이지 (/)
2. ✅ 검색 결과 표시 (SearchResultCard)
3. ✅ API 통합 레이어 (lib/api)
4. ✅ 기본 레이아웃 (루트 layout.tsx)

### Sprint 2 (Week 2) - 문서 관리
1. ✅ 문서 업로드 페이지 (/upload)
2. ✅ 문서 브라우저 (/documents)
3. ✅ Taxonomy 탐색 (/taxonomy)
4. ✅ 에러 처리 개선

### Sprint 3 (Week 3) - 관리자 기능
1. ✅ 관리자 레이아웃 (Sidebar + Header)
2. ✅ Dashboard (/admin)
3. ✅ HITL Review (/admin/hitl)
4. ✅ Agent 관리 (/admin/agents)

### Sprint 4 (Week 4) - 모니터링 및 최적화
1. ✅ Monitoring 페이지 (/admin/monitoring)
2. ✅ 성능 최적화 (캐싱, lazy loading)
3. ✅ 테스트 작성
4. ✅ 문서화

---

## 🔧 환경 변수 (.env.local)

```bash
# API 설정
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_TIMEOUT=30000
NEXT_PUBLIC_API_KEY=your-api-key-here

# Feature Flags
NEXT_PUBLIC_ENABLE_HITL=true
NEXT_PUBLIC_ENABLE_AGENTS=true
NEXT_PUBLIC_ENABLE_MONITORING=true
```

---

## 📝 구현 가이드

### 일반 사용자 메인 페이지 예시 (app/page.tsx)
```typescript
"use client"

import { useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { search } from "@/lib/api"
import { Search, Sparkles } from "lucide-react"

export default function HomePage() {
  const [query, setQuery] = useState("")

  const mutation = useMutation({
    mutationFn: search,
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      mutation.mutate({ q: query, final_topk: 10 })
    }
  }

  return (
    <div className="min-h-screen bg-white">
      {/* 간단한 헤더 */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">DT-RAG</h1>
          <nav className="flex gap-4 text-sm">
            <a href="/upload" className="text-gray-600 hover:text-gray-900">Upload</a>
            <a href="/documents" className="text-gray-600 hover:text-gray-900">Documents</a>
            <a href="/taxonomy" className="text-gray-600 hover:text-gray-900">Taxonomy</a>
          </nav>
        </div>
      </header>

      {/* 검색 중심 레이아웃 (Google 스타일) */}
      <main className="container max-w-3xl mx-auto px-4 pt-32">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Sparkles className="h-8 w-8 text-purple-600" />
            <h1 className="text-5xl font-bold text-gray-900">DT-RAG</h1>
          </div>
          <p className="text-gray-600">
            AI-powered semantic search for your documents
          </p>
        </div>

        {/* 검색창 */}
        <form onSubmit={handleSearch} className="mb-8">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search your knowledge base..."
              className="w-full h-14 pl-12 pr-4 rounded-full border-2 border-gray-200 focus:border-purple-600 focus:outline-none text-lg"
            />
          </div>
        </form>

        {/* 검색 결과 (간단한 카드) */}
        {mutation.isSuccess && (
          <div className="space-y-4">
            {mutation.data.hits.map((hit) => (
              <div
                key={hit.chunk_id}
                className="p-6 bg-white border border-gray-200 rounded-xl hover:shadow-lg transition-shadow"
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {hit.source?.title || "Untitled"}
                </h3>
                <p className="text-gray-600 mb-3 line-clamp-2">
                  {hit.text}
                </p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {hit.taxonomy_path?.map((path, i) => (
                      <span
                        key={i}
                        className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full"
                      >
                        {path}
                      </span>
                    ))}
                  </div>
                  <span className="text-sm text-gray-500">
                    ⭐ {hit.score.toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ❌ 시스템 메트릭 표시하지 않음 */}
        {/* ❌ 응답시간 표시하지 않음 */}
        {/* ❌ DB 상태 표시하지 않음 */}
      </main>
    </div>
  )
}
```

### 관리자 Dashboard 예시 (app/admin/page.tsx)
```typescript
"use client"

import { useQuery } from "@tanstack/react-query"
import { getHealth } from "@/lib/api"

export default function AdminDashboard() {
  const { data: healthData } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 60000,
  })

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">System Dashboard</h1>

      {/* ✅ 관리자용 상세 메트릭 표시 */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          title="Total Documents"
          value="2,847"
          change="+12% from last month"
        />
        <MetricCard
          title="Today's Searches"
          value="1,234"
          change="+8% from yesterday"
        />
        <MetricCard
          title="Avg Response Time"
          value="247ms"
          change="↓ 3% slower"
        />
        <MetricCard
          title="HITL Queue"
          value="12"
          change="⚠️ Needs attention"
        />
      </div>

      {/* System Status */}
      <div className="grid grid-cols-2 gap-4">
        <SystemStatus />
        <RecentActivity />
      </div>
    </div>
  )
}
```

---

## 🎯 최종 목표

**"실제 데이터 기반으로 동작하는 프로덕션 레벨의 RAG 시스템 UI"**

- ❌ 하드코딩된 메트릭 제거
- ✅ 모든 데이터 실제 API에서 조회
- ✅ 에러 처리 완벽 구현
- ✅ 반응형 디자인 100%
- ✅ 접근성 AAA 등급 달성
- ✅ 성능: Lighthouse 90+ 점수

---

## 📚 참고 리소스

- **Backend API Spec**: `apps/api/main.py` (FastAPI)
- **Common Schemas**: `packages/common-schemas/common_schemas/models.py`
- **기존 컴포넌트**: `apps/frontend/components/ui/*`
- **API 함수 예시**: `apps/frontend/lib/api/index.ts`

---

**이 프롬프트를 AI UI/UX 도구에 입력하면, 위 요구사항을 준수하는 프론트엔드 코드를 생성할 수 있습니다.**
