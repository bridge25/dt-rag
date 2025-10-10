---
id: API-INTEGRATION-001
version: 0.1.0
status: draft
created: 2025-10-11
updated: 2025-10-11
author: @username
priority: critical
category: bugfix
labels:
  - api
  - frontend
  - integration
  - performance
scope:
  packages:
    - apps/frontend/lib/api
  files:
    - apps/frontend/lib/api/index.ts
    - apps/frontend/lib/api/client.ts
---

# @SPEC:API-INTEGRATION-001: Frontend-Backend API 통합 개선

## HISTORY

### v0.1.0 (2025-10-11)
- **INITIAL**: Frontend-Backend API 통합 개선 명세 최초 작성
- **AUTHOR**: @username
- **SCOPE**: Trailing slash 불일치 해결, 하드코딩 URL 제거, CORS 설정 검증
- **CONTEXT**: 307 Temporary Redirect로 인한 성능 저하 및 환경 설정 유연성 개선 필요
- **IMPACT**: API 응답 시간 개선, 환경 간 이식성 향상

---

## Environment (환경)

### 현재 시스템 구성

#### Frontend (Next.js Application)
- **프레임워크**: Next.js with TypeScript
- **HTTP 클라이언트**: axios (apiClient)
- **환경 설정**:
  - `NEXT_PUBLIC_API_URL`: `http://localhost:8000/api/v1` (default)
  - `NEXT_PUBLIC_API_TIMEOUT`: 30000ms
  - baseURL: env.ts에서 중앙 관리
- **API 클라이언트**: `apps/frontend/lib/api/client.ts`에서 axios 인스턴스 생성

#### Backend (FastAPI Application)
- **프레임워크**: FastAPI v0.104+
- **포트**: 8000 (개발 환경)
- **API 버전**: v1
- **라우터 설정**:
  - Trailing slash: 일부 경로에서 명시적으로 설정됨
  - 자동 리다이렉트: 307 Temporary Redirect 발생 중

#### 개발 환경 구성
- **Frontend 서버**: `http://localhost:3000`
- **Backend 서버**: `http://localhost:8000`
- **API 베이스 경로**: `/api/v1`
- **CORS 설정**: `apps/api/config.py`에서 관리
  - Development Origins: `["http://localhost:3000", "http://localhost:3001", ...]`
  - Allow Credentials: `true`
  - Allow Methods: `["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]`

### 발견된 문제점

#### 1. Trailing Slash 불일치
- **현상**: Frontend에서 `/search/`, `/classify/`, `/batch-search/`로 호출
- **Backend 동작**: 일부 FastAPI 라우터가 trailing slash 없이 정의됨
- **결과**: 307 Temporary Redirect 발생 → 성능 저하

#### 2. 하드코딩된 URL
- **위치**: `apps/frontend/lib/api/index.ts`
  - Line 68: `http://localhost:8000/ingestion/upload` (uploadDocument)
  - Line 75: `http://localhost:8000/health` (getHealth)
- **문제점**:
  - 환경 변수 무시 (baseURL 미사용)
  - 프로덕션/스테이징 환경에서 동작 불가
  - 포트 변경 시 수동 수정 필요

#### 3. apiClient 중복 설정
- **getSystemHealth** (Line 80): baseURL 사용 (올바름)
- **getHealth** (Line 75): 하드코딩 URL 사용 (문제)
- **일관성 부족**: 같은 파일 내에서 다른 패턴 혼재

---

## Assumptions (가정)

### 기술적 가정

#### A1. CORS 설정 안정성
- **가정**: 현재 CORS 설정(`apps/api/config.py`)은 적절하게 구성되어 있음
- **근거**:
  - Development 환경에서 명시적 Origin 리스트 사용
  - Allow Credentials 활성화
  - 특정 헤더만 허용 (wildcard 미사용)
- **검증 필요**: 없음 (문서화만 수행)

#### A2. FastAPI 라우터 Trailing Slash 정책
- **가정**: FastAPI 라우터는 trailing slash를 엄격하게 구분함
- **근거**:
  - `/search/`와 `/search`는 다른 경로로 처리
  - 자동 리다이렉트 발생 시 307 상태 코드 반환
- **검증 완료**: Network 탭에서 307 Redirect 확인됨

#### A3. 환경 변수 우선순위
- **가정**: `NEXT_PUBLIC_API_URL`이 정의되면 모든 API 호출에서 baseURL로 사용되어야 함
- **근거**: `apps/frontend/lib/env.ts`의 Zod 스키마로 환경 변수 검증
- **현재 위반**: uploadDocument, getHealth 함수에서 무시됨

#### A4. API 응답 속도 기대치
- **가정**: 307 Redirect 제거 시 네트워크 왕복 시간(RTT) 감소
- **예상 효과**: 1 RTT 감소 (최소 수십 ms 개선)

### 비즈니스 가정

#### B1. 환경 이식성 요구사항
- **가정**: Frontend 애플리케이션은 환경 변수 변경만으로 다른 환경(dev/staging/prod)에서 동작해야 함
- **현재 상태**: 하드코딩된 URL로 인해 불가능
- **목표**: .env 파일 변경만으로 배포 가능

#### B2. 유지보수성 우선순위
- **가정**: 코드 일관성과 DRY 원칙이 중요함
- **근거**: 같은 파일 내에서 baseURL 사용/미사용 패턴이 혼재하면 유지보수 비용 증가

---

## Requirements (요구사항)

### Ubiquitous Requirements (필수 기능)

#### REQ-1: URL 구조 일관성
시스템은 모든 API 호출에서 일관된 URL 구조를 제공해야 한다.

**상세**:
- 모든 API 엔드포인트는 trailing slash 정책을 통일해야 함
- Backend 라우터 정의와 Frontend 호출이 정확히 일치해야 함

#### REQ-2: 환경 변수 기반 설정
시스템은 `NEXT_PUBLIC_API_URL` 환경 변수를 모든 API 호출에 사용해야 한다.

**상세**:
- 하드코딩된 `http://localhost:8000` 제거
- apiClient의 baseURL 속성 활용
- 상대 경로 또는 baseURL 기반 절대 경로만 사용

### Event-driven Requirements (이벤트 기반)

#### REQ-3: 리다이렉트 제거
WHEN 사용자가 search API를 호출하면, 시스템은 307 Redirect 없이 직접 응답해야 한다.

**상세**:
- `/search/` → `/search` 변경
- `/classify/` → `/classify` 변경
- `/batch-search/` → `/batch-search` 변경
- Network 탭에서 307 상태 코드 미발생 확인

#### REQ-4: 환경별 baseURL 적용
WHEN uploadDocument 함수가 호출되면, 시스템은 환경 변수 baseURL을 사용하여 요청을 전송해야 한다.

**상세**:
- `http://localhost:8000/ingestion/upload` → `/ingestion/upload`
- `http://localhost:8000/health` → `/health`
- apiClient의 baseURL과 상대 경로 조합으로 최종 URL 구성

### State-driven Requirements (상태 기반)

#### REQ-5: 개발/프로덕션 환경 분리
WHILE 애플리케이션이 프로덕션 환경에서 실행될 때, 시스템은 프로덕션 API URL을 자동으로 사용해야 한다.

**상세**:
- `.env.production` 파일의 `NEXT_PUBLIC_API_URL` 사용
- 코드 수정 없이 환경 변수 변경만으로 배포 가능

### Constraints (제약사항)

#### CON-1: FastAPI 라우터 호환성
IF API 경로가 변경되면, 시스템은 FastAPI 라우터의 trailing slash 정책을 준수해야 한다.

**상세**:
- Backend 라우터가 `/search`로 정의되면 Frontend도 `/search` 사용
- Backend 코드 수정 불필요 (Frontend만 변경)

#### CON-2: 기존 동작 보존
IF 환경 변수가 정의되지 않으면, 시스템은 기본값(`http://localhost:8000/api/v1`)을 사용해야 한다.

**상세**:
- `apps/frontend/lib/env.ts`의 default 값 유지
- 로컬 개발 환경에서 .env 파일 없이도 동작

---

## Specifications (상세 명세)

### SPEC-1: Trailing Slash 제거

#### 대상 파일
`apps/frontend/lib/api/index.ts`

#### 변경 사항

##### 1.1 search 함수 (Line 52)
```typescript
// Before
const response = await apiClient.post("/search/", validated)

// After
const response = await apiClient.post("/search", validated)
```

**태그**: @CODE:API-INTEGRATION-001:TRAILING-SLASH-SEARCH

##### 1.2 classify 함수 (Line 58)
```typescript
// Before
const response = await apiClient.post("/classify/", validated)

// After
const response = await apiClient.post("/classify", validated)
```

**태그**: @CODE:API-INTEGRATION-001:TRAILING-SLASH-CLASSIFY

##### 1.3 batchSearch 함수 (Line 98)
```typescript
// Before
const response = await apiClient.post("/batch-search/", validated)

// After
const response = await apiClient.post("/batch-search", validated)
```

**태그**: @CODE:API-INTEGRATION-001:TRAILING-SLASH-BATCH

#### 검증 방법
- 브라우저 DevTools Network 탭에서 307 상태 코드 미발생 확인
- 직접 200 OK 또는 적절한 응답 코드 수신 확인

---

### SPEC-2: 하드코딩 URL 제거

#### 대상 파일
`apps/frontend/lib/api/index.ts`

#### 변경 사항

##### 2.1 uploadDocument 함수 (Line 68)
```typescript
// Before
const response = await apiClient.post("http://localhost:8000/ingestion/upload", formData, {
  headers: { "Content-Type": "multipart/form-data" },
})

// After
const response = await apiClient.post("/ingestion/upload", formData, {
  headers: { "Content-Type": "multipart/form-data" },
})
```

**태그**: @CODE:API-INTEGRATION-001:HARDCODED-UPLOAD

**근거**:
- apiClient의 baseURL(`http://localhost:8000/api/v1`)과 상대 경로(`/ingestion/upload`) 조합
- 최종 URL: `http://localhost:8000/api/v1/ingestion/upload`
- 환경 변수로 도메인/포트 변경 가능

##### 2.2 getHealth 함수 (Line 75)
```typescript
// Before
const response = await apiClient.get("http://localhost:8000/health")

// After
const response = await apiClient.get("/healthz")
```

**태그**: @CODE:API-INTEGRATION-001:HARDCODED-HEALTH

**근거**:
- getSystemHealth (Line 80)는 이미 `/monitoring/health` 패턴 사용 중
- 일관성을 위해 동일한 패턴 적용

#### 주의사항
- **Backend 엔드포인트 확인 필요**: `/api/v1/ingestion/upload`가 실제 존재하는지 검증
- **대안**: Backend가 `/ingestion/upload`만 지원하면 `apiClient.post("/ingestion/upload")` 대신 절대 경로 필요 (별도 이슈)

---

### SPEC-3: CORS 설정 문서화

#### 대상 파일
`apps/api/config.py`

#### 작업 내용
**문서화 전용** (코드 수정 없음)

#### 현재 CORS 설정 검증

##### Development 환경 (Line 402-409)
```python
config.cors.allow_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8080",
    "http://localhost:8081",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080"
]
```

**검증 결과**:
- Frontend 개발 포트(3000) 포함 ✅
- Wildcard 미사용 (보안 준수) ✅
- Allow Credentials: `true` ✅

##### CORS Headers (Line 146-156)
```python
allow_headers: List[str] = field(default_factory=lambda: [
    "Accept",
    "Accept-Language",
    "Content-Language",
    "Content-Type",
    "Authorization",
    "X-API-Key",
    "X-Requested-With",
    "X-Request-ID",
    "Cache-Control"
])
```

**검증 결과**:
- Content-Type 포함 (JSON/FormData 지원) ✅
- Authorization 포함 (JWT 지원) ✅
- Wildcard 미사용 (보안 준수) ✅

**태그**: @DOC:API-INTEGRATION-001:CORS

#### 권장 사항
- 현재 설정 유지
- Production 환경 배포 시 HTTPS 엔드포인트로 변경 필수

---

## Traceability (@TAG 체계)

### SPEC 태그
- **@SPEC:API-INTEGRATION-001**: 본 명세서 전체

### 코드 태그
- **@CODE:API-INTEGRATION-001:TRAILING-SLASH-SEARCH**: search 함수 trailing slash 제거
- **@CODE:API-INTEGRATION-001:TRAILING-SLASH-CLASSIFY**: classify 함수 trailing slash 제거
- **@CODE:API-INTEGRATION-001:TRAILING-SLASH-BATCH**: batchSearch 함수 trailing slash 제거
- **@CODE:API-INTEGRATION-001:HARDCODED-UPLOAD**: uploadDocument 하드코딩 URL 제거
- **@CODE:API-INTEGRATION-001:HARDCODED-HEALTH**: getHealth 하드코딩 URL 제거

### 문서 태그
- **@DOC:API-INTEGRATION-001:CORS**: CORS 설정 검증 문서

### 테스트 태그 (구현 단계에서 추가)
- **@TEST:API-INTEGRATION-001:REDIRECT**: 307 Redirect 미발생 검증
- **@TEST:API-INTEGRATION-001:ENV**: 환경 변수 기반 URL 구성 검증

---

## Implementation Notes

### Backend 확인 필요 사항

#### 1. FastAPI 라우터 Trailing Slash 정책
다음 엔드포인트의 실제 정의 확인:
- `/api/v1/search` (trailing slash 없음 가정)
- `/api/v1/classify` (trailing slash 없음 가정)
- `/api/v1/batch-search` (trailing slash 없음 가정)

**확인 방법**:
```python
# apps/api/routers/*.py 파일 확인
@router.post("/search")  # 또는 "/search/"?
```

#### 2. Ingestion Upload 경로
현재 경로: `/ingestion/upload` (baseURL 제외)

**확인 필요**:
- `/api/v1/ingestion/upload`가 실제 엔드포인트인지
- `/ingestion/upload`가 별도 라우터인지 (api/v1 prefix 없음)

**확인 방법**:
```bash
curl -X POST http://localhost:8000/api/v1/ingestion/upload
curl -X POST http://localhost:8000/ingestion/upload
```

### Frontend 테스트 시나리오

#### 1. 개발 환경 테스트
```bash
# .env.development
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# 테스트
npm run dev
# 브라우저에서 search 함수 호출
# Network 탭에서 307 Redirect 미발생 확인
```

#### 2. 환경 변수 변경 테스트
```bash
# .env.production
NEXT_PUBLIC_API_URL=https://api.production.com/api/v1

# 빌드
npm run build

# uploadDocument, getHealth가 production URL 사용하는지 확인
```

---

## Success Criteria

### 1. 성능 개선
- 307 Redirect 완전 제거
- API 응답 시간 1 RTT 감소

### 2. 환경 이식성
- 환경 변수 변경만으로 모든 환경에서 동작
- 하드코딩된 URL 0개

### 3. 코드 일관성
- 모든 API 함수가 apiClient의 baseURL 사용
- 상대 경로 패턴 통일

### 4. 문서화
- CORS 설정 검증 완료
- Backend 엔드포인트 정책 문서화

---

## Risk Assessment

### 높음: Backend 엔드포인트 불일치
- **리스크**: Trailing slash 제거 후 Backend가 `/search/`만 지원하는 경우
- **대응**: Backend 라우터 코드 직접 확인 후 수정
- **완화**: 개발 환경에서 충분한 테스트

### 중간: Ingestion Upload 경로 오류
- **리스크**: `/api/v1/ingestion/upload`가 존재하지 않는 경우
- **대응**: Backend 엔드포인트 확인 후 올바른 경로 적용
- **완화**: curl 테스트로 사전 검증

### 낮음: CORS 문제
- **리스크**: 현재 설정이 적절하다고 가정했으나 실제 문제 발생
- **대응**: 현재 설정이 이미 검증됨 (개발 환경 동작 중)
- **완화**: 문서화만 수행하므로 영향 없음

---

## References

### 관련 파일
- `apps/frontend/lib/api/index.ts` - API 함수 정의
- `apps/frontend/lib/api/client.ts` - axios 클라이언트 설정
- `apps/frontend/lib/env.ts` - 환경 변수 검증
- `apps/api/config.py` - Backend CORS 설정

### 관련 문서
- [FastAPI Path Parameters](https://fastapi.tiangolo.com/tutorial/path-params/)
- [Axios Instance Configuration](https://axios-http.com/docs/instance)

### 관련 SPEC
- @SPEC:API-001 - API 기본 설계 (존재 시 참조)
- @SPEC:FOUNDATION-001 - Frontend 기초 구조 (존재 시 참조)
