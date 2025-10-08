# FRONTEND_IG_CHECKLIST.md
# 정보이득(IG) 임계치 검증 체크리스트

> **⚠️ 이 체크리스트는 각 Phase 시작 전 필수**
>
> **원칙**:
> - 모든 항목이 ✅ 상태여야 구현 시작 가능
> - 하나라도 ❌이면 **Abstain (보류)**
> - "아마도", "아마", "일반적으로" 등 모호어 발견 시 즉시 중단
>
> **참조**: `바이브코딩_완성_정제본_쉬운말로_연결한_한_권.md` 섹션 1-2

---

## 🔍 Phase 0: 프로젝트 초기화 IG 체크

### 1) 시작 전 공통 (IG 임계치)

- [ ] **Scope 문서화**: Phase 0에서 정확히 무엇을 만드는가?
  - 파일명: [ 5개 정확히 명시 ]
  - 결과물: [ 구체적 설명 ]
  - 비범위: [ 하지 않는 것 명시 ]

- [ ] **모호어 제거 완료**
  - [ ] "기본 설정" → [ 구체적 설정값으로 변환 ]
  - [ ] "적절한 구조" → [ 정확한 디렉터리 경로 ]
  - [ ] "일반적인 방법" → [ 구체적 명령어/코드 ]

- [ ] **입력(맥락) ≥ 출력(생성)×20 확인**
  - 입력: [ FRONTEND_CONTEXT.md 읽음 ]
  - 출력: [ package.json, tsconfig.json 등 5개 파일 ]
  - 비율: [ 충분한가? ]

- [ ] **SOT=코드 원칙**
  - [ ] 문서보다 코드 우선 확인
  - [ ] 주석 3줄 이상 금지

### 2) 컨텍스트 로딩

- [ ] **Main vs Reference 분리**
  - Main: `apps/frontend/` (우리가 구현)
  - Reference: `apps/api/` (인터페이스만 읽기)

- [ ] **Reference 읽기 완료** (인터페이스만)
  - [ ] `apps/api/main.py` (✅ 읽음)
  - [ ] `apps/api/config.py` (🔴 미읽음 → **읽기 필요**)
  - [ ] `openapi.yaml` (✅ 일부 읽음)

- [ ] **파일/함수/경로 정확히 지정**
  - [ ] Next.js 설치: `npx create-next-app@14.2.0` (버전 명시)
  - [ ] 디렉터리: `apps/frontend` (정확한 경로)
  - [ ] 설정 파일: 5개 (파일명 모두 명시)

- [ ] **위험 신호 없음**
  - [ ] 모호어 0개
  - [ ] 장황 설명 없음
  - [ ] 3줄 이상 주석 없음

### 3) Phase 0 전용 IG 검증

- [ ] **Next.js 14.2.0 설치 명령어 정확한가?**
  - 명령어: [ 정확한 버전과 플래그 명시 ]
  - 예상 결과: [ 생성될 파일 목록 ]

- [ ] **TypeScript strict 모드 설정 방법 확인?**
  - 파일: `tsconfig.json`
  - 설정: `"strict": true` (정확한 위치)

- [ ] **환경 변수 전체 목록 확정?**
  - [ ] `NEXT_PUBLIC_API_URL` (필수)
  - [ ] `NEXT_PUBLIC_API_TIMEOUT` (선택, 기본값: 30000)
  - [ ] `NODE_ENV` (자동)
  - 🔴 **미확정 항목**: [ apps/api/config.py 미읽음 ]

- [ ] **Tailwind 설정 정확한가?**
  - 다크모드: `class` strategy
  - 색상: [ 기본값 vs 커스텀? ]

### IG 부족 항목 (Abstain 필요)

```
🔴 apps/api/config.py 미읽음
   → 추가 환경 변수 있을 가능성
   → Phase 0.2에서 읽기

🔴 API 인증 방식 미확정
   → JWT? API Key? 없음?
   → ABSTAIN.md 참조
```

---

## 🔍 Phase 1: shadcn/ui 및 레이아웃 IG 체크

### 1) Scope 확정

- [ ] **목표 명확**
  - [ ] shadcn/ui 설정 (정확히 무슨 파일?)
  - [ ] 컴포넌트 10개 설치 (목록 명시)
  - [ ] 레이아웃 3개 (AppShell, Sidebar, Header)

### 2) Context Load

- [ ] **shadcn/ui 공식 문서 읽음**
  - [ ] 설치 방법
  - [ ] components.json 구조
  - [ ] 필요한 컴포넌트 목록

- [ ] **Next.js App Router 레이아웃 읽음**
  - [ ] 레이아웃 그룹 `(dashboard)` 이해
  - [ ] `layout.tsx` vs `page.tsx` 차이

### 3) IG 검증

- [ ] **설치할 컴포넌트 정확한 이름?**
  ```
  button, card, badge, input, select,
  dropdown-menu, scroll-area, separator, sheet, sidebar
  ```
  (10개 정확)

- [ ] **Sidebar 네비게이션 링크 7개 확정?**
  - [ ] `/` - Dashboard
  - [ ] `/search` - 검색
  - [ ] `/documents` - 문서
  - [ ] `/taxonomy` - 분류체계
  - [ ] `/agents` - 에이전트
  - [ ] `/pipeline` - 파이프라인
  - [ ] `/monitoring` - 모니터링

- [ ] **반응형 구조 명확?**
  - 데스크톱: Sidebar 고정
  - 모바일: Sheet로 전환
  - 브레이크포인트: `md` (768px)

### IG 부족 항목

```
✅ 모두 확정됨 (v0.dev 프롬프트 준비 완료)
```

---

## 🔍 Phase 2: API 클라이언트/타입 IG 체크

### 1) Scope 확정

- [ ] **생성할 파일 정확**
  - `lib/env.ts` (환경 변수 검증)
  - `lib/api/client.ts` (Axios)
  - `lib/api/types.ts` (15개 엔드포인트 타입)
  - `app/providers.tsx` (React Query)

### 2) Context Load (매우 중요)

- [ ] **각 라우터 파일 직접 읽기**
  - [ ] `apps/api/routers/search_router.py` (🔴 미읽음)
  - [ ] `apps/api/routers/classification_router.py` (🔴 미읽음)
  - [ ] `apps/api/routers/taxonomy_router.py` (🔴 미읽음)
  - [ ] `apps/api/routers/orchestration_router.py` (🔴 미읽음)
  - [ ] `apps/api/routers/agent_factory_router.py` (🔴 미읽음)
  - [ ] 나머지 10개 라우터 (🔴 미읽음)

- [ ] **openapi.yaml 전체 읽기**
  - [ ] Request schemas
  - [ ] Response schemas
  - [ ] Error schemas

### 3) IG 검증 (가장 엄격)

- [ ] **SearchResponse 정확한 타입?**
  ```typescript
  interface SearchResponse {
    hits: SearchHit[]           // ✅ 확정
    total_hits: number          // ✅ 확정
    search_time_ms: number      // ✅ 확정
    mode: string                // ✅ 확정
  }

  interface SearchHit {
    id: string                  // ✅ 확정
    title: string               // ✅ 확정
    content: string             // ✅ 확정
    score: number               // ✅ 확정
    source: string              // ✅ 확정
    metadata?: {                // 🔴 정확한 타입 미확정
      bm25_score?: number
      vector_score?: number
      [key: string]: any?       // 추가 필드 있을 수 있음
    }
  }
  ```

- [ ] **ClassifyResponse 정확한 타입?**
  - 🔴 **미확정** (apps/api/routers/classification_router.py 읽어야 함)

- [ ] **에러 응답 형식?**
  ```typescript
  // main.py:314-325에서 확인
  interface ErrorResponse {
    type: string      // ✅ 확정
    title: string     // ✅ 확정
    status: number    // ✅ 확정
    detail: string    // ✅ 확정
    instance: string  // ✅ 확정
    timestamp: number // ✅ 확정
  }
  ```

- [ ] **Axios 인증 헤더?**
  - 🔴 **미확정** (Bearer token? API Key? X-API-Key?)

### IG 부족 항목 (Critical)

```
🔴 모든 라우터 파일 미읽음 (15개)
   → Phase 2 시작 전 필수 읽기
   → ABSTAIN.md에 명시

🔴 인증 방식 미확정
   → apps/api/middleware/ 확인 필요
   → 또는 ABSTAIN

🔴 각 엔드포인트 응답 구조 추측 금지
   → 반드시 코드 읽고 확정
```

---

## 🔍 Phase 3: 검색 페이지 IG 체크

### 1) Scope

- [ ] **파일 6개 정확히 명시**
  - `app/(dashboard)/search/page.tsx`
  - `components/search/SearchBar.tsx`
  - `components/search/SearchResults.tsx`
  - `components/search/SearchFilters.tsx`
  - `lib/api/search.ts`
  - `hooks/useSearch.ts`

### 2) Context Load

- [ ] **apps/api/routers/search_router.py 정밀 읽기**
  - [ ] 모든 라우트 확인
  - [ ] 요청 파라미터 확인
  - [ ] 응답 구조 확인
  - [ ] 에러 케이스 확인

- [ ] **openapi.yaml search 섹션 전체 읽기**
  - [ ] SearchRequest 스키마 (67-89줄 읽음)
  - [ ] SearchResponse 스키마
  - [ ] 예제 확인

### 3) IG 검증

- [ ] **SearchRequest 모든 필드 의미 이해**
  - `q`: string (검색어)
  - `max_results`: number (1-50? 범위 확정 필요)
  - `canonical_in`: array of arrays (정확한 구조?)
  - `min_score`: float (0.0-1.0 범위 확정)
  - `include_highlights`: boolean (무슨 기능?)
  - `search_mode`: "hybrid" | "bm25" | "vector" (3개만?)

- [ ] **Debounce 시간 정확히?**
  - 500ms? 300ms? (결정 필요)

- [ ] **max_results 범위?**
  - 최소: 1
  - 최대: 50? 100? (코드에서 확인)
  - 기본값: 10

- [ ] **min_score 범위?**
  - 최소: 0.0
  - 최대: 1.0
  - 기본값: 0.7 (코드 확인)

### IG 부족 항목

```
🔴 SearchRequest 필드별 정확한 의미/범위 미확정
   → apps/api/routers/search_router.py 읽기 필수

🔴 canonical_in 구조 불명확
   → 예: [["Tech", "AI"]] vs ["Tech/AI"]?

🔴 include_highlights 동작 방식
   → 응답에 어떤 필드 추가되는지?
```

---

## 🔍 Phase 4-6 IG 체크 (간략)

### Phase 4: 문서 관리

- [ ] **FileUpload 허용 확장자**
  - .txt, .pdf, .docx, .md (확정)
  - 최대 크기: 10MB (코드 확인 필요)

- [ ] **업로드 엔드포인트**
  - `POST /ingestion/upload` (✅ 확정)
  - multipart/form-data
  - 응답 구조? (🔴 미확정)

### Phase 5: 나머지 페이지

- [ ] **각 페이지별 API 엔드포인트 확정**
  - Taxonomy: GET /api/v1/taxonomy/{version}/tree
  - Agents: POST /api/v1/agents/from-category
  - Pipeline: POST /api/v1/pipeline/execute
  - Monitoring: GET /api/v1/monitoring/health

- [ ] **응답 타입 모두 확정?**
  - 🔴 **미확정** (각 라우터 읽어야 함)

### Phase 6: 폴리싱

- [ ] **Vercel 배포 설정**
  - vercel.json 필요?
  - 환경 변수 설정 방법?
  - 도메인 연결?

---

## 📊 전체 IG 상태 요약

### ✅ 확정된 항목 (구현 가능)

1. **백엔드 API 엔드포인트 15개** (main.py에서 읽음)
2. **프로젝트 구조** (디렉터리, 파일명)
3. **기술 스택** (Next.js 14, shadcn/ui 등)
4. **에러 응답 형식** (RFC 7807)
5. **CORS 미들웨어 존재** (설정값 미확정)

### 🔴 미확정 항목 (Abstain 필요)

1. **각 API 엔드포인트 응답 상세 스키마** (15개 라우터 미읽음)
2. **환경 변수 전체 목록** (apps/api/config.py 미읽음)
3. **인증/권한 시스템** (구현 여부, 방식)
4. **파일 업로드 응답 구조**
5. **SearchRequest 필드별 정확한 범위/의미**
6. **canonical_in 정확한 구조**
7. **데이터베이스 스키마**
8. **Rate limiting 정확한 제한값**

---

## 🚨 Abstain 조건 (진행 불가)

다음 조건 중 하나라도 해당하면 **즉시 중단**:

1. **모호어 발견**
   - "적절히", "일반적으로", "아마도"
   - "기본", "보통", "대략"

2. **IG 임계치 미달**
   - 필수 항목 중 하나라도 🔴 상태
   - 타입 정의에 `any` 사용 고려
   - 응답 구조 추측 필요

3. **코드 미확인**
   - 라우터 파일 읽지 않음
   - openapi.yaml 미확인
   - 환경 변수 추측

4. **위험 신호**
   - 3줄 이상 주석
   - 장황한 설명
   - 여러 해석 가능한 문장

---

## ✅ 진행 가능 조건

모든 Phase는 다음 조건 충족 시에만 시작:

1. **Scope 100% 명확**
   - 파일명 정확
   - 결과물 구체적
   - 비범위 명시

2. **Context Load 완료**
   - 필요한 코드 모두 읽음
   - 타입 정의 확정
   - 예제 확인

3. **IG 체크리스트 100% ✅**
   - 모호어 0개
   - 추측 항목 0개
   - 모든 값 확정

4. **Plan ≤5파일**
   - 커밋당 파일 수 확정
   - 순서 명확
   - DoD 정의

---

**문서 끝**

이 체크리스트는 바이브코딩 원칙을 강제합니다.
하나라도 미달 시 ABSTAIN.md 참조하여 정보 수집 후 재개하세요.
