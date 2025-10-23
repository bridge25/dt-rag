# SPEC-TEST-004 Acceptance Criteria
# 보안 및 인증 테스트

## Overview

본 문서는 SPEC-TEST-004의 완료 조건을 정의합니다. Phase 3 API의 보안 검증, 인증 우회 방지, 입력 검증, SQL Injection 방어, Rate limiting이 완료되고, 모든 보안 기준이 충족되어야 합니다.

---

## Given-When-Then Scenarios

### Scenario 1: API 키 인증 필수

**Given**:
- FastAPI 서버가 정상 실행 중
- 인증 미들웨어가 활성화되어 있음

**When**:
- X-API-Key 헤더 없이 POST /reflection/analyze 호출

**Then**:
- 응답 상태 코드는 401 Unauthorized
- 응답 JSON에 다음 필드 포함:
  - `detail`: "API key is required"

---

### Scenario 2: 유효하지 않은 API 키 거부

**Given**:
- FastAPI 서버가 정상 실행 중
- 유효하지 않은 API 키: `invalid_api_key_12345`

**When**:
- POST /reflection/analyze 호출 (X-API-Key: invalid_api_key_12345)

**Then**:
- 응답 상태 코드는 401 Unauthorized
- 응답 JSON에 다음 필드 포함:
  - `detail`: "Invalid API key"

---

### Scenario 3: Health Check는 인증 불필요

**Given**:
- FastAPI 서버가 정상 실행 중

**When**:
- X-API-Key 헤더 없이 GET /reflection/health 호출

**Then**:
- 응답 상태 코드는 200 OK
- 응답 JSON에 다음 필드 포함:
  - `status`: "healthy"

---

### Scenario 4: 필수 필드 누락 시 422 반환

**Given**:
- 유효한 API 키가 있음

**When**:
- POST /reflection/analyze 호출 (case_id 필드 누락)

**Then**:
- 응답 상태 코드는 422 Unprocessable Entity
- 응답 JSON에 다음 필드 포함:
  - `detail[0].loc`: ["body", "case_id"]
  - `detail[0].msg`: "field required"

---

### Scenario 5: 잘못된 타입 거부

**Given**:
- 유효한 API 키가 있음

**When**:
- POST /reflection/analyze 호출 (case_id: 12345, 문자열 대신 숫자)

**Then**:
- 응답 상태 코드는 422 Unprocessable Entity
- 응답 JSON에 타입 오류 메시지 포함

---

### Scenario 6: 초과 크기 입력 거부

**Given**:
- 유효한 API 키가 있음
- 100KB 크기의 텍스트 입력

**When**:
- POST /classify 호출 (text: 100KB 텍스트)

**Then**:
- 응답 상태 코드는 422 Unprocessable Entity
- 응답 JSON에 크기 제한 오류 메시지 포함

---

### Scenario 7: SQL Injection 방어 - case_id

**Given**:
- 유효한 API 키가 있음
- 악의적 SQL 페이로드: `"test-001' OR '1'='1"`

**When**:
- POST /reflection/analyze 호출 (case_id: `"test-001' OR '1'='1"`)

**Then**:
- 응답 상태 코드는 404 Not Found 또는 422 Unprocessable Entity
- 데이터 유출 없음 (API 키, 민감 정보 노출 없음)

---

### Scenario 8: SQL Injection 방어 - 검색 쿼리

**Given**:
- 유효한 API 키가 있음
- 악의적 SQL 페이로드: `"machine learning' OR '1'='1"`

**When**:
- POST /search 호출 (q: `"machine learning' OR '1'='1"`)

**Then**:
- 응답 상태 코드는 200 OK 또는 422 Unprocessable Entity
- 200 OK인 경우: 정상 검색 결과 반환 (SQL Injection 실행되지 않음)
- 데이터 유출 없음

---

### Scenario 9: XSS 방어 - 스크립트 페이로드

**Given**:
- 유효한 API 키가 있음
- XSS 페이로드: `"<script>alert('XSS')</script>"`

**When**:
- POST /classify 호출 (text: `"<script>alert('XSS')</script>"`)

**Then**:
- 응답 상태 코드는 200 OK 또는 422 Unprocessable Entity
- 응답 JSON에 `<script>` 태그 없음 (sanitize됨)
- 데이터베이스에 저장된 데이터도 이스케이프됨 (선택 사항)

---

### Scenario 10: Rate Limiting - 100 요청 초과

**Given**:
- 유효한 API 키가 있음
- Rate limit: 100 req/min per API key

**When**:
- GET /reflection/health 101번 연속 호출

**Then**:
- 첫 100개 요청: 200 OK
- 101번째 요청: 429 Too Many Requests
- 응답 헤더에 다음 필드 포함:
  - `Retry-After`: 60 (초 단위)
  - `X-RateLimit-Remaining`: 0

---

### Scenario 11: Rate Limiting - API 키별 독립 제한

**Given**:
- 유효한 API 키 2개: `api_key_1`, `api_key_2`
- API 키 1로 100번 요청 완료

**When**:
- API 키 2로 GET /reflection/health 호출

**Then**:
- 응답 상태 코드는 200 OK
- API 키 2의 Rate limit은 독립적으로 적용됨

---

### Scenario 12: bandit 정적 분석 - 고위험 취약점 없음

**Given**:
- `apps/` 디렉토리에 Python 코드가 있음

**When**:
- `bandit -r apps/ -f txt -o security_reports/bandit_report.txt` 실행

**Then**:
- 고위험 취약점 (Severity: HIGH) 0개
- 중위험 취약점 (Severity: MEDIUM) < 5개
- 리포트가 `security_reports/bandit_report.txt`에 저장됨

---

### Scenario 13: safety 의존성 스캔 - 고위험 취약점 없음

**Given**:
- `requirements.txt`에 Python 의존성이 정의되어 있음

**When**:
- `safety check --json > security_reports/safety_report.txt` 실행

**Then**:
- 고위험 취약점 (Severity: HIGH) 0개
- 중위험 취약점 (Severity: MEDIUM) < 3개
- 리포트가 `security_reports/safety_report.txt`에 저장됨

---

### Scenario 14: sqlmap 자동 스캔 - SQL Injection 취약점 없음 (선택 사항)

**Given**:
- FastAPI 서버가 정상 실행 중
- sqlmap이 설치되어 있음

**When**:
- `sqlmap -u "http://localhost:8000/reflection/analyze" --data='{"case_id":"test-001"}' --header="X-API-Key: test_api_key" --batch --level=5 --risk=3` 실행

**Then**:
- SQL Injection 취약점 0개 탐지
- 모든 엔드포인트가 parameterized queries 사용 확인

---

## Test Case Matrix

### Authentication Tests (10개)

| Test ID | Scenario | Expected Status | Expected Message | Priority |
|---------|----------|-----------------|------------------|----------|
| AUTH-001 | API 키 누락 (POST /reflection/analyze) | 401 | "API key is required" | HIGH |
| AUTH-002 | API 키 누락 (POST /reflection/batch) | 401 | "API key is required" | HIGH |
| AUTH-003 | API 키 누락 (POST /consolidation/run) | 401 | "API key is required" | HIGH |
| AUTH-004 | 유효하지 않은 API 키 | 401 | "Invalid API key" | HIGH |
| AUTH-005 | 빈 API 키 | 401 | "API key is required" | MEDIUM |
| AUTH-006 | 형식 오류 API 키 | 401 | "Invalid API key" | MEDIUM |
| AUTH-007 | 만료된 API 키 (선택 사항) | 401 | "API key expired" | MEDIUM |
| AUTH-008 | Health check 인증 불필요 | 200 | N/A | HIGH |
| AUTH-009 | Consolidation health 인증 불필요 | 200 | N/A | MEDIUM |
| AUTH-010 | Taxonomy endpoint 인증 불필요 | 200 | N/A | LOW |

### Input Validation Tests (8개)

| Test ID | Scenario | Expected Status | Error Location | Priority |
|---------|----------|-----------------|----------------|----------|
| VAL-001 | case_id 필드 누락 | 422 | ["body", "case_id"] | HIGH |
| VAL-002 | query 필드 누락 (search) | 422 | ["body", "q"] | HIGH |
| VAL-003 | text 필드 누락 (classify) | 422 | ["body", "text"] | HIGH |
| VAL-004 | case_id 잘못된 타입 (숫자) | 422 | ["body", "case_id"] | HIGH |
| VAL-005 | final_topk 잘못된 타입 (문자열) | 422 | ["body", "final_topk"] | MEDIUM |
| VAL-006 | 초과 크기 텍스트 (100KB) | 422 | ["body", "text"] | MEDIUM |
| VAL-007 | 음수 final_topk | 422 | ["body", "final_topk"] | MEDIUM |
| VAL-008 | 초과 final_topk (> 1000) | 422 | ["body", "final_topk"] | LOW |

### SQL Injection Prevention Tests (6개)

| Test ID | Scenario | Malicious Payload | Expected Status | Priority |
|---------|----------|-------------------|-----------------|----------|
| SQL-001 | case_id SQL 페이로드 1 | `' OR '1'='1` | 404 또는 422 | HIGH |
| SQL-002 | case_id SQL 페이로드 2 | `'; DROP TABLE case_bank; --` | 404 또는 422 | HIGH |
| SQL-003 | case_id SQL 페이로드 3 | `' UNION SELECT * FROM api_keys; --` | 404 또는 422 | HIGH |
| SQL-004 | 검색 쿼리 SQL 페이로드 | `machine learning' OR '1'='1` | 200 또는 422 | HIGH |
| SQL-005 | sqlmap 자동 스캔 (선택 사항) | N/A | 취약점 0개 | MEDIUM |
| SQL-006 | Raw SQL 사용 금지 검증 | N/A | 코드 리뷰 통과 | LOW |

### XSS Prevention Tests (4개)

| Test ID | Scenario | XSS Payload | Expected Result | Priority |
|---------|----------|-------------|-----------------|----------|
| XSS-001 | 스크립트 페이로드 | `<script>alert('XSS')</script>` | sanitize됨 | MEDIUM |
| XSS-002 | 이미지 태그 XSS | `<img src=x onerror=alert('XSS')>` | sanitize됨 | MEDIUM |
| XSS-003 | 응답에 스크립트 없음 | `<script>alert('XSS')</script>` | `<script>` 태그 없음 | MEDIUM |
| XSS-004 | DB 저장 데이터 이스케이프 | `<script>alert('XSS')</script>` | HTML 엔티티 이스케이프 | LOW |

### Rate Limiting Tests (4개)

| Test ID | Scenario | Requests | Expected Result | Priority |
|---------|----------|----------|-----------------|----------|
| RATE-001 | 100 요청 초과 | 101 | 101번째 요청 429 반환 | HIGH |
| RATE-002 | Retry-After 헤더 | 101 | `Retry-After: 60` 포함 | HIGH |
| RATE-003 | API 키별 독립 제한 | 100 (키1) + 1 (키2) | 키2는 200 OK | MEDIUM |
| RATE-004 | Rate limit 리셋 (선택 사항) | 101 + wait 1m + 1 | 리셋 후 200 OK | LOW |

### Security Scanning (2개)

| Test ID | Tool | Target | Expected Result | Priority |
|---------|------|--------|-----------------|----------|
| SCAN-001 | bandit | `apps/` | 고위험 취약점 0개 | MEDIUM |
| SCAN-002 | safety | `requirements.txt` | 고위험 취약점 0개 | MEDIUM |

---

## Definition of Done (완료 조건)

### Authentication (인증)

- [ ] 10개 인증 테스트 작성 완료
- [ ] 모든 API 엔드포인트가 인증 필수 (health check 제외)
- [ ] 유효하지 않은 API 키 거부 검증
- [ ] 401 Unauthorized 응답 포맷 일관성 확인

### Input Validation (입력 검증)

- [ ] 8개 입력 검증 테스트 작성 완료
- [ ] Pydantic 모델 기반 타입 검증 100%
- [ ] 필수 필드 누락 시 422 반환 검증
- [ ] 잘못된 타입 및 초과 크기 입력 거부 검증

### SQL Injection Prevention (SQL Injection 방어)

- [ ] 6개 SQL Injection 테스트 작성 완료
- [ ] 모든 악의적 SQL 페이로드 차단 확인
- [ ] SQLAlchemy ORM 또는 parameterized queries 사용 검증
- [ ] sqlmap 자동 스캔 통과 (선택 사항)
- [ ] 데이터 유출 없음 확인

### XSS Prevention (XSS 방어)

- [ ] 4개 XSS 방어 테스트 작성 완료
- [ ] 모든 스크립트 페이로드 sanitize 확인
- [ ] 응답에 `<script>` 태그 없음 검증
- [ ] 데이터베이스 저장 데이터 이스케이프 확인 (선택 사항)

### Rate Limiting (Rate Limiting)

- [ ] 4개 Rate Limiting 테스트 작성 완료
- [ ] 100 req/min per API key 제한 검증
- [ ] 429 Too Many Requests 응답 확인
- [ ] API 키별 독립 제한 검증
- [ ] Retry-After 헤더 포함 확인

### Security Scanning (보안 스캔)

- [ ] bandit 정적 분석 실행 완료
- [ ] safety 의존성 스캔 실행 완료
- [ ] 고위험 취약점 0개 확인
- [ ] 보안 리포트 자동 생성 (`security_reports/`)

### CI/CD Integration (CI/CD 통합)

- [ ] GitHub Actions 보안 워크플로우 작성
- [ ] 보안 테스트 자동 실행
- [ ] 취약점 발견 시 PR 블로킹
- [ ] 보안 리포트 자동 저장 (artifacts)

### Documentation (문서화)

- [ ] 보안 테스트 실행 가이드 작성
- [ ] 보안 정책 문서화 (OWASP Top 10 준수)
- [ ] 취약점 대응 프로세스 정의
- [ ] 보안 테스트 트러블슈팅 가이드

---

## Verification Checklist (검증 체크리스트)

### Pre-Acceptance Testing (수락 전 테스트)

1. **로컬 보안 테스트**
   - [ ] `pytest tests/security/ -v` 통과
   - [ ] 모든 테스트가 5분 이내에 완료
   - [ ] 0개 테스트 실패

2. **정적 분석**
   - [ ] `bandit -r apps/` 실행 → 고위험 취약점 0개
   - [ ] `safety check` 실행 → 고위험 취약점 0개
   - [ ] 리포트 파일 생성 확인

3. **SQL Injection 방어**
   - [ ] 모든 SQL 페이로드 테스트 통과
   - [ ] sqlmap 자동 스캔 통과 (선택 사항)
   - [ ] 데이터 유출 없음 검증

4. **Rate Limiting**
   - [ ] 100 요청 초과 시 429 반환 검증
   - [ ] API 키별 독립 제한 검증
   - [ ] Retry-After 헤더 포함 확인

5. **CI/CD 파이프라인 검증**
   - [ ] GitHub Actions 워크플로우 실행 성공
   - [ ] 보안 스캔 자동 실행
   - [ ] 취약점 발견 시 PR 블로킹 확인

---

## Security Standards Compliance (보안 표준 준수)

### OWASP Top 10 Coverage

| OWASP Category | Coverage | Tests |
|----------------|----------|-------|
| A01: Broken Access Control | ✅ | AUTH-001 ~ AUTH-010 |
| A02: Cryptographic Failures | ⭕ (별도 SPEC 필요) | N/A |
| A03: Injection | ✅ | SQL-001 ~ SQL-006 |
| A04: Insecure Design | ✅ | 입력 검증, Rate Limiting |
| A05: Security Misconfiguration | ✅ | bandit, safety |
| A06: Vulnerable Components | ✅ | SCAN-002 (safety) |
| A07: Authentication Failures | ✅ | AUTH-001 ~ AUTH-007 |
| A08: Software and Data Integrity | ⭕ (별도 SPEC 필요) | N/A |
| A09: Security Logging Failures | ⭕ (별도 SPEC 필요) | N/A |
| A10: Server-Side Request Forgery (SSRF) | ⭕ (해당 없음) | N/A |

---

## Acceptance Criteria Summary (수락 기준 요약)

### Must Have (필수)
✅ 모든 API 엔드포인트 인증 필수 (health check 제외)
✅ SQL Injection 방어 100%
✅ 입력 검증 완전성 100%
✅ Rate limiting 정상 동작
✅ bandit, safety 고위험 취약점 0개

### Should Have (권장)
✅ XSS 방어 테스트
✅ sqlmap 자동 스캔 통과
✅ CI/CD 보안 워크플로우 통합

### Could Have (선택)
⭕ CORS 정책 테스트
⭕ IP 기반 Rate limiting
⭕ SIEM 통합

---

## Sign-off (승인)

### Stakeholders (이해관계자)
- **Security Engineer**: 보안 테스트 결과 승인
- **Tech Lead**: 보안 정책 준수 확인
- **DevOps Engineer**: CI/CD 보안 파이프라인 승인

### Approval Checklist
- [ ] 모든 수락 기준 충족
- [ ] OWASP Top 10 주요 항목 준수
- [ ] 고위험 취약점 0개
- [ ] CI/CD 통합 완료

---

**Document Version**: 1.0
**Last Updated**: 2025-10-23
**Author**: @Alfred
