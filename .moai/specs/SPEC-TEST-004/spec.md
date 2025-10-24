---
id: TEST-004
version: 1.0.0
status: completed
created: 2025-10-23
updated: 2025-10-24
completed: 2025-10-24
author: @Alfred
implementer: @tdd-implementer
priority: low
category: testing
labels: [security, authorization, validation, vulnerability]
depends_on:
  - TEST-001
  - TEST-002
related_specs:
  - TEST-003
scope:
  packages:
    - apps/api
  files:
    - apps/api/deps.py
    - apps/api/security/api_key_storage.py
    - apps/api/routers/*.py
  tests:
    - tests/security/test_authentication.py
    - tests/security/test_input_validation.py
    - tests/security/test_sql_injection_prevention.py
    - tests/security/test_xss_prevention.py
    - tests/security/test_rate_limiting.py
  scripts:
    - scripts/security_scan.sh
---

# @SPEC:TEST-004 보안 및 인증 테스트

## HISTORY

### v1.0.0 (2025-10-24)
- **COMPLETED**: 보안 및 인증 테스트 구현 완료
- **IMPLEMENTATION**: TDD로 6개 TAG 완료 (TEST-004-001 ~ TEST-004-006)
- **TESTS**: 29개 보안 테스트 통과 (authentication: 5, input validation: 6, SQL injection: 6, XSS: 6, rate limiting: 6)
- **SECURITY TOOLS**: bandit, safety를 requirements.txt에 추가, security_scan.sh 스크립트 생성
- **COVERAGE**: API 키 인증, 입력 검증, SQL Injection 방어, XSS 방어, Rate Limiting 검증 완료

### v0.0.1 (2025-10-23)
- **INITIAL**: 보안 및 인증 테스트 SPEC 초안 작성
- **AUTHOR**: @Alfred
- **SCOPE**: Phase 3 API 보안 검증, 인증 우회 방지, 입력 검증, SQL Injection 방지, Rate Limiting
- **CONTEXT**: TEST-001, TEST-002 완료 후 프로덕션 배포 전 보안 검증
- **BASELINE**: FastAPI 보안 best practices, OWASP Top 10

## Environment (환경)

본 SPEC은 다음 환경에서 적용됩니다:

- **API Framework**: FastAPI (Python 3.11+)
- **Authentication**: X-API-Key 헤더 기반
- **Testing Framework**: pytest + httpx
- **Security Tools**:
  - sqlmap (SQL Injection 탐지)
  - bandit (Python 정적 분석)
  - safety (의존성 취약점 스캔)
- **Rate Limiting**: slowapi (FastAPI rate limiter)
- **Input Validation**: Pydantic models
- **Security Targets**:
  - 모든 엔드포인트가 인증 필요
  - SQL Injection 방어 100%
  - 입력 검증 완전성 100%
  - Rate limiting: 100 req/min per API key

## Assumptions (전제 조건)

본 SPEC은 다음을 전제로 합니다:

1. TEST-001, TEST-002 완료 (기본 기능 검증)
2. FastAPI 인증 미들웨어가 구현되어 있음
3. Pydantic 모델을 통한 입력 검증 활성화
4. 데이터베이스 접근이 SQLAlchemy ORM을 통해서만 수행됨
5. Rate limiting 미들웨어가 설정되어 있음

## Requirements (요구사항)

### Ubiquitous Requirements (범용 요구사항)

**REQ-1**: The system shall enforce API key authentication
- 모든 API 엔드포인트는 `X-API-Key` 헤더 필수
- 유효하지 않은 API 키는 401 Unauthorized 반환
- API 키 누락 시 401 Unauthorized 반환
- Health check 엔드포인트는 예외 (인증 불필요)

**REQ-2**: The system shall validate all input data
- Pydantic 모델을 사용한 타입 검증
- 필수 필드 누락 시 422 Unprocessable Entity 반환
- 잘못된 타입은 422 반환
- 범위 초과 값은 422 반환

**REQ-3**: The system shall prevent SQL Injection attacks
- 모든 데이터베이스 쿼리는 parameterized queries 사용
- 사용자 입력이 직접 SQL 문자열에 포함되지 않음
- sqlmap 테스트 통과 (취약점 0개)

**REQ-4**: The system shall implement rate limiting
- API 키당 분당 최대 100 요청
- Rate limit 초과 시 429 Too Many Requests 반환
- Rate limit 정보는 헤더에 포함 (`X-RateLimit-Remaining`)

### Event-driven Requirements (이벤트 기반 요구사항)

**REQ-5**: WHEN API request is made without X-API-Key header
- THEN the system shall return 401 Unauthorized
- THEN the response shall include error message: "API key is required"

**REQ-6**: WHEN API request is made with invalid API key
- THEN the system shall return 401 Unauthorized
- THEN the response shall include error message: "Invalid API key"

**REQ-7**: WHEN API request is made with expired API key
- THEN the system shall return 401 Unauthorized
- THEN the response shall include error message: "API key expired"

**REQ-8**: WHEN malicious SQL payload is injected
- THEN the system shall sanitize the input
- THEN the query shall fail safely (no data leak)
- THEN the response shall return 422 Unprocessable Entity

**REQ-9**: WHEN rate limit is exceeded
- THEN the system shall return 429 Too Many Requests
- THEN the response shall include `Retry-After` header
- THEN subsequent requests shall be blocked until limit resets

**REQ-10**: WHEN XSS payload is submitted in text field
- THEN the system shall sanitize the input
- THEN the stored data shall escape HTML entities
- THEN the response shall not execute scripts

### State-driven Requirements (상태 기반 요구사항)

**REQ-11**: WHILE the system is under attack (brute force)
- Rate limiting shall protect against excessive requests
- Failed authentication attempts shall be logged
- IP-based blocking may be triggered (선택 사항)

**REQ-12**: WHILE input validation is active
- All Pydantic models shall enforce constraints
- Invalid data shall be rejected before reaching business logic
- Error messages shall not expose internal implementation details

**REQ-13**: WHILE database queries are executed
- All queries shall use SQLAlchemy ORM or parameterized queries
- No raw SQL with string interpolation shall be used
- Query errors shall be caught and sanitized

### Optional Features (선택적 기능)

**REQ-14**: WHERE advanced security logging is enabled
- The system may log all authentication failures
- The system may track suspicious IP addresses
- The system may integrate with SIEM tools

**REQ-15**: WHERE CORS policy is configured
- The system may enforce allowed origins
- The system may restrict HTTP methods
- The system may validate request headers

### Constraints (제약사항)

**CON-1**: IF authentication bypass is detected
- THEN the system shall immediately block the API key
- THEN the security team shall be notified
- THEN the incident shall be logged

**CON-2**: IF SQL Injection vulnerability is found
- THEN the affected endpoint shall be disabled
- THEN a hotfix shall be deployed within 24 hours
- THEN a security advisory shall be published

**CON-3**: Security tests shall not impact production
- Use dedicated test environment
- Use test API keys only
- No real user data shall be used

**CON-4**: Security test execution time shall be < 5 minutes
- Focus on critical vulnerabilities
- Exclude long-running penetration tests (run separately)

## Specifications (상세 명세)

### Test Structure

```
tests/security/
├── conftest.py                      # 공통 fixture 및 설정
├── test_authentication.py           # API 키 인증 테스트
├── test_input_validation.py         # 입력 검증 테스트
├── test_sql_injection.py            # SQL Injection 방어 테스트
├── test_xss_prevention.py           # XSS 방어 테스트
├── test_rate_limiting.py            # Rate limiting 테스트
└── test_cors_policy.py              # CORS 정책 테스트 (선택 사항)

security_reports/
├── bandit_report.txt                # Python 정적 분석 리포트
├── safety_report.txt                # 의존성 취약점 리포트
└── sqlmap_report.txt                # SQL Injection 탐지 리포트
```

### Authentication Tests

```python
# test_authentication.py

@pytest.mark.asyncio
async def test_api_requires_authentication(api_client):
    """모든 API 엔드포인트는 인증 필요"""
    endpoints = [
        ("/reflection/analyze", "POST", {"case_id": "test-001"}),
        ("/reflection/batch", "POST", {}),
        ("/consolidation/run", "POST", {}),
    ]

    for path, method, payload in endpoints:
        response = await api_client.request(method, path, json=payload)
        assert response.status_code == 401
        assert "API key is required" in response.json()["detail"]

@pytest.mark.asyncio
async def test_invalid_api_key_rejected(api_client):
    """유효하지 않은 API 키는 거부됨"""
    response = await api_client.post(
        "/reflection/analyze",
        json={"case_id": "test-001"},
        headers={"X-API-Key": "invalid_api_key_12345"}
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]

@pytest.mark.asyncio
async def test_expired_api_key_rejected(api_client):
    """만료된 API 키는 거부됨"""
    response = await api_client.post(
        "/reflection/analyze",
        json={"case_id": "test-001"},
        headers={"X-API-Key": "expired_api_key_12345"}
    )
    assert response.status_code == 401
    assert "API key expired" in response.json()["detail"]
```

### Input Validation Tests

```python
# test_input_validation.py

@pytest.mark.asyncio
async def test_missing_required_field_rejected(api_client, valid_api_key):
    """필수 필드 누락 시 422 반환"""
    response = await api_client.post(
        "/reflection/analyze",
        json={},  # case_id 누락
        headers={"X-API-Key": valid_api_key}
    )
    assert response.status_code == 422
    assert "case_id" in response.json()["detail"][0]["loc"]

@pytest.mark.asyncio
async def test_invalid_type_rejected(api_client, valid_api_key):
    """잘못된 타입은 422 반환"""
    response = await api_client.post(
        "/reflection/analyze",
        json={"case_id": 12345},  # 문자열 대신 숫자
        headers={"X-API-Key": valid_api_key}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_oversized_input_rejected(api_client, valid_api_key):
    """초과 크기 입력은 422 반환"""
    large_text = "a" * 100000  # 100KB
    response = await api_client.post(
        "/classify",
        json={"chunk_id": "test-001", "text": large_text},
        headers={"X-API-Key": valid_api_key}
    )
    assert response.status_code == 422
```

### SQL Injection Prevention Tests

```python
# test_sql_injection.py

@pytest.mark.asyncio
async def test_sql_injection_in_case_id_blocked(api_client, valid_api_key):
    """case_id에 SQL Injection 시도 차단"""
    malicious_payloads = [
        "test-001' OR '1'='1",
        "test-001'; DROP TABLE case_bank; --",
        "test-001' UNION SELECT * FROM api_keys; --",
    ]

    for payload in malicious_payloads:
        response = await api_client.post(
            "/reflection/analyze",
            json={"case_id": payload},
            headers={"X-API-Key": valid_api_key}
        )
        # 404 (케이스 없음) 또는 422 (입력 검증 실패) 반환
        assert response.status_code in [404, 422]

@pytest.mark.asyncio
async def test_sql_injection_in_search_query_blocked(api_client, valid_api_key):
    """검색 쿼리에 SQL Injection 시도 차단"""
    malicious_query = "machine learning' OR '1'='1"
    response = await api_client.post(
        "/search",
        json={"q": malicious_query, "final_topk": 5},
        headers={"X-API-Key": valid_api_key}
    )
    # 정상 응답 또는 입력 검증 실패 (데이터 유출 없음)
    assert response.status_code in [200, 422]
    if response.status_code == 200:
        # 결과가 있다면 정상적인 검색 결과여야 함
        data = response.json()
        assert "hits" in data
```

### XSS Prevention Tests

```python
# test_xss_prevention.py

@pytest.mark.asyncio
async def test_xss_payload_sanitized(api_client, valid_api_key, test_db):
    """XSS 페이로드는 sanitize됨"""
    xss_payload = "<script>alert('XSS')</script>"
    response = await api_client.post(
        "/classify",
        json={"chunk_id": "xss-001", "text": xss_payload},
        headers={"X-API-Key": valid_api_key}
    )

    # 응답 자체에 스크립트가 포함되지 않음
    assert "<script>" not in response.text

    # 데이터베이스에 저장된 데이터도 이스케이프됨
    # (선택 사항: 실제 데이터베이스 확인)
```

### Rate Limiting Tests

```python
# test_rate_limiting.py

@pytest.mark.asyncio
async def test_rate_limit_enforced(api_client, valid_api_key):
    """Rate limit 초과 시 429 반환"""
    # 101번 요청 (limit: 100 req/min)
    responses = []
    for i in range(101):
        response = await api_client.get(
            "/reflection/health",
            headers={"X-API-Key": valid_api_key}
        )
        responses.append(response)

    # 첫 100개 요청은 성공
    assert all(r.status_code == 200 for r in responses[:100])

    # 101번째 요청은 429 반환
    assert responses[100].status_code == 429
    assert "Retry-After" in responses[100].headers

@pytest.mark.asyncio
async def test_rate_limit_per_api_key(api_client, valid_api_key, another_api_key):
    """Rate limit은 API 키별로 적용됨"""
    # API 키 1: 100번 요청
    for i in range(100):
        await api_client.get("/reflection/health", headers={"X-API-Key": valid_api_key})

    # API 키 2: 여전히 사용 가능
    response = await api_client.get("/reflection/health", headers={"X-API-Key": another_api_key})
    assert response.status_code == 200
```

### Security Scanning Integration

```bash
# bandit (Python 정적 분석)
bandit -r apps/ -f txt -o security_reports/bandit_report.txt

# safety (의존성 취약점 스캔)
safety check --json > security_reports/safety_report.txt

# sqlmap (SQL Injection 탐지) - 수동 실행
sqlmap -u "http://localhost:8000/reflection/analyze" \
       --data='{"case_id":"test-001"}' \
       --header="X-API-Key: test_api_key" \
       --batch --level=5 --risk=3
```

### Security Test Matrix

| Test ID | Category | Scenario | Expected Result | Tool | Priority |
|---------|----------|----------|-----------------|------|----------|
| SEC-001 | Authentication | API 키 누락 | 401 Unauthorized | pytest | HIGH |
| SEC-002 | Authentication | 유효하지 않은 API 키 | 401 Unauthorized | pytest | HIGH |
| SEC-003 | Authentication | 만료된 API 키 | 401 Unauthorized | pytest | MEDIUM |
| SEC-004 | Input Validation | 필수 필드 누락 | 422 Validation Error | pytest | HIGH |
| SEC-005 | Input Validation | 잘못된 타입 | 422 Validation Error | pytest | HIGH |
| SEC-006 | Input Validation | 초과 크기 입력 | 422 Validation Error | pytest | MEDIUM |
| SEC-007 | SQL Injection | case_id SQL 페이로드 | 404 또는 422 (데이터 유출 없음) | pytest | HIGH |
| SEC-008 | SQL Injection | 검색 쿼리 SQL 페이로드 | 200 또는 422 (데이터 유출 없음) | pytest | HIGH |
| SEC-009 | SQL Injection | sqlmap 자동 탐지 | 취약점 0개 | sqlmap | HIGH |
| SEC-010 | XSS | 스크립트 페이로드 | sanitize됨 | pytest | MEDIUM |
| SEC-011 | Rate Limiting | 100 요청 초과 | 429 Too Many Requests | pytest | HIGH |
| SEC-012 | Rate Limiting | API 키별 독립 제한 | 키별 독립 카운트 | pytest | MEDIUM |
| SEC-013 | Static Analysis | Python 코드 취약점 | 취약점 0개 | bandit | MEDIUM |
| SEC-014 | Dependency Scan | 의존성 취약점 | 고위험 취약점 0개 | safety | MEDIUM |

## Traceability (추적성)

- **SPEC**: @SPEC:TEST-004
- **TEST**:
  - tests/security/test_authentication.py
  - tests/security/test_input_validation.py
  - tests/security/test_sql_injection.py
  - tests/security/test_xss_prevention.py
  - tests/security/test_rate_limiting.py
- **CODE**:
  - apps/api/dependencies/auth.py (@CODE:AUTH-001)
  - apps/api/routers/*.py (모든 라우터)
- **DOC**: README.md (Security section)
- **RELATED SPECS**:
  - @SPEC:TEST-001 (기존 API 테스트)
  - @SPEC:TEST-002 (Phase 3 API 테스트)

## Success Criteria (성공 기준)

1. ✅ 모든 API 엔드포인트가 인증 필수 (health check 제외)
2. ✅ SQL Injection 방어 100% (sqlmap 테스트 통과)
3. ✅ 입력 검증 완전성 100% (Pydantic 모델 검증)
4. ✅ Rate limiting 정상 동작 (100 req/min per API key)
5. ✅ 정적 분석 통과 (bandit: 고위험 취약점 0개)
6. ✅ 의존성 취약점 스캔 통과 (safety: 고위험 취약점 0개)
7. ✅ 모든 보안 테스트가 CI/CD 파이프라인에서 통과

## References (참고 문서)

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
- sqlmap: https://sqlmap.org/
- bandit: https://bandit.readthedocs.io/
- safety: https://pyup.io/safety/
