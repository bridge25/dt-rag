# SPEC-TEST-004 Implementation Plan
# 보안 및 인증 테스트

## Overview

본 계획서는 SPEC-TEST-004 (보안 및 인증 테스트)의 구현 계획을 정의합니다. Phase 3 API의 보안 검증, 인증 우회 방지, 입력 검증, SQL Injection 방어, Rate limiting을 테스트하여 프로덕션 배포 전 보안 준비를 완료합니다.

---

## Work Breakdown Structure (작업 분해)

### Phase 1: 보안 테스트 환경 구성 (Priority: HIGH)

#### Task 1.1: pytest 보안 테스트 환경 설정
- **Description**: 보안 테스트 전용 fixture 및 헬퍼 함수 구성
- **Deliverables**:
  - `tests/security/conftest.py` 작성
  - 유효/무효 API 키 fixture 생성
  - 악의적 페이로드 리스트 정의
- **Dependencies**: 없음
- **Estimated Effort**: 낮음

#### Task 1.2: 보안 스캔 도구 설치 및 설정
- **Description**: bandit, safety, sqlmap 설치 및 설정
- **Deliverables**:
  - `bandit` 설치 및 설정 파일 작성 (`.bandit`)
  - `safety` 설치
  - `sqlmap` 설치 (선택 사항: Docker 이미지 사용)
- **Dependencies**: 없음
- **Estimated Effort**: 낮음

#### Task 1.3: 보안 리포트 디렉토리 생성
- **Description**: 보안 스캔 결과 저장 경로 설정
- **Deliverables**:
  - `security_reports/` 디렉토리 생성
  - `.gitignore`에 보안 리포트 제외 추가
- **Dependencies**: 없음
- **Estimated Effort**: 낮음

---

### Phase 2: 인증 테스트 작성 (Priority: HIGH)

#### Task 2.1: API 키 인증 필수 테스트
- **Description**: 모든 엔드포인트가 인증을 요구하는지 검증
- **Test Cases**:
  - `test_api_requires_authentication`: 모든 API 엔드포인트 인증 필수
  - `test_health_endpoint_public`: Health check는 인증 불필요
- **Dependencies**: Phase 1 완료
- **Estimated Effort**: 낮음

#### Task 2.2: 유효하지 않은 API 키 테스트
- **Description**: 잘못된 API 키는 거부되는지 검증
- **Test Cases**:
  - `test_invalid_api_key_rejected`: 유효하지 않은 API 키 401 반환
  - `test_empty_api_key_rejected`: 빈 API 키 401 반환
  - `test_malformed_api_key_rejected`: 형식 오류 API 키 401 반환
- **Dependencies**: Task 2.1
- **Estimated Effort**: 낮음

#### Task 2.3: 만료된 API 키 테스트 (선택 사항)
- **Description**: 만료된 API 키는 거부되는지 검증
- **Test Cases**:
  - `test_expired_api_key_rejected`: 만료된 API 키 401 반환
- **Dependencies**: Task 2.2
- **Estimated Effort**: 낮음 (API 키 만료 기능이 구현된 경우)

---

### Phase 3: 입력 검증 테스트 작성 (Priority: HIGH)

#### Task 3.1: 필수 필드 검증 테스트
- **Description**: 필수 필드 누락 시 422 반환 검증
- **Test Cases**:
  - `test_missing_case_id_rejected`: case_id 누락 시 422 반환
  - `test_missing_query_rejected`: 검색 쿼리 누락 시 422 반환
  - `test_missing_text_rejected`: 분류 텍스트 누락 시 422 반환
- **Dependencies**: Phase 2 완료
- **Estimated Effort**: 낮음

#### Task 3.2: 타입 검증 테스트
- **Description**: 잘못된 타입은 422 반환 검증
- **Test Cases**:
  - `test_invalid_type_case_id`: case_id에 숫자 전달 시 422 반환
  - `test_invalid_type_final_topk`: final_topk에 문자열 전달 시 422 반환
- **Dependencies**: Task 3.1
- **Estimated Effort**: 낮음

#### Task 3.3: 범위 및 크기 검증 테스트
- **Description**: 초과 크기 또는 범위 외 값은 422 반환 검증
- **Test Cases**:
  - `test_oversized_input_rejected`: 100KB 초과 텍스트 422 반환
  - `test_negative_topk_rejected`: final_topk < 0 시 422 반환
  - `test_excessive_topk_rejected`: final_topk > 1000 시 422 반환
- **Dependencies**: Task 3.2
- **Estimated Effort**: 낮음

---

### Phase 4: SQL Injection 방어 테스트 (Priority: HIGH)

#### Task 4.1: case_id SQL Injection 테스트
- **Description**: case_id에 SQL Injection 시도 차단 검증
- **Test Cases**:
  - `test_sql_injection_in_case_id_blocked`: SQL 페이로드 차단
  - Payload 예: `' OR '1'='1`, `'; DROP TABLE; --`, `' UNION SELECT * FROM api_keys; --`
- **Dependencies**: Phase 3 완료
- **Estimated Effort**: 중간

#### Task 4.2: 검색 쿼리 SQL Injection 테스트
- **Description**: 검색 쿼리에 SQL Injection 시도 차단 검증
- **Test Cases**:
  - `test_sql_injection_in_search_query_blocked`: SQL 페이로드 차단
- **Dependencies**: Task 4.1
- **Estimated Effort**: 중간

#### Task 4.3: sqlmap 자동 스캔 (선택 사항)
- **Description**: sqlmap을 사용한 자동 SQL Injection 탐지
- **Deliverables**:
  - sqlmap 스크립트 작성
  - `security_reports/sqlmap_report.txt` 생성
- **Dependencies**: Task 4.2
- **Estimated Effort**: 중간 (수동 실행)

---

### Phase 5: XSS 방어 테스트 (Priority: MEDIUM)

#### Task 5.1: XSS 페이로드 sanitization 테스트
- **Description**: XSS 페이로드가 sanitize되는지 검증
- **Test Cases**:
  - `test_xss_payload_sanitized`: `<script>alert('XSS')</script>` sanitize됨
  - `test_xss_in_response_escaped`: 응답에 스크립트 태그 없음
- **Dependencies**: Phase 4 완료
- **Estimated Effort**: 낮음

#### Task 5.2: HTML 엔티티 이스케이프 검증 (선택 사항)
- **Description**: 데이터베이스에 저장된 데이터도 이스케이프되는지 검증
- **Test Cases**:
  - `test_xss_stored_data_escaped`: DB에 저장된 데이터 이스케이프 확인
- **Dependencies**: Task 5.1
- **Estimated Effort**: 낮음

---

### Phase 6: Rate Limiting 테스트 (Priority: MEDIUM)

#### Task 6.1: Rate limit 기본 동작 테스트
- **Description**: Rate limit 초과 시 429 반환 검증
- **Test Cases**:
  - `test_rate_limit_enforced`: 100 요청 초과 시 429 반환
  - `test_rate_limit_retry_after_header`: Retry-After 헤더 포함 확인
- **Dependencies**: Phase 5 완료
- **Estimated Effort**: 중간

#### Task 6.2: API 키별 독립 Rate limit 테스트
- **Description**: Rate limit이 API 키별로 독립적으로 적용되는지 검증
- **Test Cases**:
  - `test_rate_limit_per_api_key`: API 키 1 차단되어도 API 키 2 사용 가능
- **Dependencies**: Task 6.1
- **Estimated Effort**: 낮음

#### Task 6.3: Rate limit 리셋 테스트 (선택 사항)
- **Description**: Rate limit이 1분 후 리셋되는지 검증
- **Test Cases**:
  - `test_rate_limit_resets_after_1_minute`: 1분 후 다시 사용 가능
- **Dependencies**: Task 6.2
- **Estimated Effort**: 중간 (시간 대기 필요)

---

### Phase 7: 정적 분석 및 의존성 스캔 (Priority: LOW)

#### Task 7.1: bandit 정적 분석
- **Description**: Python 코드 취약점 스캔
- **Deliverables**:
  - `bandit -r apps/ -f txt -o security_reports/bandit_report.txt` 실행
  - 고위험 취약점 0개 확인
- **Dependencies**: Phase 6 완료
- **Estimated Effort**: 낮음

#### Task 7.2: safety 의존성 스캔
- **Description**: Python 의존성 취약점 스캔
- **Deliverables**:
  - `safety check --json > security_reports/safety_report.txt` 실행
  - 고위험 취약점 0개 확인
- **Dependencies**: Task 7.1
- **Estimated Effort**: 낮음

#### Task 7.3: CI/CD 파이프라인 통합
- **Description**: 보안 스캔을 GitHub Actions에 통합
- **Deliverables**:
  - `.github/workflows/security.yml` 작성
  - bandit, safety 자동 실행
  - 취약점 발견 시 PR 블로킹
- **Dependencies**: Task 7.2
- **Estimated Effort**: 중간

---

## Dependencies (의존성)

### 외부 의존성
- **SPEC-TEST-001**: 기존 API 테스트 패턴
- **SPEC-TEST-002**: Phase 3 API 인증 구현

### 내부 의존성
- **Phase 1 → Phase 2**: 테스트 환경 없이 인증 테스트 불가
- **Phase 2 → Phase 3**: 인증 통과 후 입력 검증 테스트 가능
- **Phase 3 → Phase 4**: 입력 검증 패턴을 SQL Injection 테스트에 재사용
- **Phase 4 → Phase 5**: SQL Injection 패턴을 XSS 테스트에 재사용
- **Phase 5 → Phase 6**: Rate limiting은 독립적으로 테스트 가능
- **Phase 6 → Phase 7**: 모든 기능 테스트 완료 후 정적 분석

### 기술 의존성
- **pytest**: ^7.4.0
- **httpx**: ^0.24.0
- **bandit**: ^1.7.5
- **safety**: ^2.3.5
- **sqlmap**: (선택 사항, Docker 이미지 사용 권장)

---

## Risk Assessment (위험 요소)

### Risk 1: SQL Injection 취약점 발견
- **Probability**: Low
- **Impact**: Critical
- **Mitigation**:
  - SQLAlchemy ORM 사용 강제
  - 모든 쿼리에 대해 parameterized queries 적용
  - sqlmap 자동 스캔으로 사전 탐지

### Risk 2: Rate Limiting 우회 가능성
- **Probability**: Medium
- **Impact**: Medium
- **Mitigation**:
  - API 키별 독립 제한 검증
  - IP 기반 추가 제한 검토 (선택 사항)

### Risk 3: XSS 취약점 (낮은 위험)
- **Probability**: Low
- **Impact**: Medium
- **Mitigation**:
  - Pydantic 모델을 통한 타입 검증
  - HTML 엔티티 이스케이프 자동화

### Risk 4: 의존성 취약점
- **Probability**: Medium
- **Impact**: Medium
- **Mitigation**:
  - safety 정기 스캔 (주간 배치)
  - Dependabot 자동 업데이트 활성화

---

## Resource Requirements (리소스 요구사항)

### 개발 리소스
- **Security Engineer**: 1명
- **Backend Developer**: 0.5명 (보안 패치 지원)

### 인프라 리소스
- **Test Environment**: 격리된 테스트 환경
- **Security Tools**: bandit, safety (Python 패키지)
- **sqlmap**: Docker 이미지 (선택 사항)

### 시간 리소스
- **Phase 1**: 0.5일
- **Phase 2**: 1일
- **Phase 3**: 1일
- **Phase 4**: 1-2일
- **Phase 5**: 0.5일
- **Phase 6**: 1일
- **Phase 7**: 1일
- **Total**: 6-7일

---

## Architecture Decisions (아키텍처 결정)

### Decision 1: SQLAlchemy ORM vs Raw SQL
- **Choice**: SQLAlchemy ORM (parameterized queries 강제)
- **Rationale**:
  - SQL Injection 방어 자동화
  - 타입 안정성 향상
  - 유지보수성 개선

### Decision 2: X-API-Key vs JWT
- **Choice**: X-API-Key (현재 구현 유지)
- **Rationale**:
  - 간단한 구현
  - 프로덕션 환경에 적합
  - JWT는 향후 확장 시 고려

### Decision 3: Rate Limiting 방식
- **Choice**: slowapi (FastAPI 전용)
- **Rationale**:
  - FastAPI 네이티브 지원
  - 간단한 설정
  - API 키별 독립 제한 가능

---

## Technical Approach (기술적 접근법)

### 인증 테스트 패턴
```python
@pytest.mark.asyncio
async def test_api_requires_authentication(api_client):
    response = await api_client.post("/reflection/analyze", json={"case_id": "test-001"})
    assert response.status_code == 401
    assert "API key is required" in response.json()["detail"]
```

### SQL Injection 테스트 패턴
```python
@pytest.mark.asyncio
async def test_sql_injection_in_case_id_blocked(api_client, valid_api_key):
    malicious_payloads = [
        "test-001' OR '1'='1",
        "test-001'; DROP TABLE case_bank; --",
    ]
    for payload in malicious_payloads:
        response = await api_client.post(
            "/reflection/analyze",
            json={"case_id": payload},
            headers={"X-API-Key": valid_api_key}
        )
        assert response.status_code in [404, 422]  # 데이터 유출 없음
```

### Rate Limiting 테스트 패턴
```python
@pytest.mark.asyncio
async def test_rate_limit_enforced(api_client, valid_api_key):
    responses = []
    for i in range(101):
        response = await api_client.get("/reflection/health", headers={"X-API-Key": valid_api_key})
        responses.append(response)

    assert all(r.status_code == 200 for r in responses[:100])
    assert responses[100].status_code == 429
```

---

## Success Metrics (성공 지표)

### 정량적 지표
- **인증 테스트**: 10개 테스트 작성 및 통과
- **입력 검증**: 8개 테스트 작성 및 통과
- **SQL Injection**: 6개 테스트 작성 및 통과
- **Rate Limiting**: 4개 테스트 작성 및 통과
- **정적 분석**: bandit 고위험 취약점 0개
- **의존성 스캔**: safety 고위험 취약점 0개

### 정성적 지표
- **보안 정책 준수**: OWASP Top 10 기준 준수
- **문서화**: 보안 테스트 가이드 작성
- **CI/CD 통합**: 자동화된 보안 스캔 파이프라인 구축

---

## Next Steps (다음 단계)

1. **Phase 1 시작**: 보안 테스트 환경 구성
2. **프로덕션 배포 준비**: 모든 보안 테스트 통과 후 배포 승인
3. **정기 보안 스캔**: 주간 배치로 bandit, safety 자동 실행

---

**Document Version**: 1.0
**Last Updated**: 2025-10-23
**Author**: @Alfred
