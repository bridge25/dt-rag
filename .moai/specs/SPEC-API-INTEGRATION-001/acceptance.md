# Acceptance Criteria: API-INTEGRATION-001

## 개요

Frontend-Backend API 통합 개선에 대한 상세한 수락 기준을 정의합니다. 모든 기준은 Given-When-Then 형식의 시나리오로 작성되었으며, 자동화 가능한 검증 방법을 포함합니다.

---

## AC-1: Trailing Slash 제거

### AC-1.1: search 함수 307 Redirect 제거

#### Given-When-Then 시나리오
```gherkin
Given Frontend 애플리케이션이 실행 중이고
  And Backend API 서버가 http://localhost:8000에서 실행 중이고
  And search 라우터가 "/search" (trailing slash 없음)로 정의되어 있을 때

When 사용자가 search 함수를 호출하면
  search({ query: "test", top_k: 5 })

Then API 요청이 "http://localhost:8000/api/v1/search"로 전송되고
  And HTTP 상태 코드가 200 OK이고
  And 307 Temporary Redirect가 발생하지 않고
  And SearchResponse 스키마에 맞는 데이터가 반환된다
```

#### 검증 방법

**자동 검증** (Jest/Vitest):
```typescript
test('search 함수는 307 Redirect 없이 직접 응답한다', async () => {
  // Arrange
  const mockAdapter = new MockAdapter(apiClient);
  mockAdapter.onPost('/search').reply(200, {
    results: [],
    query: "test",
    top_k: 5
  });

  // Act
  const response = await search({ query: "test", top_k: 5 });

  // Assert
  expect(mockAdapter.history.post.length).toBe(1);
  expect(mockAdapter.history.post[0].url).toBe('/search');  // trailing slash 없음
  expect(response.results).toBeDefined();
});
```

**수동 검증** (Browser DevTools):
1. Frontend 애플리케이션 실행
2. search 함수 트리거 (UI 또는 콘솔)
3. Network 탭 확인:
   - Request URL: `http://localhost:8000/api/v1/search`
   - Status Code: `200 OK` (NOT `307 Temporary Redirect`)
   - Response 데이터 확인

**통과 기준**:
- ✅ 307 상태 코드 미발생
- ✅ 200 OK 직접 응답
- ✅ 올바른 SearchResponse 반환

---

### AC-1.2: classify 함수 307 Redirect 제거

#### Given-When-Then 시나리오
```gherkin
Given Frontend 애플리케이션이 실행 중이고
  And Backend API 서버가 실행 중이고
  And classify 라우터가 "/classify" (trailing slash 없음)로 정의되어 있을 때

When 사용자가 classify 함수를 호출하면
  classify({ text: "sample document" })

Then API 요청이 "http://localhost:8000/api/v1/classify"로 전송되고
  And HTTP 상태 코드가 200 OK이고
  And 307 Temporary Redirect가 발생하지 않고
  And ClassifyResponse 스키마에 맞는 데이터가 반환된다
```

#### 검증 방법

**자동 검증** (Jest/Vitest):
```typescript
test('classify 함수는 307 Redirect 없이 직접 응답한다', async () => {
  // Arrange
  const mockAdapter = new MockAdapter(apiClient);
  mockAdapter.onPost('/classify').reply(200, {
    category: "TEST_CATEGORY",
    confidence: 0.95
  });

  // Act
  const response = await classify({ text: "sample document" });

  // Assert
  expect(mockAdapter.history.post[0].url).toBe('/classify');
  expect(response.category).toBe("TEST_CATEGORY");
});
```

**수동 검증** (Browser DevTools):
1. classify 함수 호출
2. Network 탭에서 확인:
   - Request URL: `http://localhost:8000/api/v1/classify`
   - Status Code: `200 OK`
   - Response Body: `{ category, confidence }`

**통과 기준**:
- ✅ 307 상태 코드 미발생
- ✅ 올바른 분류 결과 반환

---

### AC-1.3: batchSearch 함수 307 Redirect 제거

#### Given-When-Then 시나리오
```gherkin
Given Frontend 애플리케이션이 실행 중이고
  And Backend API 서버가 실행 중이고
  And batch-search 라우터가 "/batch-search" (trailing slash 없음)로 정의되어 있을 때

When 사용자가 batchSearch 함수를 호출하면
  batchSearch({ queries: ["query1", "query2"], top_k: 5 })

Then API 요청이 "http://localhost:8000/api/v1/batch-search"로 전송되고
  And HTTP 상태 코드가 200 OK이고
  And 307 Temporary Redirect가 발생하지 않고
  And BatchSearchResponse 스키마에 맞는 데이터가 반환된다
```

#### 검증 방법

**자동 검증** (Jest/Vitest):
```typescript
test('batchSearch 함수는 307 Redirect 없이 직접 응답한다', async () => {
  // Arrange
  const mockAdapter = new MockAdapter(apiClient);
  mockAdapter.onPost('/batch-search').reply(200, {
    results: [
      { query: "query1", results: [] },
      { query: "query2", results: [] }
    ]
  });

  // Act
  const response = await batchSearch({
    queries: ["query1", "query2"],
    top_k: 5
  });

  // Assert
  expect(mockAdapter.history.post[0].url).toBe('/batch-search');
  expect(response.results.length).toBe(2);
});
```

**통과 기준**:
- ✅ 307 상태 코드 미발생
- ✅ 배치 검색 결과 정상 반환

---

## AC-2: 하드코딩 URL 제거 및 baseURL 준수

### AC-2.1: uploadDocument 함수 baseURL 사용

#### Given-When-Then 시나리오
```gherkin
Given NEXT_PUBLIC_API_URL 환경 변수가 "http://localhost:8000/api/v1"로 설정되어 있고
  And Frontend 애플리케이션이 실행 중일 때

When 사용자가 uploadDocument 함수를 호출하면
  const formData = new FormData();
  formData.append('file', file);
  uploadDocument(formData)

Then API 요청이 "http://localhost:8000/api/v1/ingestion/upload"로 전송되고
  And 하드코딩된 "http://localhost:8000/ingestion/upload"가 사용되지 않고
  And apiClient의 baseURL과 상대 경로 "/ingestion/upload"가 조합되어 사용되고
  And DocumentUploadResponse 스키마에 맞는 데이터가 반환된다
```

#### 검증 방법

**자동 검증** (Jest/Vitest):
```typescript
test('uploadDocument는 baseURL을 사용한다', async () => {
  // Arrange
  const mockAdapter = new MockAdapter(apiClient);
  mockAdapter.onPost('/ingestion/upload').reply(200, {
    document_id: "doc-123",
    status: "uploaded"
  });

  const formData = new FormData();
  formData.append('file', new Blob(['test'], { type: 'text/plain' }));

  // Act
  const response = await uploadDocument(formData);

  // Assert
  const lastRequest = mockAdapter.history.post[0];
  expect(lastRequest.url).toBe('/ingestion/upload');  // 상대 경로
  expect(lastRequest.url).not.toContain('localhost:8000');  // 하드코딩 없음
  expect(response.document_id).toBe("doc-123");
});
```

**수동 검증** (Browser DevTools):
1. 파일 업로드 UI 사용
2. Network 탭 확인:
   - Request URL: `http://localhost:8000/api/v1/ingestion/upload`
   - Request Method: `POST`
   - Content-Type: `multipart/form-data`

**환경 변수 변경 테스트**:
```bash
# .env.test
NEXT_PUBLIC_API_URL=http://test-api.example.com/v2

# 기대 결과
# Request URL: http://test-api.example.com/v2/ingestion/upload
```

**통과 기준**:
- ✅ 하드코딩 URL 미사용
- ✅ baseURL + 상대 경로 조합 사용
- ✅ 환경 변수 변경 시 URL 자동 변경

---

### AC-2.2: getHealth 함수 baseURL 사용

#### Given-When-Then 시나리오
```gherkin
Given NEXT_PUBLIC_API_URL 환경 변수가 "http://localhost:8000/api/v1"로 설정되어 있고
  And Frontend 애플리케이션이 실행 중일 때

When 사용자가 getHealth 함수를 호출하면
  getHealth()

Then API 요청이 "http://localhost:8000/api/v1/healthz"로 전송되고
  And 하드코딩된 "http://localhost:8000/health"가 사용되지 않고
  And apiClient의 baseURL과 상대 경로 "/healthz"가 조합되어 사용되고
  And HealthCheckResponse 스키마에 맞는 데이터가 반환된다
```

#### 검증 방법

**자동 검증** (Jest/Vitest):
```typescript
test('getHealth는 baseURL을 사용한다', async () => {
  // Arrange
  const mockAdapter = new MockAdapter(apiClient);
  mockAdapter.onGet('/healthz').reply(200, {
    status: "healthy",
    timestamp: new Date().toISOString()
  });

  // Act
  const response = await getHealth();

  // Assert
  const lastRequest = mockAdapter.history.get[0];
  expect(lastRequest.url).toBe('/healthz');
  expect(lastRequest.url).not.toContain('localhost:8000');
  expect(response.status).toBe("healthy");
});
```

**수동 검증** (Browser DevTools):
1. Health check 호출 (앱 시작 시 또는 수동)
2. Network 탭 확인:
   - Request URL: `http://localhost:8000/api/v1/healthz`
   - Status Code: `200 OK`

**통과 기준**:
- ✅ 하드코딩 URL 미사용
- ✅ getSystemHealth (Line 80)와 동일한 패턴 사용
- ✅ 환경 변수 기반 URL 구성

---

### AC-2.3: 코드 일관성 검증

#### Given-When-Then 시나리오
```gherkin
Given apps/frontend/lib/api/index.ts 파일이 있을 때

When 파일 내 모든 API 함수를 검사하면

Then 하드코딩된 절대 URL (http://localhost:8000)이 존재하지 않고
  And 모든 함수가 상대 경로 또는 apiClient.baseURL을 사용하고
  And URL 구성 패턴이 일관되어 있다
```

#### 검증 방법

**자동 검증** (ESLint Custom Rule):
```typescript
// .eslintrc.js (선택사항)
rules: {
  'no-hardcoded-urls': ['error', {
    forbiddenPatterns: [
      'http://localhost:8000',
      'http://127.0.0.1:8000'
    ]
  }]
}
```

**수동 검증** (Grep):
```bash
# 하드코딩된 localhost URL 검색
grep -n "http://localhost:8000" apps/frontend/lib/api/index.ts

# 기대 결과: 매칭 없음 (No matches)
```

**통과 기준**:
- ✅ `http://localhost` 패턴 0개
- ✅ `http://127.0.0.1` 패턴 0개
- ✅ 모든 API 함수가 상대 경로 사용

---

## AC-3: 환경 이식성 검증

### AC-3.1: 개발 환경 동작

#### Given-When-Then 시나리오
```gherkin
Given .env.development 파일이 다음과 같이 설정되어 있을 때
  NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
  And Frontend 개발 서버가 실행 중일 때

When 임의의 API 함수를 호출하면

Then 모든 API 요청이 http://localhost:8000/api/v1 baseURL을 사용하고
  And Backend 서버와 정상적으로 통신하고
  And 올바른 응답 데이터를 받는다
```

#### 검증 방법

**수동 검증**:
```bash
# 1. 환경 파일 확인
cat .env.development
# NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# 2. 개발 서버 실행
npm run dev

# 3. 브라우저에서 앱 열기
# 4. Network 탭에서 모든 요청 확인
#    - General → Request URL → http://localhost:8000/api/v1/... 확인
```

**통과 기준**:
- ✅ 모든 API 호출이 localhost:8000/api/v1 사용
- ✅ CORS 에러 없음
- ✅ 정상적인 응답 수신

---

### AC-3.2: 프로덕션 환경 시뮬레이션

#### Given-When-Then 시나리오
```gherkin
Given .env.production 파일이 다음과 같이 설정되어 있을 때
  NEXT_PUBLIC_API_URL=https://api.production.com/v2
  And Next.js 애플리케이션이 프로덕션 모드로 빌드되었을 때

When 빌드된 애플리케이션을 실행하면

Then 모든 API 요청이 https://api.production.com/v2 baseURL을 사용하고
  And localhost:8000 URL이 사용되지 않고
  And 환경 변수 값이 정적 파일에 올바르게 임베드된다
```

#### 검증 방법

**빌드 테스트**:
```bash
# 1. 프로덕션 환경 변수 설정
echo 'NEXT_PUBLIC_API_URL=https://api.production.com/v2' > .env.production

# 2. 프로덕션 빌드
npm run build

# 3. 빌드 결과 확인
grep -r "api.production.com" .next/

# 4. 프로덕션 모드 실행 (로컬)
npm run start

# 5. 브라우저 Network 탭 확인
#    - Request URL → https://api.production.com/v2/... 확인
```

**통과 기준**:
- ✅ 빌드 결과물에 production URL 포함
- ✅ localhost:8000 참조 없음
- ✅ 런타임에서 올바른 URL 사용

---

### AC-3.3: 환경 변수 미설정 시 기본값 사용

#### Given-When-Then 시나리오
```gherkin
Given NEXT_PUBLIC_API_URL 환경 변수가 설정되어 있지 않을 때

When Frontend 애플리케이션을 실행하면

Then 기본값 "http://localhost:8000/api/v1"이 사용되고
  And 환경 변수 검증 에러가 발생하지 않고
  And 로컬 개발 환경에서 정상적으로 동작한다
```

#### 검증 방법

**수동 검증**:
```bash
# 1. .env 파일 제거 또는 백업
mv .env.development .env.development.backup

# 2. 개발 서버 실행
npm run dev

# 3. 콘솔 로그 확인 (에러 없음)
# 4. Network 탭 확인 → http://localhost:8000/api/v1/... 사용
```

**통과 기준**:
- ✅ 에러 없이 실행
- ✅ 기본값 URL 사용
- ✅ Backend 연결 성공

---

## AC-4: 성능 개선 검증

### AC-4.1: 307 Redirect 제거로 인한 응답 시간 개선

#### Given-When-Then 시나리오
```gherkin
Given Trailing slash 제거 전 search 함수 호출 시 307 Redirect가 발생했고
  And 평균 응답 시간이 T ms였을 때

When Trailing slash 제거 후 search 함수를 호출하면

Then 307 Redirect가 발생하지 않고
  And 평균 응답 시간이 T - RTT ms로 개선되고
  And Network waterfall에서 redirect overhead가 제거된다
```

#### 검증 방법

**성능 측정** (Browser DevTools):
```javascript
// 1. Performance 탭 또는 Network 탭 사용
// 2. search 함수 10회 호출
// 3. 평균 응답 시간 계산

// Before (Trailing slash 있음):
// Request 1: /search/ → 307 → /search (150ms)
// Request 2: /search/ → 307 → /search (145ms)
// Average: 147.5ms

// After (Trailing slash 없음):
// Request 1: /search → 200 OK (120ms)
// Request 2: /search → 200 OK (115ms)
// Average: 117.5ms

// 개선: 30ms (약 20% 향상)
```

**자동 측정** (Performance API):
```typescript
test('search 함수의 응답 시간이 개선되었다', async () => {
  const iterations = 10;
  const times: number[] = [];

  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    await search({ query: "test", top_k: 5 });
    const end = performance.now();
    times.push(end - start);
  }

  const average = times.reduce((a, b) => a + b) / times.length;

  // 기대: 200ms 이하 (Redirect 제거 전 대비)
  expect(average).toBeLessThan(200);
});
```

**통과 기준**:
- ✅ 307 Redirect 완전 제거
- ✅ 평균 응답 시간 개선 확인
- ✅ Network waterfall에서 추가 요청 없음

---

### AC-4.2: Network 왕복 횟수 감소

#### Given-When-Then 시나리오
```gherkin
Given search 함수 호출 시 Network 탭에서 요청을 관찰할 때

When Trailing slash 제거 후 search 함수를 호출하면

Then 단일 HTTP 요청만 발생하고
  And 307 Redirect로 인한 추가 왕복이 발생하지 않고
  And Time to First Byte (TTFB)가 개선된다
```

#### 검증 방법

**수동 검증** (Browser DevTools Network 탭):
```
Before:
1. POST /search/ → 307 Temporary Redirect (Location: /search)
2. POST /search → 200 OK
   Total: 2 requests

After:
1. POST /search → 200 OK
   Total: 1 request
```

**통과 기준**:
- ✅ 요청 횟수 2 → 1 감소
- ✅ TTFB 개선 확인

---

## AC-5: CORS 설정 검증

### AC-5.1: Preflight 요청 성공

#### Given-When-Then 시나리오
```gherkin
Given Frontend가 http://localhost:3000에서 실행 중이고
  And Backend CORS 설정이 localhost:3000을 허용하고
  And POST 요청을 보내려 할 때

When 브라우저가 OPTIONS preflight 요청을 보내면

Then Backend가 200 OK 또는 204 No Content를 응답하고
  And Access-Control-Allow-Origin 헤더가 "http://localhost:3000"이고
  And Access-Control-Allow-Methods에 "POST"가 포함되고
  And 실제 POST 요청이 성공한다
```

#### 검증 방법

**수동 검증** (Browser DevTools):
```
Network 탭:
1. OPTIONS /search (Preflight)
   Response Headers:
     Access-Control-Allow-Origin: http://localhost:3000
     Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
     Access-Control-Allow-Headers: Content-Type, Authorization, ...
   Status: 200 OK

2. POST /search (Actual Request)
   Status: 200 OK
```

**통과 기준**:
- ✅ Preflight 요청 성공
- ✅ CORS 헤더 올바름
- ✅ 실제 요청 성공

---

### AC-5.2: CORS 설정 문서화

#### Given-When-Then 시나리오
```gherkin
Given apps/api/config.py 파일에 CORS 설정이 정의되어 있을 때

When CORS 설정을 검토하면

Then allow_origins에 wildcard "*"가 사용되지 않고
  And 명시적인 Origin 리스트가 정의되어 있고
  And allow_headers에 필요한 헤더만 포함되어 있고
  And Production 환경에서 HTTPS Origin만 사용하고
  And 문서화가 완료되어 있다
```

#### 검증 방법

**코드 리뷰**:
```python
# apps/api/config.py
# Line 142-157: CORSConfig 클래스
allow_origins: List[str] = field(default_factory=lambda: [
    "http://localhost:3000",  # ✅ 명시적 Origin
    "http://localhost:3001",
    # ...
])
allow_credentials: bool = True  # ✅
allow_headers: List[str] = field(default_factory=lambda: [
    "Content-Type",  # ✅
    "Authorization",  # ✅
    # ...
])
```

**문서 체크리스트**:
- [x] Wildcard 미사용 확인
- [x] Development Origins 목록 확인
- [x] Production HTTPS 권장사항 문서화
- [x] Credentials 활성화 이유 설명

**통과 기준**:
- ✅ 보안 모범 사례 준수
- ✅ 문서화 완료

---

## AC-6: 회귀 테스트

### AC-6.1: 기존 API 함수 동작 유지

#### Given-When-Then 시나리오
```gherkin
Given Trailing slash 제거 및 하드코딩 URL 제거가 완료되었을 때

When 다음 기존 API 함수들을 호출하면
  - getTaxonomyTree
  - generateEmbedding
  - evaluateRagResponse
  - createAgentFromCategory
  - listAgents
  - getAgent
  - updateAgent
  - deleteAgent
  - getAgentMetrics
  - getHITLTasks
  - submitHITLReview

Then 모든 함수가 정상적으로 동작하고
  And 응답 데이터가 예상대로 반환되고
  And 타입 안전성이 유지되고
  And 기존 동작에 영향이 없다
```

#### 검증 방법

**자동 테스트** (Jest/Vitest Suite):
```typescript
describe('API Integration Regression Tests', () => {
  test('getTaxonomyTree 정상 동작', async () => {
    // ...
  });

  test('generateEmbedding 정상 동작', async () => {
    // ...
  });

  // ... 모든 기존 함수 테스트
});
```

**통과 기준**:
- ✅ 모든 기존 테스트 통과
- ✅ 타입 검사 에러 없음
- ✅ 런타임 에러 없음

---

### AC-6.2: Zod 스키마 검증 유지

#### Given-When-Then 시나리오
```gherkin
Given 모든 API 함수가 Zod 스키마로 요청/응답을 검증할 때

When API 호출이 발생하면

Then 요청 데이터가 Schema.parse()를 통과하고
  And 응답 데이터가 Schema.parse()를 통과하고
  And 타입 불일치 시 명확한 에러가 발생한다
```

#### 검증 방법

**자동 검증**:
```typescript
test('API 응답이 Zod 스키마를 준수한다', async () => {
  const response = await search({ query: "test", top_k: 5 });

  // Zod 검증 성공 시 에러 없음
  expect(() => SearchResponseSchema.parse(response)).not.toThrow();
});
```

**통과 기준**:
- ✅ 모든 스키마 검증 통과
- ✅ 타입 안전성 유지

---

## 품질 게이트 (Quality Gates)

### Gate 1: 코드 품질
- [ ] ESLint 에러 0개
- [ ] TypeScript 컴파일 에러 0개
- [ ] 하드코딩 URL 0개 (Grep 검증)
- [ ] 일관된 코드 스타일 유지

### Gate 2: 기능 완전성
- [ ] AC-1 (Trailing Slash 제거) 100% 통과
- [ ] AC-2 (하드코딩 URL 제거) 100% 통과
- [ ] AC-3 (환경 이식성) 100% 통과
- [ ] AC-6 (회귀 테스트) 100% 통과

### Gate 3: 성능 기준
- [ ] 307 Redirect 발생률 0%
- [ ] API 평균 응답 시간 개선 확인
- [ ] Network 왕복 횟수 감소 확인

### Gate 4: 보안 기준
- [ ] CORS 설정 검증 완료
- [ ] Wildcard Origin 미사용
- [ ] Production HTTPS 권장사항 문서화

### Gate 5: 문서화
- [ ] CORS 설정 체크리스트 작성
- [ ] Backend 엔드포인트 정책 문서화
- [ ] 환경 변수 설정 가이드 작성

---

## 검증 도구 (Validation Tools)

### 1. 자동화된 테스트

#### Jest/Vitest 테스트 스위트
```typescript
// apps/frontend/lib/api/__tests__/integration.test.ts
describe('API Integration Tests', () => {
  describe('AC-1: Trailing Slash 제거', () => {
    test('AC-1.1: search 함수', async () => {
      // ...
    });
    test('AC-1.2: classify 함수', async () => {
      // ...
    });
    test('AC-1.3: batchSearch 함수', async () => {
      // ...
    });
  });

  describe('AC-2: 하드코딩 URL 제거', () => {
    test('AC-2.1: uploadDocument 함수', async () => {
      // ...
    });
    test('AC-2.2: getHealth 함수', async () => {
      // ...
    });
    test('AC-2.3: 코드 일관성', () => {
      // Grep 또는 정적 분석
    });
  });

  // ... AC-3, AC-6
});
```

**실행**:
```bash
npm run test -- apps/frontend/lib/api/__tests__/integration.test.ts
```

---

### 2. 수동 검증 체크리스트

#### DevTools Network 탭 체크리스트
- [ ] search 호출 → 307 미발생, 200 OK 확인
- [ ] classify 호출 → 307 미발생, 200 OK 확인
- [ ] batchSearch 호출 → 307 미발생, 200 OK 확인
- [ ] uploadDocument 호출 → baseURL 사용 확인
- [ ] getHealth 호출 → baseURL 사용 확인
- [ ] 모든 요청 URL에 localhost:8000/api/v1 prefix 확인

#### CORS 헤더 체크리스트
- [ ] Access-Control-Allow-Origin: http://localhost:3000
- [ ] Access-Control-Allow-Credentials: true
- [ ] Access-Control-Allow-Methods: POST, GET, ... 확인
- [ ] Access-Control-Allow-Headers: Content-Type, Authorization, ... 확인

---

### 3. 성능 프로파일링

#### Chrome DevTools Performance 탭
```javascript
// 1. Performance 탭 열기
// 2. Record 시작
// 3. search 함수 10회 호출
// 4. Record 중지
// 5. Network 섹션에서 redirect overhead 확인

// Before: search → 307 → search (2 entries)
// After: search → 200 (1 entry)
```

#### Lighthouse 성능 감사
```bash
# Frontend 빌드
npm run build
npm run start

# Lighthouse 실행
lighthouse http://localhost:3000 --view

# 네트워크 요청 분석
# - Redirect 횟수 확인
# - TTFB 확인
```

---

### 4. 환경 변수 검증 스크립트

#### validate-env.sh
```bash
#!/bin/bash
# 환경 변수 검증 스크립트

echo "Validating environment variables..."

# .env.development 확인
if [ -f .env.development ]; then
  source .env.development
  echo "✅ .env.development 파일 존재"
  echo "   NEXT_PUBLIC_API_URL: $NEXT_PUBLIC_API_URL"
else
  echo "⚠️  .env.development 파일 없음 (기본값 사용)"
fi

# 하드코딩 URL 검색
echo "Checking for hardcoded URLs..."
HARDCODED=$(grep -c "http://localhost:8000" apps/frontend/lib/api/index.ts)

if [ "$HARDCODED" -eq 0 ]; then
  echo "✅ 하드코딩 URL 없음"
else
  echo "❌ 하드코딩 URL 발견: $HARDCODED 개"
  exit 1
fi

echo "✅ 모든 검증 통과"
```

**실행**:
```bash
chmod +x validate-env.sh
./validate-env.sh
```

---

## 완료 조건 체크리스트 (Definition of Done)

### 필수 항목
- [ ] AC-1.1: search 함수 307 Redirect 제거 ✅
- [ ] AC-1.2: classify 함수 307 Redirect 제거 ✅
- [ ] AC-1.3: batchSearch 함수 307 Redirect 제거 ✅
- [ ] AC-2.1: uploadDocument 함수 baseURL 사용 ✅
- [ ] AC-2.2: getHealth 함수 baseURL 사용 ✅
- [ ] AC-2.3: 코드 일관성 검증 ✅
- [ ] AC-3.1: 개발 환경 동작 검증 ✅
- [ ] AC-3.2: 프로덕션 환경 시뮬레이션 ✅
- [ ] AC-3.3: 환경 변수 미설정 시 기본값 사용 ✅

### 성능 항목
- [ ] AC-4.1: 307 Redirect 제거로 인한 응답 시간 개선 ✅
- [ ] AC-4.2: Network 왕복 횟수 감소 ✅

### 보안 항목
- [ ] AC-5.1: Preflight 요청 성공 ✅
- [ ] AC-5.2: CORS 설정 문서화 ✅

### 회귀 테스트 항목
- [ ] AC-6.1: 기존 API 함수 동작 유지 ✅
- [ ] AC-6.2: Zod 스키마 검증 유지 ✅

### 문서화 항목
- [ ] CORS 설정 체크리스트 작성
- [ ] Backend 엔드포인트 정책 문서화
- [ ] 환경 변수 설정 가이드 작성
- [ ] Production 배포 주의사항 정리

### 코드 품질 항목
- [ ] ESLint 에러 0개
- [ ] TypeScript 컴파일 에러 0개
- [ ] 하드코딩 URL 0개
- [ ] 일관된 코드 스타일 유지

---

## 롤백 계획 (Rollback Plan)

### 롤백 트리거
다음 조건 중 하나라도 발생 시 롤백:
1. AC-1 실패: 307 Redirect가 404 Not Found로 변경된 경우
2. AC-2 실패: uploadDocument/getHealth가 동작하지 않는 경우
3. AC-6 실패: 기존 기능이 손상된 경우

### 롤백 절차
```bash
# 1. Git 브랜치로 이동
git checkout master

# 2. 변경사항 되돌리기
git revert <commit-hash>

# 3. 테스트 재실행
npm run test

# 4. 개발 서버 재시작
npm run dev
```

### 롤백 후 조치
1. Backend 라우터 정의 재확인
2. Trailing slash 정책 문서화
3. 대안 접근 방법 논의

---

## 참고 자료

### 관련 문서
- [SPEC-API-INTEGRATION-001 spec.md](./spec.md)
- [SPEC-API-INTEGRATION-001 plan.md](./plan.md)
- [FastAPI Path Operations Documentation](https://fastapi.tiangolo.com/tutorial/path-params/)
- [Axios Configuration Documentation](https://axios-http.com/docs/config_defaults)

### 관련 도구
- Chrome DevTools Network 탭
- Jest/Vitest 테스트 프레임워크
- ESLint 정적 분석
- Lighthouse 성능 감사

### 관련 SPEC
- @SPEC:API-001 (존재 시)
- @SPEC:FOUNDATION-001 (존재 시)
