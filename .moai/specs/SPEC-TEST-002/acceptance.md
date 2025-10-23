# SPEC-TEST-002 Acceptance Criteria
# Phase 3 API 엔드포인트 통합 테스트

## Overview

본 문서는 SPEC-TEST-002의 완료 조건을 정의합니다. 24개 통합 테스트가 작성되고, 95% 커버리지가 달성되며, 모든 성능 SLA가 충족되어야 합니다.

---

## Given-When-Then Scenarios

### Scenario 1: Reflection Analyze API 테스트

**Given**:
- Docker PostgreSQL 테스트 환경이 구성되어 있음
- CaseBank에 `test-001` 케이스가 존재함 (success_rate: 85.0)
- ExecutionLog에 100건의 실행 로그가 있음

**When**:
- POST /reflection/analyze 호출 (case_id: "test-001", API 키 포함)

**Then**:
- 응답 상태 코드는 200 OK
- 응답 시간은 1초 미만
- 응답 JSON에 다음 필드 포함:
  - `case_id`: "test-001"
  - `success_rate`: 85.0
  - `total_executions`: 100
  - `common_errors`: []
  - `avg_execution_time_ms`: 양수 값

---

### Scenario 2: Reflection Analyze API - 존재하지 않는 케이스

**Given**:
- CaseBank에 `nonexistent-case` 케이스가 없음

**When**:
- POST /reflection/analyze 호출 (case_id: "nonexistent-case")

**Then**:
- 응답 상태 코드는 404 Not Found
- 응답 JSON에 다음 필드 포함:
  - `detail`: "Case not found: nonexistent-case"

---

### Scenario 3: Reflection Analyze API - 인증 누락

**Given**:
- API 키 없이 요청

**When**:
- POST /reflection/analyze 호출 (X-API-Key 헤더 없음)

**Then**:
- 응답 상태 코드는 401 Unauthorized
- 응답 JSON에 다음 필드 포함:
  - `detail`: "API key is required"

---

### Scenario 4: Reflection Batch API - 전체 케이스 분석

**Given**:
- CaseBank에 50개의 active 케이스가 있음
- 각 케이스에 100건 이상의 ExecutionLog 존재

**When**:
- POST /reflection/batch 호출

**Then**:
- 응답 상태 코드는 200 OK
- 응답 시간은 10초 미만
- 응답 JSON에 다음 필드 포함:
  - `analyzed_cases`: 50
  - `low_performance_cases`: ≥ 0
  - `suggestions`: List[Dict]

---

### Scenario 5: Reflection Batch API - 성능 SLA

**Given**:
- CaseBank에 100개의 active 케이스가 있음

**When**:
- POST /reflection/batch 호출

**Then**:
- P95 응답 시간 < 10초
- 모든 케이스의 success_rate가 업데이트됨
- 저성능 케이스(success_rate < 50%)에 대해 개선 제안 생성됨

---

### Scenario 6: Consolidation Run API - 실행 모드

**Given**:
- CaseBank에 다음 케이스들이 있음:
  - `low-perf-001`: success_rate 25%, usage_count 15 (제거 대상)
  - `duplicate-001`: query_vector 유사도 > 95% (병합 대상)
  - `inactive-001`: last_accessed_at > 90일 (아카이빙 대상)

**When**:
- POST /consolidation/run 호출 (dry_run: false)

**Then**:
- 응답 상태 코드는 200 OK
- 응답 시간은 3초 미만
- 응답 JSON에 다음 필드 포함:
  - `removed_cases`: ≥ 1
  - `merged_cases`: ≥ 1
  - `archived_cases`: ≥ 1
- 데이터베이스에 실제 변경 적용됨:
  - `low-perf-001`.status = 'archived'
  - `duplicate-001`.status = 'archived'
  - `inactive-001`.status = 'archived'

---

### Scenario 7: Consolidation Dry-Run API - 시뮬레이션 모드

**Given**:
- Scenario 6과 동일한 상태

**When**:
- POST /consolidation/dry-run 호출 (dry_run: true)

**Then**:
- 응답 상태 코드는 200 OK
- 응답 시간은 2초 미만
- 응답 JSON에 예상 변경사항 포함
- 데이터베이스에 변경 없음:
  - 모든 케이스의 status는 'active' 유지

---

### Scenario 8: Consolidation Summary API

**Given**:
- CaseBank에 다음과 같은 상태:
  - Active cases: 100
  - Archived cases: 20
  - Total cases: 120

**When**:
- GET /consolidation/summary 호출

**Then**:
- 응답 상태 코드는 200 OK
- 응답 JSON에 다음 필드 포함:
  - `total_cases`: 120
  - `active_cases`: 100
  - `archived_cases`: 20

---

### Scenario 9: Health Endpoints - 정상 상태

**Given**:
- 데이터베이스 연결이 정상
- Reflection 및 Consolidation 서비스가 실행 중

**When**:
- GET /reflection/health 호출
- GET /consolidation/health 호출

**Then**:
- 모든 응답 상태 코드는 200 OK
- 응답 시간은 100ms 미만
- 응답 JSON에 다음 필드 포함:
  - `status`: "healthy"
  - `database`: "connected"
  - `timestamp`: ISO 8601 형식

---

## Test Case Matrix

### Reflection API 테스트 매트릭스 (12개)

| Test ID | Endpoint | Scenario | Expected Status | Expected Response Time | Priority |
|---------|----------|----------|-----------------|------------------------|----------|
| REF-001 | POST /reflection/analyze | 정상 케이스 | 200 OK | < 1s | HIGH |
| REF-002 | POST /reflection/analyze | 존재하지 않는 case_id | 404 Not Found | < 1s | HIGH |
| REF-003 | POST /reflection/analyze | 인증 누락 | 401 Unauthorized | < 100ms | HIGH |
| REF-004 | POST /reflection/batch | 전체 케이스 분석 | 200 OK | < 10s | HIGH |
| REF-005 | POST /reflection/batch | 성능 SLA 검증 | 200 OK | P95 < 10s | HIGH |
| REF-006 | POST /reflection/batch | 인증 누락 | 401 Unauthorized | < 100ms | HIGH |
| REF-007 | POST /reflection/suggestions | 저성능 케이스 | 200 OK | < 2s | MEDIUM |
| REF-008 | POST /reflection/suggestions | 고성능 케이스 | 200 OK (빈 제안) | < 1s | MEDIUM |
| REF-009 | POST /reflection/suggestions | 인증 누락 | 401 Unauthorized | < 100ms | HIGH |
| REF-010 | GET /reflection/health | 정상 상태 | 200 OK | < 100ms | HIGH |
| REF-011 | GET /reflection/health | 응답 시간 검증 | 200 OK | P95 < 100ms | MEDIUM |
| REF-012 | GET /reflection/health | DB 연결 상태 | 200 OK | < 100ms | HIGH |

### Consolidation API 테스트 매트릭스 (12개)

| Test ID | Endpoint | Scenario | Expected Status | Expected Response Time | Priority |
|---------|----------|----------|-----------------|------------------------|----------|
| CON-001 | POST /consolidation/run | 실행 모드 | 200 OK | < 3s | HIGH |
| CON-002 | POST /consolidation/run | DB 변경 검증 | 200 OK | < 3s | HIGH |
| CON-003 | POST /consolidation/run | 인증 누락 | 401 Unauthorized | < 100ms | HIGH |
| CON-004 | POST /consolidation/dry-run | 시뮬레이션 모드 | 200 OK | < 2s | HIGH |
| CON-005 | POST /consolidation/dry-run | DB 변경 없음 검증 | 200 OK | < 2s | HIGH |
| CON-006 | POST /consolidation/dry-run | 인증 누락 | 401 Unauthorized | < 100ms | HIGH |
| CON-007 | GET /consolidation/summary | 통계 정보 | 200 OK | < 1s | MEDIUM |
| CON-008 | GET /consolidation/summary | 응답 스키마 검증 | 200 OK | < 1s | MEDIUM |
| CON-009 | GET /consolidation/summary | 인증 누락 | 401 Unauthorized | < 100ms | HIGH |
| CON-010 | GET /consolidation/health | 정상 상태 | 200 OK | < 100ms | HIGH |
| CON-011 | GET /consolidation/health | 응답 시간 검증 | 200 OK | P95 < 100ms | MEDIUM |
| CON-012 | GET /consolidation/health | DB 연결 상태 | 200 OK | < 100ms | HIGH |

---

## Definition of Done (완료 조건)

### Code Completeness (코드 완성도)

- [ ] 24개 통합 테스트 케이스 작성 완료
- [ ] `tests/integration/test_phase3_reflection.py` 구현 (12개 테스트)
- [ ] `tests/integration/test_phase3_consolidation.py` 구현 (12개 테스트)
- [ ] pytest fixture (`conftest.py`) 업데이트
- [ ] Docker PostgreSQL 테스트 환경 구성
- [ ] 트랜잭션 격리 메커니즘 구현

### Test Coverage (테스트 커버리지)

- [ ] Phase 3 API 라우터 커버리지 ≥ 95%
- [ ] `apps/api/routers/reflection.py`: ≥ 95%
- [ ] `apps/api/routers/consolidation.py`: ≥ 95%
- [ ] Branch coverage 포함
- [ ] 모든 주요 코드 경로 테스트됨

### Test Quality (테스트 품질)

- [ ] 모든 테스트가 독립적으로 실행 가능
- [ ] 테스트 간 상태 공유 없음 (트랜잭션 롤백 검증)
- [ ] 명확한 AAA 패턴 (Arrange-Act-Assert) 준수
- [ ] 에러 메시지가 명확하고 디버깅 가능
- [ ] 테스트 실행 시간 합리적 (< 2분)

### Performance (성능)

- [ ] POST /reflection/analyze: P95 < 1초
- [ ] POST /reflection/batch: P95 < 10초 (100 케이스)
- [ ] POST /consolidation/run: P95 < 3초
- [ ] POST /consolidation/dry-run: P95 < 2초
- [ ] GET /reflection/health: P95 < 100ms
- [ ] GET /consolidation/health: P95 < 100ms

### CI/CD Integration (CI/CD 통합)

- [ ] GitHub Actions에 Phase 3 테스트 추가
- [ ] Docker PostgreSQL 서비스 구성
- [ ] 모든 테스트가 CI에서 통과
- [ ] PR 생성 시 자동 테스트 실행
- [ ] 테스트 실패 시 PR 블로킹

### Documentation (문서화)

- [ ] 테스트 케이스별 주석 작성 (목적 명시)
- [ ] README.md에 Phase 3 테스트 섹션 추가
- [ ] 테스트 실행 방법 문서화 (`pytest tests/integration/test_phase3_*`)
- [ ] Docker 환경 설정 가이드 작성
- [ ] 트러블슈팅 가이드 추가

### Code Review (코드 리뷰)

- [ ] pytest best practices 준수
- [ ] 코드 중복 최소화 (fixture 재사용)
- [ ] 네이밍 컨벤션 일관성 유지
- [ ] 불필요한 주석 제거
- [ ] Type hints 추가 (Python 3.11+)

---

## Verification Checklist (검증 체크리스트)

### Pre-Acceptance Testing (수락 전 테스트)

1. **로컬 환경 테스트**
   - [ ] `pytest tests/integration/test_phase3_reflection.py -v` 통과
   - [ ] `pytest tests/integration/test_phase3_consolidation.py -v` 통과
   - [ ] 모든 테스트가 5초 이내에 완료

2. **Docker 환경 테스트**
   - [ ] `docker-compose -f docker-compose.test.yml up -d` 성공
   - [ ] PostgreSQL 컨테이너 정상 시작
   - [ ] 테스트 실행 후 자동 cleanup 확인

3. **커버리지 검증**
   - [ ] `pytest --cov=apps/api/routers/reflection --cov-report=term` ≥ 95%
   - [ ] `pytest --cov=apps/api/routers/consolidation --cov-report=term` ≥ 95%
   - [ ] 커버리지 리포트 HTML 생성

4. **성능 벤치마크**
   - [ ] `pytest --benchmark-only tests/integration/test_phase3_*` 실행
   - [ ] P95 latency 모든 엔드포인트 SLA 통과
   - [ ] 성능 회귀 없음

5. **CI/CD 파이프라인 검증**
   - [ ] GitHub Actions 워크플로우 실행 성공
   - [ ] Docker PostgreSQL 서비스 정상 동작
   - [ ] 테스트 결과 자동 리포트 생성

---

## Acceptance Criteria Summary (수락 기준 요약)

### Must Have (필수)
✅ 24개 통합 테스트 작성 완료
✅ Phase 3 API 커버리지 95% 이상
✅ 모든 테스트 통과 (100%)
✅ CI/CD 파이프라인 통합
✅ 성능 SLA 충족

### Should Have (권장)
✅ pytest-benchmark를 통한 성능 회귀 탐지
✅ 상세한 테스트 문서화
✅ Docker 환경 트러블슈팅 가이드

### Could Have (선택)
⭕ 부하 테스트 (SPEC-TEST-003에서 다룰 예정)
⭕ 보안 테스트 (SPEC-TEST-004에서 다룰 예정)
⭕ 테스트 리포트 시각화 대시보드

---

## Sign-off (승인)

### Stakeholders (이해관계자)
- **Product Owner**: Phase 3 기능 검증 완료
- **Tech Lead**: 코드 품질 및 아키텍처 승인
- **QA Engineer**: 테스트 커버리지 및 품질 승인
- **DevOps Engineer**: CI/CD 통합 승인

### Approval Checklist
- [ ] 모든 수락 기준 충족
- [ ] 문서화 완료
- [ ] CI/CD 통합 완료
- [ ] 코드 리뷰 완료

---

**Document Version**: 1.0
**Last Updated**: 2025-10-23
**Author**: @Alfred
