# DT-RAG Frontend

Next.js 14 기반 RAG 시스템 관리자 대시보드

## 기술 스택

- **Framework**: Next.js 14.2.33 (App Router)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS 3.4.0
- **UI Library**: shadcn/ui
- **State Management**: @tanstack/react-query 5.0.0
- **HTTP Client**: Axios 1.12.2
- **Validation**: Zod 4.1.11
- **Icons**: lucide-react

## 시작하기

### 환경 변수 설정

`.env.local` 파일 생성:

```bash
cp .env.example .env.local
```

필수 환경 변수:
- `NEXT_PUBLIC_API_URL`: 백엔드 API URL (기본값: http://localhost:8000)
- `NEXT_PUBLIC_API_TIMEOUT`: API 타임아웃 (기본값: 30000ms)

### 개발 서버 실행

```bash
npm install
npm run dev
```

http://localhost:3000 접속

### 프로덕션 빌드

```bash
npm run build
npm start
```

## 주요 기능

### 7개 페이지
1. **Dashboard** - 시스템 상태 개요
2. **Search** - 하이브리드 검색 (BM25 + Vector)
3. **Documents** - 문서 업로드 및 관리
4. **Taxonomy** - 분류 체계 트리
5. **Agents** - AI 에이전트 관리
6. **Pipeline** - RAG 파이프라인 실행
7. **Monitoring** - 시스템 헬스 체크

### API 연동 (15개 엔드포인트)
- ✅ Search (POST /search/)
- ✅ Classify (POST /classify/)
- ✅ Taxonomy (GET /taxonomy/{version}/tree)
- ✅ Document Upload (POST /ingestion/upload)
- ✅ Health Check (GET /monitoring/health)
- ✅ Pipeline Execute (POST /api/v1/pipeline/execute)
- ✅ Agent Management (POST /api/v1/agents/*)
- ✅ Embedding (POST /api/v1/embeddings/generate)
- ✅ Evaluation (POST /api/v1/evaluation/evaluate)
- ✅ Batch Search (POST /api/v1/batch/search)

## 프로젝트 구조

```
apps/frontend/
├── app/
│   ├── (dashboard)/          # 대시보드 레이아웃 그룹
│   │   ├── layout.tsx       # 공통 레이아웃 (Sidebar + Header)
│   │   ├── page.tsx         # Dashboard 홈
│   │   ├── search/          # 검색 페이지
│   │   ├── documents/       # 문서 관리
│   │   ├── taxonomy/        # 분류 체계
│   │   ├── agents/          # 에이전트
│   │   ├── pipeline/        # 파이프라인
│   │   └── monitoring/      # 모니터링
│   ├── error.tsx            # 에러 바운더리
│   ├── not-found.tsx        # 404 페이지
│   ├── loading.tsx          # 로딩 상태
│   └── layout.tsx           # Root 레이아웃
├── components/
│   ├── ui/                  # shadcn/ui 컴포넌트
│   └── layout/              # 레이아웃 컴포넌트
├── lib/
│   ├── api/                 # API 클라이언트
│   │   ├── client.ts       # Axios 인스턴스
│   │   ├── types.ts        # Zod 스키마
│   │   └── index.ts        # API 함수
│   ├── env.ts              # 환경 변수 검증
│   └── utils.ts            # 유틸리티
└── .env.example            # 환경 변수 예제
```

## 개발 가이드

### 코드 스타일
- ESLint 규칙 준수
- TypeScript strict mode
- 모든 API는 Zod로 런타임 검증

### 새 페이지 추가
1. `app/(dashboard)/[페이지명]/page.tsx` 생성
2. `components/layout/Sidebar.tsx`에 네비게이션 추가
3. API 타입이 필요하면 `lib/api/types.ts`에 Zod 스키마 추가

### 새 API 추가
1. `lib/api/types.ts`에 Request/Response 스키마 정의
2. `lib/api/index.ts`에 API 함수 구현
3. React Query hooks로 사용

## 배포

### Vercel (권장)
```bash
vercel
```

### 환경 변수 설정
Vercel 대시보드에서 설정:
- `NEXT_PUBLIC_API_URL`: 프로덕션 API URL

## 성능

- First Load JS: 87.3~143 kB
- 모든 페이지 Static Pre-render
- Dark mode 지원
- 반응형 디자인

## 라이선스

Private
