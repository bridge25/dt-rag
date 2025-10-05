# FRONTEND_PLAN.md
# DT-RAG 프론트엔드 재구현 전체 로드맵

> **⚠️ 바이브코딩 7-Stage 루프 준수 필수**
>
> 각 Phase는 반드시 순서대로 진행:
> 1. **Scope** → 2. **Context Load** → 3. **Synthesis** → 4. **Plan** → 5. **Explain** → 6. **Implement** → 7. **Verify**
>
> **절대 금지**:
> - Phase 건너뛰기
> - IG 임계치 미달 상태에서 구현
> - 코드 미확인 항목 구현
> - 모호어 ('적절히', '기본', '일반적으로') 사용

---

## 📋 프로젝트 개요

### 목표
Next.js 14 + shadcn/ui 기반 프로덕션 레벨 프론트엔드 구현

### 비목표 (Non-Goals)
- FastAPI 웹 프론트엔드 유지
- 기존 frontend-admin 마이그레이션
- 모바일 네이티브 앱

### 제약 조건
- TypeScript strict 모드 필수
- 모든 API 호출 타입 안전성
- 커밋당 파일 ≤5개
- 린트 에러 0개

### 성공 기준
- [ ] 백엔드 API 15개 엔드포인트 100% 연동
- [ ] TypeScript strict 모드 빌드 성공
- [ ] 7개 핵심 페이지 동작
- [ ] 모바일/태블릿/데스크톱 반응형

---

## 🛠️ 기술 스택 (2025-10-05 웹서치 검증 완료)

### Core
- **Framework**: Next.js 14.2.0 (App Router)
- **Language**: TypeScript 5.3.0 (strict: true)
- **Styling**: Tailwind CSS 3.4.0
- **UI Library**: shadcn/ui (latest)

### State & Data
- **Server State**: @tanstack/react-query 5.0.0
- **Client State**: Zustand 4.5.0
- **Forms**: react-hook-form 7.50.0 + zod 3.22.0
- **HTTP Client**: axios 1.6.0

### Tooling
- **AI Code Gen**: v0.dev, Cursor
- **Icons**: lucide-react 0.300.0
- **Charts**: recharts 2.10.0
- **Toast**: sonner 1.3.0

---

## 📁 디렉터리 구조 (최종)

```
apps/frontend/
├── app/
│   ├── (dashboard)/              # Dashboard 레이아웃 그룹
│   │   ├── layout.tsx           # 공통 Sidebar + Header
│   │   ├── page.tsx             # Dashboard 홈
│   │   ├── search/
│   │   │   └── page.tsx         # 하이브리드 검색
│   │   ├── documents/
│   │   │   └── page.tsx         # 문서 관리
│   │   ├── taxonomy/
│   │   │   └── page.tsx         # 분류체계
│   │   ├── agents/
│   │   │   └── page.tsx         # 에이전트 관리
│   │   ├── pipeline/
│   │   │   └── page.tsx         # RAG 파이프라인
│   │   └── monitoring/
│   │       └── page.tsx         # 시스템 모니터링
│   ├── layout.tsx                # Root 레이아웃
│   ├── globals.css
│   └── providers.tsx             # React Query, Theme
├── components/
│   ├── ui/                       # shadcn/ui 컴포넌트 (자동 생성)
│   ├── search/
│   │   ├── SearchBar.tsx
│   │   ├── SearchResults.tsx
│   │   ├── SearchFilters.tsx
│   │   └── HighlightText.tsx
│   ├── documents/
│   │   ├── FileUpload.tsx
│   │   ├── DocumentList.tsx
│   │   └── DocumentPreview.tsx
│   ├── taxonomy/
│   │   ├── TaxonomyTree.tsx
│   │   ├── CategoryBadge.tsx
│   │   └── VersionSelector.tsx
│   ├── agents/
│   │   ├── AgentCard.tsx
│   │   ├── AgentForm.tsx
│   │   └── AgentStatus.tsx
│   ├── monitoring/
│   │   ├── MetricsChart.tsx
│   │   ├── HealthStatus.tsx
│   │   └── AlertBanner.tsx
│   └── layout/
│       ├── AppShell.tsx
│       ├── Sidebar.tsx
│       ├── Header.tsx
│       └── Breadcrumb.tsx
├── lib/
│   ├── api/
│   │   ├── client.ts             # Axios instance + interceptors
│   │   ├── types.ts              # API 타입 정의 (Zod schemas)
│   │   ├── search.ts
│   │   ├── classification.ts
│   │   ├── taxonomy.ts
│   │   ├── agents.ts
│   │   ├── pipeline.ts
│   │   ├── monitoring.ts
│   │   └── ingestion.ts
│   ├── store/
│   │   └── useStore.ts           # Zustand global state
│   ├── env.ts                    # 환경 변수 검증 (Zod)
│   └── utils.ts                  # cn(), formatDate() 등
├── hooks/
│   ├── useSearch.ts
│   ├── useTaxonomy.ts
│   ├── useAgents.ts
│   └── useToast.ts
├── .env.local
├── .env.example
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── components.json               # shadcn/ui 설정
├── package.json
└── README.md
```

---

## 🚀 Phase별 상세 계획

## Phase 0: 준비 및 검증 (1일)

### 0.1 Scope 작성
**목적**: Phase 0에서 정확히 무엇을 완료할지 명시

**결과물**:
- [ ] 프로젝트 생성 명령어 (정확한 버전)
- [ ] 환경 변수 목록 (FRONTEND_IG_CHECKLIST.md 참조)
- [ ] 디렉터리 구조 확정

### 0.2 Context Load (코드 직접 읽기)
- [ ] `apps/api/config.py` 읽기 → 환경 변수 전체 목록 확보
- [ ] `apps/api/routers/search_router.py` 읽기 → SearchResponse 타입 확정
- [ ] `apps/api/routers/classification_router.py` 읽기
- [ ] `apps/api/models/common_models.py` 읽기 (있다면)

**IG 임계치 체크**:
- [ ] API 응답 스키마 100% 확정?
- [ ] 환경 변수 전체 목록 확정?
- [ ] 인증 방식 결정 완료?
- **No라면 → Abstain, 정보 수집 후 재개**

### 0.3 Synthesis (Context Sheet 작성)
**파일**: `PHASE0_CONTEXT_SHEET.md` 생성

내용:
```markdown
## 입력 (확정된 사실)
- API 엔드포인트: 15개 (FRONTEND_CONTEXT.md)
- 응답 타입: [각 엔드포인트별 Zod 스키마]
- 환경 변수: [apps/api/config.py에서 읽은 목록]

## 출력 (생성할 파일)
1. apps/frontend/package.json (정확한 버전)
2. apps/frontend/tsconfig.json (strict: true)
3. apps/frontend/.env.example
4. apps/frontend/next.config.js
5. apps/frontend/lib/env.ts (Zod 검증)

## 제약 조건
- 파일 5개 이하
- 모호어 0개
- TypeScript 에러 0개

## IG 부족 항목
- [있다면 명시]
```

### 0.4 Plan (≤5파일)
**커밋 1**: 프로젝트 초기화

파일:
1. `apps/frontend/package.json`
2. `apps/frontend/tsconfig.json`
3. `apps/frontend/next.config.js`
4. `apps/frontend/.env.example`
5. `apps/frontend/tailwind.config.ts`

### 0.5 Explain (알고리즘 10줄)
```
1. npx create-next-app@14.2.0 apps/frontend --typescript --tailwind --app
2. tsconfig.json에 strict: true 추가
3. next.config.js에 API proxy 설정 (http://localhost:8000)
4. .env.example에 NEXT_PUBLIC_API_URL 추가
5. Tailwind 다크모드 활성화 (class strategy)
6. 린트 규칙 엄격화 (eslint-config-next)
7. Git에 .env.local 제외 (.gitignore 확인)
8. npm install 실행
9. npm run dev 테스트 (포트 3000)
10. 빌드 성공 확인 (npm run build)
```

**승인 필요**: 이 10줄 검토 후 구현 시작

### 0.6 Implement
```bash
# 1. 기존 frontend-admin 완전 삭제
rm -rf apps/frontend-admin

# 2. Next.js 14 프로젝트 생성
npx create-next-app@14.2.0 apps/frontend \
  --typescript \
  --tailwind \
  --app \
  --no-src-dir \
  --import-alias "@/*"

cd apps/frontend

# 3. package.json 수정 (정확한 버전)
# (Edit tool 사용)

# 4. 나머지 설정 파일들
# (Write tool 사용)
```

### 0.7 Verify
- [ ] `npm run lint` 성공 (에러 0개)
- [ ] `npm run build` 성공
- [ ] `npm run dev` 실행 → http://localhost:3000 접속
- [ ] Git status 확인 (변경 파일 ≤5개)

**DoD (Definition of Done)**:
- [ ] TypeScript 에러 0개
- [ ] 린트 에러 0개
- [ ] 빌드 성공
- [ ] 서버 실행 성공

---

## Phase 1: shadcn/ui 및 기본 레이아웃 (1일)

### 1.1 Scope
**목표**: shadcn/ui 설정 + AppShell + Sidebar + Header 구현

**결과물**:
- shadcn/ui 컴포넌트 10개 설치
- `components/layout/AppShell.tsx`
- `components/layout/Sidebar.tsx`
- `components/layout/Header.tsx`
- `app/(dashboard)/layout.tsx`

### 1.2 Context Load
- [ ] shadcn/ui 설치 가이드 읽기
- [ ] Next.js App Router 레이아웃 문서 읽기
- [ ] 7개 페이지 라우팅 경로 확정

### 1.3 IG 임계치 체크
- [ ] shadcn 설치 명령어 정확한가?
- [ ] 필요한 컴포넌트 목록 확정?
- [ ] 레이아웃 구조 명확한가?

### 1.4 Plan (≤5파일)
**커밋 2**: shadcn/ui 설정
1. `components.json` (shadcn 설정)
2. `components/ui/button.tsx` (자동 생성)
3. `components/ui/card.tsx`
4. `components/ui/badge.tsx`
5. `lib/utils.ts`

**커밋 3**: 레이아웃 구현
1. `components/layout/AppShell.tsx`
2. `components/layout/Sidebar.tsx`
3. `components/layout/Header.tsx`
4. `app/(dashboard)/layout.tsx`
5. `app/(dashboard)/page.tsx` (임시)

### 1.5 Explain
```
1. npx shadcn@latest init (default 설정)
2. npx shadcn@latest add button card badge input select
3. Sidebar: 7개 네비게이션 링크 (lucide-react 아이콘)
4. Header: 검색바 + 사용자 메뉴
5. AppShell: Sidebar(고정) + Main(스크롤)
6. (dashboard) 레이아웃 그룹으로 공통 레이아웃 공유
7. 다크모드 토글 (next-themes)
8. 반응형: 모바일은 Sidebar를 Sheet로
9. 모든 컴포넌트 TypeScript strict
10. 린트 통과
```

### 1.6 Implement
```bash
# shadcn 설치
npx shadcn@latest init

# 필수 컴포넌트
npx shadcn@latest add button card badge input select \
  dropdown-menu scroll-area separator sheet sidebar \
  tabs toast tooltip popover progress slider switch
```

### 1.7 Verify
- [ ] 레이아웃 렌더링 성공
- [ ] 7개 링크 클릭 동작 (404 정상)
- [ ] 다크모드 토글 동작
- [ ] 모바일 Sidebar Sheet 동작
- [ ] TypeScript/린트 0 에러

**DoD**:
- [ ] 모든 페이지 공통 레이아웃 적용
- [ ] 반응형 동작
- [ ] 접근성 (키보드 네비게이션)

---

## Phase 2: API 클라이언트 및 타입 (1일)

### 2.1 Scope
**목표**: Axios 클라이언트 + Zod 스키마 + React Query 설정

**결과물**:
- `lib/env.ts` (환경 변수 검증)
- `lib/api/client.ts` (Axios instance)
- `lib/api/types.ts` (모든 API 타입)
- `app/providers.tsx` (QueryClientProvider)

### 2.2 Context Load
- [ ] `apps/api/routers/*.py` 전체 읽기 → 응답 타입 추출
- [ ] openapi.yaml 읽기 → 요청/응답 스키마
- [ ] React Query 문서 읽기

### 2.3 IG 임계치 체크
- [ ] 15개 엔드포인트 응답 타입 100% 확정?
- [ ] 에러 응답 형식 확정?
- [ ] 환경 변수 전체 확정?

**미확정 시 → Abstain**

### 2.4 Plan (≤5파일)
**커밋 4**: 환경 변수 + Axios
1. `lib/env.ts`
2. `lib/api/client.ts`
3. `.env.local` (Git 제외)
4. `.env.example` 업데이트

**커밋 5**: API 타입 (1/3)
1. `lib/api/types.ts` (Search, Classify, Taxonomy)

**커밋 6**: API 타입 (2/3)
1. `lib/api/types.ts` 업데이트 (Agents, Pipeline, Monitoring)

**커밋 7**: API 타입 (3/3) + React Query
1. `lib/api/types.ts` 업데이트 (Ingestion, Embeddings, Evaluation)
2. `app/providers.tsx`
3. `app/layout.tsx` 업데이트 (Provider 추가)

### 2.5 Explain
```
1. Zod로 env 스키마 정의 (NEXT_PUBLIC_API_URL 필수)
2. Axios instance: baseURL, timeout 30s, interceptors
3. Request interceptor: Authorization 헤더 추가 (추후)
4. Response interceptor: 401 → 로그아웃, 에러 토스트
5. 각 엔드포인트별 Zod 스키마 정의
6. zod-to-ts로 TypeScript 타입 자동 생성
7. React Query: staleTime 5분, cacheTime 10분
8. onError global handler: toast 표시
9. devtools 활성화 (development only)
10. 모든 타입 strict 검증
```

### 2.6 Implement
(코드 작성)

### 2.7 Verify
- [ ] env.parse() 성공
- [ ] Axios instance 생성 성공
- [ ] 타입 Import 에러 없음
- [ ] React Query Devtools 보임

**DoD**:
- [ ] 모든 API 타입 정의 완료 (15개 엔드포인트)
- [ ] Zod 런타임 검증 동작
- [ ] TypeScript 타입 추론 정확

---

## Phase 3: 검색 페이지 (1일)

### 3.1 Scope
**목표**: 하이브리드 검색 UI 완전 동작

**결과물**:
- `app/(dashboard)/search/page.tsx`
- `components/search/SearchBar.tsx`
- `components/search/SearchResults.tsx`
- `components/search/SearchFilters.tsx`
- `lib/api/search.ts` (React Query hooks)
- `hooks/useSearch.ts`

### 3.2 Context Load
- [ ] `apps/api/routers/search_router.py` 정밀 읽기
- [ ] openapi.yaml search 섹션 읽기
- [ ] v0.dev 검색 UI 예제 생성

### 3.3 IG 임계치 체크
- [ ] SearchRequest 모든 필드 의미 이해?
- [ ] SearchResponse 정확한 구조 확인?
- [ ] 필터 옵션 (min_score, max_results) 범위 확정?

### 3.4 Plan (≤5파일)
**커밋 8**: v0.dev로 UI 생성
1. `components/search/SearchBar.tsx`
2. `components/search/SearchResults.tsx`
3. `components/search/SearchFilters.tsx`

**커밋 9**: API 연동
1. `lib/api/search.ts`
2. `hooks/useSearch.ts`
3. `app/(dashboard)/search/page.tsx`

### 3.5 Explain
```
1. SearchBar: debounced input (500ms), Enter 키 검색
2. SearchFilters: max_results slider (1-50), min_score (0-1)
3. taxonomy filter: Multi-select (나중에 구현)
4. SearchResults: Card 그리드 (3열 데스크톱, 1열 모바일)
5. 각 결과: 제목, 스니펫, 점수 badge, 출처
6. useSearch hook: useQuery + debounce
7. 로딩: Skeleton 3개 표시
8. 에러: Alert 컴포넌트로 표시
9. 빈 결과: "검색 결과 없음" 메시지
10. 무한 스크롤 (추후)
```

### 3.6 v0.dev 프롬프트
```
Create a hybrid search interface using Next.js 14 and shadcn/ui:

Components needed:
1. SearchBar with debounced input (lucide-react Search icon)
2. SearchFilters with sliders for max_results (1-50) and min_score (0-1)
3. SearchResults grid showing title, content snippet, score badge, source
4. Loading skeleton state
5. Error state with Alert component
6. Empty state

Requirements:
- TypeScript with strict types
- Tailwind CSS responsive (1 col mobile, 2 col tablet, 3 col desktop)
- shadcn/ui components: Input, Button, Card, Badge, Slider, Alert, Skeleton
- Dark mode support
- Accessible (ARIA labels, keyboard navigation)

Return complete code for all 3 components.
```

### 3.7 Implement
(v0.dev 결과 복사 + 수정)

### 3.8 Verify
- [ ] 검색어 입력 → API 호출 확인 (Network 탭)
- [ ] 결과 렌더링 확인
- [ ] 필터 변경 → 재검색
- [ ] 로딩/에러 상태 테스트
- [ ] 모바일 반응형

**DoD**:
- [ ] 실제 API 연동 동작
- [ ] 모든 필터 동작
- [ ] 에러 처리 완료
- [ ] 접근성 확인

---

## Phase 4: 문서 관리 페이지 (1일)

### 4.1 Scope
**목표**: 파일 업로드 + 문서 목록

**결과물**:
- `app/(dashboard)/documents/page.tsx`
- `components/documents/FileUpload.tsx`
- `components/documents/DocumentList.tsx`
- `lib/api/ingestion.ts`
- `hooks/useDocuments.ts`

### 4.2 Context Load
- [ ] `apps/api/routers/ingestion.py` 읽기
- [ ] 파일 업로드 엔드포인트 확인
- [ ] 작업 상태 확인 방법

### 4.3 Plan (≤5파일)
**커밋 10**: 파일 업로드 UI
1. `components/documents/FileUpload.tsx` (v0.dev)
2. `components/documents/DocumentList.tsx`

**커밋 11**: API 연동
1. `lib/api/ingestion.ts`
2. `hooks/useDocuments.ts`
3. `app/(dashboard)/documents/page.tsx`

### 4.4 v0.dev 프롬프트
```
Create a file upload component with Next.js 14 and shadcn/ui:

Features:
- Drag and drop zone with dashed border
- Multiple file selection
- Progress bars for each file
- File list with remove buttons
- Status badges (pending, uploading, success, error)
- Accept: .txt, .pdf, .docx, .md
- Size limit: 10MB per file
- TypeScript strict

Components: Card, Button, Progress, Badge, Alert
Use lucide-react icons: Upload, FileText, X, Check, AlertCircle

Return complete working component.
```

### 4.5 Verify
- [ ] 파일 선택 동작
- [ ] 업로드 진행률 표시
- [ ] 성공/실패 처리
- [ ] 목록 새로고침

**DoD**:
- [ ] 실제 업로드 동작
- [ ] 에러 처리
- [ ] UX 부드러움

---

## Phase 5: 나머지 페이지 (2일)

### 5.1 Dashboard 페이지
- 시스템 상태 카드 4개
- 최근 활동 목록
- 차트 (Recharts)

### 5.2 Taxonomy 페이지
- 트리 뷰어 (v0.dev)
- 버전 선택
- 확장/축소

### 5.3 Agents 페이지
- 에이전트 카드 그리드
- 생성 폼
- 활성화/비활성화

### 5.4 Pipeline 페이지
- 파이프라인 실행 UI
- 단계별 진행 표시
- 결과 표시

### 5.5 Monitoring 페이지
- 메트릭 차트
- 헬스 체크 상태
- 알림 목록

---

## Phase 6: 폴리싱 및 프로덕션 준비 (1일)

### 6.1 에러 바운더리
- `app/error.tsx`
- `app/not-found.tsx`

### 6.2 로딩 상태
- `app/loading.tsx`
- Skeleton 컴포넌트

### 6.3 Toast 시스템
- sonner 설정
- 전역 에러 toast

### 6.4 환경 변수 검증
- Zod 스키마 강화
- 빌드 시 검증

### 6.5 성능 최적화
- 번들 사이즈 확인
- 이미지 최적화
- 코드 스플리팅

### 6.6 배포 준비
- Vercel 설정
- 환경 변수 설정
- 도메인 연결 (선택)

---

## 📊 전체 타임라인

```
Day 1: Phase 0 (프로젝트 초기화) + Phase 1 (레이아웃)
Day 2: Phase 2 (API 클라이언트/타입)
Day 3: Phase 3 (검색 페이지)
Day 4: Phase 4 (문서 관리)
Day 5-6: Phase 5 (나머지 페이지)
Day 7: Phase 6 (폴리싱)
```

**총 예상 기간**: 7일

---

## 🚨 리스크 및 대응

### 리스크 1: API 응답 타입 불일치
**대응**: Zod 런타임 검증으로 즉시 탐지

### 리스크 2: v0.dev 생성 코드 품질
**대응**: 생성 후 즉시 린트 + TypeScript 검증

### 리스크 3: 컨텍스트 윈도우 초과
**대응**: Phase별로 새 세션 시작 가능하도록 문서화

### 리스크 4: IG 임계치 미달
**대응**: 각 Phase 시작 전 체크리스트 100% 완료 강제

---

## ✅ 각 Phase DoD (공통)

모든 Phase는 아래 조건 충족 시에만 완료:

- [ ] TypeScript strict 모드 에러 0개
- [ ] ESLint 에러 0개
- [ ] 커밋당 파일 ≤5개
- [ ] 모든 함수/컴포넌트 타입 정의
- [ ] 에러 처리 완료
- [ ] 로딩 상태 구현
- [ ] 반응형 동작 확인
- [ ] 접근성 기본 (ARIA, 키보드)
- [ ] 다크모드 지원
- [ ] Git 커밋 메시지 명확

---

## 📝 PR 체크리스트 (최종)

프로덕션 배포 전 확인:

- [ ] 모든 Phase DoD 완료
- [ ] 백엔드 API 15개 엔드포인트 100% 테스트
- [ ] 7개 페이지 모두 동작
- [ ] 모바일/태블릿/데스크톱 반응형
- [ ] 다크모드 완벽 동작
- [ ] TypeScript strict: true 빌드 성공
- [ ] 번들 사이즈 ≤500KB (First Load JS)
- [ ] Lighthouse 점수: Performance ≥90
- [ ] 접근성: WCAG 2.1 AA 준수
- [ ] 환경 변수 .env.example 최신화
- [ ] README.md 실행 가이드 완성

---

**문서 끝**

이 계획은 바이브코딩 7-Stage 루프를 준수합니다.
각 Phase는 IG 임계치 체크 후에만 진행 가능합니다.
