# Implementation Plan: API-INTEGRATION-001

## 개요

Frontend-Backend API 통합 개선을 위한 구현 계획입니다. Trailing slash 불일치 해결과 하드코딩된 URL 제거를 통해 성능과 환경 이식성을 향상시킵니다.

---

## 우선순위별 마일스톤

### 1차 목표: Trailing Slash 제거 (Critical)

**목표**: 307 Redirect 제거를 통한 API 응답 속도 개선

#### 작업 항목
1. **Backend 라우터 확인**
   - `apps/api/routers/search.py` (또는 관련 파일) 읽기
   - `/search`, `/classify`, `/batch-search` 엔드포인트의 trailing slash 정책 확인
   - 실제 정의가 `/search`인지 `/search/`인지 검증

2. **Frontend 코드 수정**
   - `apps/frontend/lib/api/index.ts` 파일 수정
   - Line 52: `/search/` → `/search`
   - Line 58: `/classify/` → `/classify`
   - Line 98: `/batch-search/` → `/batch-search`

3. **개발 환경 테스트**
   - Frontend 개발 서버 실행
   - 각 API 함수 호출 테스트
   - Network 탭에서 307 Redirect 미발생 확인
   - 200 OK 응답 수신 확인

**완료 조건**:
- Backend 라우터 정의와 Frontend 호출 경로 완전 일치
- 모든 API 호출에서 307 상태 코드 미발생
- 정상적인 응답 데이터 수신

**의존성**: 없음 (독립 실행 가능)

---

### 2차 목표: 하드코딩 URL 제거 (High)

**목표**: 환경 변수 기반 설정으로 이식성 향상

#### 작업 항목

##### Phase 2.1: Backend 엔드포인트 검증
1. **Ingestion Upload 경로 확인**
   ```bash
   # 다음 경로 중 어느 것이 유효한지 확인
   curl -X POST http://localhost:8000/api/v1/ingestion/upload
   curl -X POST http://localhost:8000/ingestion/upload
   ```

2. **Health Check 경로 확인**
   ```bash
   # 다음 경로 중 어느 것이 유효한지 확인
   curl -X GET http://localhost:8000/api/v1/health
   curl -X GET http://localhost:8000/health
   ```

3. **Backend 라우터 코드 읽기**
   - `apps/api/routers/` 디렉토리의 관련 파일 확인
   - Ingestion 라우터 파일 검색 및 읽기
   - Health check 엔드포인트 정의 확인

##### Phase 2.2: Frontend 코드 수정
1. **uploadDocument 함수 수정** (Line 68)
   - 하드코딩 URL 제거
   - 상대 경로로 변경 (Backend 검증 결과 기반)
   - 옵션 1: `/ingestion/upload` (baseURL 적용)
   - 옵션 2: `/api/v1/ingestion/upload` (baseURL에 `/api/v1` 미포함 시)

2. **getHealth 함수 수정** (Line 75)
   - 하드코딩 URL 제거
   - 상대 경로로 변경
   - getSystemHealth (Line 80) 패턴 참고

##### Phase 2.3: 환경 변수 테스트
1. **.env 파일 준비**
   ```bash
   # .env.development
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

   # .env.staging (가상)
   NEXT_PUBLIC_API_URL=https://staging-api.example.com/api/v1
   ```

2. **환경별 동작 검증**
   - Development 환경에서 테스트
   - 환경 변수 변경 후 재빌드
   - 각 환경에서 올바른 URL 사용 확인

**완료 조건**:
- 모든 API 함수가 apiClient의 baseURL 사용
- 하드코딩된 `localhost:8000` 완전 제거
- 환경 변수 변경만으로 배포 가능

**의존성**: 1차 목표 완료 후 시작 권장 (독립 실행 가능하지만 테스트 효율성 고려)

---

### 3차 목표: CORS 설정 문서화 (Medium)

**목표**: Backend CORS 설정 검증 및 문서화

#### 작업 항목
1. **CORS 설정 검토**
   - `apps/api/config.py` Line 142-157 (CORSConfig 클래스) 확인 완료
   - Development 환경 설정 (Line 402-409) 확인 완료
   - Production 환경 고려사항 문서화

2. **보안 검증**
   - Wildcard origin 미사용 확인 ✅
   - Wildcard header 미사용 확인 ✅
   - HTTPS 적용 권장사항 기록

3. **문서 작성**
   - CORS 설정 체크리스트 작성
   - Production 배포 시 주의사항 정리

**완료 조건**:
- CORS 설정이 적절하게 구성되어 있음을 확인
- Production 환경 배포 가이드 작성
- 보안 체크리스트 완성

**의존성**: 독립 실행 가능 (문서화 전용)

---

### 최종 목표: 통합 테스트 및 검증 (Critical)

**목표**: 전체 변경사항의 안정성 확보

#### 작업 항목

##### Phase 4.1: 단위 테스트
1. **각 API 함수 개별 테스트**
   - search, classify, batchSearch
   - uploadDocument, getHealth, getSystemHealth
   - 각 함수의 URL 구성 확인
   - 응답 데이터 Zod 스키마 검증

##### Phase 4.2: 통합 테스트
1. **엔드투엔드 시나리오**
   - Frontend에서 실제 사용자 동작 시뮬레이션
   - 문서 업로드 → 분류 → 검색 플로우 테스트
   - Network 탭에서 모든 요청 모니터링

2. **성능 측정**
   - 307 Redirect 제거 전후 비교
   - API 응답 시간 측정
   - Network waterfall 분석

##### Phase 4.3: 환경 이식성 테스트
1. **다양한 환경 변수 조합 테스트**
   ```bash
   # Test 1: Default (localhost)
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

   # Test 2: Custom Port
   NEXT_PUBLIC_API_URL=http://localhost:9000/api/v1

   # Test 3: Remote (가상)
   NEXT_PUBLIC_API_URL=https://api.example.com/v2
   ```

2. **빌드 및 배포 시뮬레이션**
   - `npm run build` 실행
   - 환경 변수가 정적 파일에 올바르게 임베드되는지 확인
   - Production 모드에서 동작 검증

**완료 조건**:
- 모든 API 함수가 정상 동작
- 성능 개선 확인 (307 Redirect 제거)
- 환경 변수 기반 배포 검증 완료

**의존성**: 1차, 2차, 3차 목표 모두 완료 후 시작

---

## 기술적 접근 방법

### 1. Backend 라우터 확인 전략

#### 방법 1: 코드 읽기 (권장)
```bash
# Grep으로 관련 라우터 파일 검색
rg '@router\.(get|post).*/(search|classify|batch-search|ingestion|health)' apps/api/routers/

# 파일 직접 읽기
Read("apps/api/routers/search.py")
Read("apps/api/routers/classify.py")
```

**장점**:
- 정확한 엔드포인트 정의 확인
- Trailing slash 정책 명확히 파악
- 추가 파라미터나 제약사항 발견 가능

#### 방법 2: curl 테스트 (보조)
```bash
# Trailing slash 있는 경우
curl -v -X POST http://localhost:8000/api/v1/search/ -H "Content-Type: application/json" -d '{}'

# Trailing slash 없는 경우
curl -v -X POST http://localhost:8000/api/v1/search -H "Content-Type: application/json" -d '{}'

# 307 Redirect 확인
# Location 헤더 확인
```

**장점**:
- 실제 동작 확인
- 리다이렉트 여부 즉시 파악

---

### 2. Frontend 코드 수정 전략

#### Edit Tool 사용 (권장)
```typescript
// 정확한 old_string 매칭 필요
Edit({
  file_path: "apps/frontend/lib/api/index.ts",
  old_string: 'const response = await apiClient.post("/search/", validated)',
  new_string: 'const response = await apiClient.post("/search", validated)'
})
```

**주의사항**:
- 줄 번호 prefix 제외
- 정확한 인덴테이션 유지
- 파일을 먼저 Read로 읽어야 함

#### 일괄 수정 옵션
- 3개의 trailing slash를 순차적으로 수정
- 각 수정마다 Read → Edit 반복
- 하드코딩 URL 2개도 동일한 방식

---

### 3. 환경 변수 검증 전략

#### 현재 설정 확인
```typescript
// apps/frontend/lib/env.ts
const envSchema = z.object({
  NEXT_PUBLIC_API_URL: z.string().url().optional().default("http://localhost:8000/api/v1"),
  // ...
})
```

**특징**:
- Zod 스키마로 타입 안전성 보장
- URL 형식 자동 검증
- 기본값 제공 (개발 편의성)

#### 테스트 방법
```bash
# .env.development 생성
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1' > .env.development

# 빌드
npm run build

# 출력 파일에서 환경 변수 확인
grep -r 'NEXT_PUBLIC_API_URL' .next/
```

---

### 4. apiClient 사용 패턴

#### 올바른 패턴
```typescript
// ✅ 상대 경로 사용 (baseURL 자동 결합)
apiClient.post("/search", data)
// 결과: http://localhost:8000/api/v1/search

// ✅ 절대 경로 (baseURL과 독립)
apiClient.post("http://other-service.com/api", data)
// 결과: http://other-service.com/api
```

#### 잘못된 패턴 (현재 코드)
```typescript
// ❌ 하드코딩 절대 경로 (환경 변수 무시)
apiClient.post("http://localhost:8000/ingestion/upload", formData)
// 결과: 항상 localhost:8000 사용 (프로덕션에서 실패)
```

**수정 방향**:
- 절대 경로 → 상대 경로 변환
- apiClient의 baseURL 신뢰
- 환경 변수로 중앙 관리

---

## 아키텍처 설계 방향

### 1. URL 구성 계층

```
환경 변수 (.env)
  ↓
NEXT_PUBLIC_API_URL: "http://localhost:8000/api/v1"
  ↓
env.ts (Zod 검증)
  ↓
apiClient (axios instance)
  baseURL: env.NEXT_PUBLIC_API_URL
  ↓
API 함수 (index.ts)
  상대 경로: "/search"
  ↓
최종 URL 조합
  http://localhost:8000/api/v1/search
```

**장점**:
- 단일 진실 공급원 (Single Source of Truth)
- 환경별 설정 분리
- 타입 안전성 (Zod 검증)

---

### 2. 에러 처리 전략

#### 현재 구현 (apiClient Interceptor)
```typescript
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error("API Error:", error.response.status, error.response.data)
    }
    // ...
  }
)
```

**개선 방향** (선택 사항, 본 SPEC 범위 외):
- 307 Redirect 자동 재시도 로직 추가
- 환경 변수 검증 실패 시 명확한 에러 메시지
- Production 환경에서 console.error → 모니터링 서비스 전송

---

### 3. CORS 설정 아키텍처

#### Backend (FastAPI)
```python
# apps/api/config.py
config.cors.allow_origins = [
    "http://localhost:3000",  # Frontend Dev
    # ...
]
config.cors.allow_credentials = True
config.cors.allow_headers = [
    "Content-Type",
    "Authorization",
    # ...
]
```

**특징**:
- 환경별 Origin 리스트 관리
- Wildcard 금지 (보안)
- Preflight 요청 지원 (OPTIONS)

#### Frontend (Axios)
```typescript
// apps/frontend/lib/api/client.ts
export const apiClient = axios.create({
  baseURL: env.NEXT_PUBLIC_API_URL,
  headers: {
    "Content-Type": "application/json",
    // ...
  },
})
```

**특징**:
- 자동 CORS preflight 처리
- Credentials 자동 포함 (withCredentials: true 설정 시)

---

## 리스크 관리 및 대응 방안

### Risk 1: Backend 라우터 Trailing Slash 불일치

**시나리오**: Frontend에서 `/search`로 변경했지만 Backend가 `/search/`만 지원

**대응 방안**:
1. **우선순위**: Backend 코드 읽기로 사전 확인
2. **대안 1**: Backend 라우터 수정 (FastAPI)
   ```python
   @router.post("/search")  # trailing slash 제거
   ```
3. **대안 2**: Frontend 복구 (원래대로)
   ```typescript
   apiClient.post("/search/", validated)  # trailing slash 유지
   ```

**선택 기준**:
- Backend 수정 가능 여부
- Breaking Change 영향 범위
- API 버전 정책

---

### Risk 2: Ingestion Upload 경로 오류

**시나리오**: `/api/v1/ingestion/upload`가 존재하지 않고 `/ingestion/upload`만 유효

**대응 방안**:
1. **curl 테스트로 사전 확인**
   ```bash
   curl -X POST http://localhost:8000/api/v1/ingestion/upload -v
   curl -X POST http://localhost:8000/ingestion/upload -v
   ```

2. **옵션 A**: baseURL에 `/api/v1` 미포함 시
   ```typescript
   // env.ts
   NEXT_PUBLIC_API_URL: "http://localhost:8000"

   // index.ts
   apiClient.post("/api/v1/search", data)
   apiClient.post("/ingestion/upload", formData)  // 별도 prefix
   ```

3. **옵션 B**: 별도 axios 인스턴스 생성
   ```typescript
   const ingestionClient = axios.create({
     baseURL: "http://localhost:8000",  // /api/v1 제외
   })

   ingestionClient.post("/ingestion/upload", formData)
   ```

**권장**: curl 테스트 후 실제 경로에 맞게 조정

---

### Risk 3: 환경 변수 캐싱 문제

**시나리오**: .env 파일 변경 후에도 이전 값 사용

**대응 방안**:
1. **개발 서버 재시작**
   ```bash
   # Next.js dev server 재시작 필요
   npm run dev
   ```

2. **빌드 캐시 삭제**
   ```bash
   rm -rf .next
   npm run build
   ```

3. **검증 방법**
   ```typescript
   // 임시 로그 추가
   console.log('Current API URL:', env.NEXT_PUBLIC_API_URL)
   ```

---

## 테스트 체크리스트

### 1. 기능 테스트

#### 1.1 Trailing Slash 제거
- [ ] search 함수 호출 → 200 OK (307 미발생)
- [ ] classify 함수 호출 → 200 OK (307 미발생)
- [ ] batchSearch 함수 호출 → 200 OK (307 미발생)
- [ ] Network 탭에서 모든 요청이 직접 응답 확인

#### 1.2 하드코딩 URL 제거
- [ ] uploadDocument 함수 → 올바른 baseURL 사용 확인
- [ ] getHealth 함수 → 올바른 baseURL 사용 확인
- [ ] 환경 변수 변경 시 URL 자동 변경 확인

#### 1.3 CORS 설정
- [ ] OPTIONS preflight 요청 성공
- [ ] POST 요청에 CORS 헤더 포함 확인
- [ ] Credentials 포함 요청 성공

---

### 2. 성능 테스트

#### 2.1 응답 시간 측정
- [ ] 307 Redirect 제거 전 평균 응답 시간 기록
- [ ] 307 Redirect 제거 후 평균 응답 시간 기록
- [ ] 개선 정도 확인 (최소 1 RTT 감소 기대)

#### 2.2 Network Waterfall 분석
- [ ] 각 API 호출의 timing 분석
- [ ] DNS lookup, TCP handshake, Request/Response 시간
- [ ] Redirect overhead 제거 확인

---

### 3. 환경 이식성 테스트

#### 3.1 다양한 환경 변수 조합
- [ ] NEXT_PUBLIC_API_URL 미설정 → 기본값 사용 확인
- [ ] NEXT_PUBLIC_API_URL=http://localhost:9000/api/v1 → 올바르게 적용
- [ ] NEXT_PUBLIC_API_URL=https://api.production.com/v2 → 올바르게 적용

#### 3.2 빌드 및 배포
- [ ] `npm run build` 성공
- [ ] `.next/` 디렉토리에 환경 변수 임베드 확인
- [ ] Production 모드 실행 성공

---

### 4. 회귀 테스트

#### 4.1 기존 기능 유지
- [ ] getTaxonomyTree 함수 정상 동작
- [ ] generateEmbedding 함수 정상 동작
- [ ] evaluateRagResponse 함수 정상 동작
- [ ] Agent 관련 함수들 정상 동작
- [ ] HITL 관련 함수들 정상 동작

#### 4.2 스키마 검증
- [ ] 모든 API 응답이 Zod 스키마 검증 통과
- [ ] 타입 안전성 유지
- [ ] TypeScript 컴파일 에러 없음

---

## 완료 조건 (Definition of Done)

### 필수 조건
1. ✅ 모든 trailing slash 제거 (search, classify, batchSearch)
2. ✅ 모든 하드코딩 URL 제거 (uploadDocument, getHealth)
3. ✅ Backend 라우터와 Frontend 호출 경로 일치 확인
4. ✅ 307 Redirect 완전 제거
5. ✅ 환경 변수 기반 URL 구성 검증
6. ✅ CORS 설정 문서화 완료

### 검증 조건
1. ✅ 개발 환경에서 모든 API 함수 정상 동작
2. ✅ Network 탭에서 307 상태 코드 미발생
3. ✅ 환경 변수 변경 테스트 통과
4. ✅ 회귀 테스트 통과 (기존 기능 유지)

### 문서화 조건
1. ✅ CORS 설정 체크리스트 작성
2. ✅ Backend 엔드포인트 정책 문서화
3. ✅ Production 배포 가이드 작성

---

## 다음 단계

### 구현 후 활동
1. **성능 모니터링**
   - API 응답 시간 추이 관찰
   - 307 Redirect 재발 여부 모니터링

2. **문서 업데이트**
   - Frontend API 사용 가이드 작성
   - Backend 엔드포인트 명세 문서화

3. **관련 SPEC 작성**
   - API 버전 관리 SPEC (필요 시)
   - 환경 설정 표준화 SPEC (필요 시)

### git-manager 에이전트 작업
- Git 브랜치 생성: `feature/api-integration-001`
- 커밋 메시지 작성
- Draft PR 생성 (Team 모드인 경우)

---

## 참고 사항

### 시간 예측 금지
본 계획에는 "예상 소요 시간" 정보가 포함되지 않습니다. 이는 TRUST 원칙의 Trackable 요구사항을 준수하기 위함입니다.

### 우선순위 기반 실행
- Critical: 1차 목표, 최종 목표
- High: 2차 목표
- Medium: 3차 목표

각 마일스톤은 독립적으로 실행 가능하지만, 최종 목표는 모든 이전 목표 완료 후 시작을 권장합니다.
