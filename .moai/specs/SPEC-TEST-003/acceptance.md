# SPEC-TEST-003 Acceptance Criteria
# 성능 및 부하 테스트

## Overview

본 문서는 SPEC-TEST-003의 완료 조건을 정의합니다. Phase 3 API의 성능 벤치마킹, 부하 테스트, 데이터베이스 쿼리 최적화가 완료되고, 모든 성능 SLA가 충족되어야 합니다.

---

## Given-When-Then Scenarios

### Scenario 1: Reflection Analyze API - 베이스라인 벤치마크

**Given**:
- pytest-benchmark 환경이 구성되어 있음
- CaseBank에 100개의 테스트 케이스가 있음
- API 서버가 정상 실행 중

**When**:
- `pytest --benchmark-only tests/performance/test_benchmark_baseline.py::test_reflection_analyze_benchmark` 실행

**Then**:
- P50 latency < 500ms
- P95 latency < 1s
- P99 latency < 2s
- 벤치마크 결과가 `reports/performance_baseline.json`에 저장됨

---

### Scenario 2: Reflection Batch API - 부하 테스트 (10 users)

**Given**:
- Locust 부하 테스트 환경이 구성되어 있음
- CaseBank에 50개의 active 케이스가 있음
- 각 케이스에 100건 이상의 ExecutionLog 존재

**When**:
- `locust -f locustfile.py --users 10 --spawn-rate 2 --run-time 5m --headless` 실행

**Then**:
- P95 latency < 10s
- Error rate < 0.1%
- 총 요청 수 > 100
- HTML 리포트가 `reports/load_test_results.html`에 저장됨

---

### Scenario 3: Reflection Batch API - 부하 테스트 (50 users)

**Given**:
- Scenario 2와 동일한 상태

**When**:
- `locust -f locustfile.py --users 50 --spawn-rate 5 --run-time 5m --headless` 실행

**Then**:
- P95 latency < 15s (베이스라인 대비 50% 증가 허용)
- Error rate < 1%
- 데이터베이스 connection pool이 고갈되지 않음
- 시스템이 안정적으로 유지됨

---

### Scenario 4: Reflection Batch API - 부하 테스트 (100 users)

**Given**:
- Scenario 2와 동일한 상태

**When**:
- `locust -f locustfile.py --users 100 --spawn-rate 10 --run-time 5m --headless` 실행

**Then**:
- P95 latency < 20s (베이스라인 대비 100% 증가 허용)
- Error rate < 5%
- 시스템이 크래시되지 않음 (graceful degradation)
- 메모리 사용량 < 2GB per worker

---

### Scenario 5: Consolidation Run API - 부하 테스트 (50 users)

**Given**:
- CaseBank에 100개의 케이스가 있음 (다양한 success_rate 및 usage_count)
- Consolidation policy가 정상 실행 가능한 상태

**When**:
- `locust -f locustfile.py --users 50 --spawn-rate 5 --run-time 5m --headless` 실행 (consolidation 시나리오)

**Then**:
- P95 latency < 3s
- Error rate < 1%
- 데이터베이스 트랜잭션이 1초 이상 블로킹되지 않음
- Archived cases가 비동기로 백업됨

---

### Scenario 6: Spike Test - 급격한 트래픽 증가

**Given**:
- 시스템이 정상 실행 중 (현재 부하: 0)

**When**:
- Locust spike test: 0 → 100 users in 10 seconds

**Then**:
- 시스템이 크래시되지 않음
- P99 latency가 30초 이내에 베이스라인으로 복구됨
- 데이터베이스 deadlock 발생하지 않음
- Error rate < 10% (spike 동안)

---

### Scenario 7: Database Query Optimization - CaseBank 쿼리

**Given**:
- PostgreSQL에 `pg_stat_statements` 확장이 활성화되어 있음
- CaseBank에 10,000개의 레코드가 있음

**When**:
- `EXPLAIN ANALYZE SELECT * FROM case_bank WHERE status = 'active' AND success_rate < 30 ORDER BY usage_count DESC LIMIT 100;` 실행

**Then**:
- 쿼리 실행 시간 < 50ms
- Index Scan이 사용됨 (Seq Scan 없음)
- `idx_case_bank_status`, `idx_case_bank_success_rate` 인덱스가 사용됨
- Explain plan이 문서화됨

---

### Scenario 8: Database Query Optimization - ExecutionLog 쿼리

**Given**:
- ExecutionLog에 100,000개의 레코드가 있음

**When**:
- `EXPLAIN ANALYZE SELECT * FROM execution_log WHERE case_id = 'test-001' ORDER BY created_at DESC LIMIT 100;` 실행

**Then**:
- 쿼리 실행 시간 < 20ms
- Index Scan이 사용됨
- `idx_execution_log_case_id`, `idx_execution_log_created_at` 인덱스가 사용됨

---

### Scenario 9: Performance Profiling - Reflection Batch

**Given**:
- cProfile 및 py-spy가 설치되어 있음
- CaseBank에 100개의 케이스가 있음

**When**:
- `python -m cProfile -o reflection_batch_profile.txt apps/orchestration/src/reflection_engine.py` 실행
- `py-spy record -o reflection_batch_flame.svg -- python apps/orchestration/src/reflection_engine.py` 실행

**Then**:
- 병목점이 식별됨 (top 3 함수)
- Flame graph가 생성됨 (`reports/profiling/reflection_batch_flame.svg`)
- 최적화 권장사항이 문서화됨

---

### Scenario 10: Performance Regression Detection

**Given**:
- 베이스라인 메트릭이 `reports/performance_baseline.json`에 저장되어 있음
- 코드 변경으로 인해 성능이 12% 저하됨 (P95 latency: 1s → 1.12s)

**When**:
- `pytest --benchmark-only` 실행

**Then**:
- pytest-benchmark가 성능 회귀를 탐지함
- 테스트가 실패함 (회귀 임계값 10% 초과)
- 상세한 비교 리포트가 출력됨

---

## Test Case Matrix

### Performance Benchmarking (8개)

| Test ID | Endpoint | Metric | Target | Tool | Priority |
|---------|----------|--------|--------|------|----------|
| PERF-001 | POST /reflection/analyze | P50 | < 500ms | pytest-benchmark | HIGH |
| PERF-002 | POST /reflection/analyze | P95 | < 1s | pytest-benchmark | HIGH |
| PERF-003 | POST /reflection/batch | P50 | < 5s | pytest-benchmark | HIGH |
| PERF-004 | POST /reflection/batch | P95 | < 10s | pytest-benchmark | HIGH |
| PERF-005 | POST /consolidation/run | P50 | < 1.5s | pytest-benchmark | HIGH |
| PERF-006 | POST /consolidation/run | P95 | < 3s | pytest-benchmark | HIGH |
| PERF-007 | POST /consolidation/dry-run | P50 | < 1s | pytest-benchmark | MEDIUM |
| PERF-008 | POST /consolidation/dry-run | P95 | < 2s | pytest-benchmark | MEDIUM |

### Load Testing (12개)

| Test ID | Scenario | Users | Duration | Target P95 | Error Rate | Priority |
|---------|----------|-------|----------|------------|------------|----------|
| LOAD-001 | Reflection Analyze | 10 | 5m | < 1s | < 0.1% | HIGH |
| LOAD-002 | Reflection Analyze | 50 | 5m | < 1.5s | < 1% | HIGH |
| LOAD-003 | Reflection Analyze | 100 | 5m | < 2s | < 5% | MEDIUM |
| LOAD-004 | Reflection Batch | 10 | 10m | < 10s | < 0.1% | HIGH |
| LOAD-005 | Reflection Batch | 50 | 10m | < 15s | < 1% | HIGH |
| LOAD-006 | Reflection Batch | 100 | 10m | < 20s | < 5% | MEDIUM |
| LOAD-007 | Consolidation Run | 10 | 5m | < 3s | < 0.1% | HIGH |
| LOAD-008 | Consolidation Run | 50 | 5m | < 4.5s | < 1% | MEDIUM |
| LOAD-009 | Consolidation Dry-Run | 10 | 5m | < 2s | < 0.1% | MEDIUM |
| LOAD-010 | Consolidation Dry-Run | 50 | 5m | < 3s | < 1% | MEDIUM |
| LOAD-011 | Spike Test (All APIs) | 0→100 | 10s | P99 recovery < 30s | < 10% | HIGH |
| LOAD-012 | Soak Test (All APIs) | 50 | 1h | No degradation | < 0.5% | LOW |

### Database Query Optimization (6개)

| Test ID | Query Type | Table | Target Latency | Index Usage | Priority |
|---------|------------|-------|----------------|-------------|----------|
| DB-001 | SELECT (filtered) | case_bank | < 50ms | Index Scan | HIGH |
| DB-002 | SELECT (ordered) | case_bank | < 50ms | Index Scan | HIGH |
| DB-003 | SELECT (aggregated) | case_bank | < 100ms | Index Scan | MEDIUM |
| DB-004 | SELECT (filtered) | execution_log | < 20ms | Index Scan | HIGH |
| DB-005 | SELECT (aggregated) | execution_log | < 100ms | Index Scan | MEDIUM |
| DB-006 | Vector Similarity | case_bank | < 200ms | pgvector Index | HIGH |

---

## Definition of Done (완료 조건)

### Performance Benchmarking (성능 벤치마킹)

- [ ] 8개 베이스라인 벤치마크 테스트 작성 완료
- [ ] 모든 엔드포인트의 P50, P95, P99 측정 완료
- [ ] `reports/performance_baseline.json` 생성 완료
- [ ] README.md에 베이스라인 섹션 추가

### Load Testing (부하 테스트)

- [ ] 12개 부하 테스트 시나리오 작성 완료
- [ ] Locust `locustfile.py` 구현 완료
- [ ] 10, 50, 100 users 부하 테스트 통과
- [ ] Spike test 통과 (시스템 안정성 검증)
- [ ] HTML 리포트 자동 생성 (`reports/load_test_results.html`)

### Database Query Optimization (데이터베이스 쿼리 최적화)

- [ ] 6개 쿼리 프로파일링 테스트 작성 완료
- [ ] 모든 쿼리가 Index Scan 사용 확인
- [ ] 누락된 인덱스 식별 및 문서화
- [ ] Before/After 성능 비교 리포트 작성
- [ ] 인덱스 최적화 SQL 스크립트 작성

### Performance Profiling (성능 프로파일링)

- [ ] cProfile 프로파일링 실행 및 결과 저장
- [ ] py-spy flame graph 생성 (`reports/profiling/*.svg`)
- [ ] 병목점 top 3 식별 및 문서화
- [ ] 최적화 권장사항 작성 (구체적이고 실행 가능)

### Performance Regression Detection (성능 회귀 탐지)

- [ ] `pytest_benchmark_compare_failed` 후크 구현
- [ ] 회귀 임계값 설정 (10% 저하 시 실패)
- [ ] CI/CD 파이프라인에 통합
- [ ] 성능 회귀 시 자동 실패 검증

### CI/CD Integration (CI/CD 통합)

- [ ] GitHub Actions에 성능 테스트 워크플로우 추가
- [ ] 간소화된 부하 테스트 (1분) CI에서 실행
- [ ] 전체 부하 테스트 (10분) 주간 배치로 실행
- [ ] 성능 리포트 자동 저장 (artifacts)

### Documentation (문서화)

- [ ] 성능 테스트 실행 가이드 작성
- [ ] 병목점 분석 리포트 작성
- [ ] 최적화 권장사항 문서화
- [ ] 트러블슈팅 가이드 추가

---

## Verification Checklist (검증 체크리스트)

### Pre-Acceptance Testing (수락 전 테스트)

1. **로컬 성능 벤치마크**
   - [ ] `pytest --benchmark-only tests/performance/` 통과
   - [ ] 모든 P95 latency가 SLA 내에 있음
   - [ ] 베이스라인 메트릭 파일 생성 확인

2. **로컬 부하 테스트**
   - [ ] `locust -f locustfile.py --users 10 --run-time 1m --headless` 통과
   - [ ] Error rate < 0.1%
   - [ ] HTML 리포트 생성 확인

3. **데이터베이스 쿼리 프로파일링**
   - [ ] `pytest tests/performance/test_database_optimization.py -v` 통과
   - [ ] 모든 쿼리가 Index Scan 사용
   - [ ] EXPLAIN ANALYZE 결과 저장 확인

4. **성능 회귀 탐지**
   - [ ] 베이스라인 대비 15% 성능 저하 시 테스트 실패 검증
   - [ ] 회귀 탐지 후크 동작 확인

5. **CI/CD 파이프라인 검증**
   - [ ] GitHub Actions 워크플로우 실행 성공
   - [ ] 성능 테스트 자동 실행
   - [ ] 리포트 자동 저장 확인

---

## Performance SLA Summary (성능 SLA 요약)

### Critical Endpoints (HIGH Priority)

| Endpoint | P50 | P95 | P99 | Load (50 users) Error Rate |
|----------|-----|-----|-----|----------------------------|
| POST /reflection/analyze | < 500ms | < 1s | < 2s | < 1% |
| POST /reflection/batch | < 5s | < 10s | < 15s | < 1% |
| POST /consolidation/run | < 1.5s | < 3s | < 5s | < 1% |

### Important Endpoints (MEDIUM Priority)

| Endpoint | P50 | P95 | P99 | Load (50 users) Error Rate |
|----------|-----|-----|-----|----------------------------|
| POST /consolidation/dry-run | < 1s | < 2s | < 3s | < 1% |
| GET /reflection/health | < 50ms | < 100ms | < 200ms | < 0.1% |
| GET /consolidation/health | < 50ms | < 100ms | < 200ms | < 0.1% |

### Database Queries

| Query Type | Target Latency (P95) | Index Required |
|------------|----------------------|----------------|
| CaseBank filtered SELECT | < 50ms | Yes |
| ExecutionLog filtered SELECT | < 20ms | Yes |
| Vector similarity | < 200ms | pgvector Index |

---

## Acceptance Criteria Summary (수락 기준 요약)

### Must Have (필수)
✅ 모든 베이스라인 벤치마크 측정 완료
✅ 10, 50 users 부하 테스트 통과
✅ 데이터베이스 쿼리 인덱스 사용 검증
✅ 성능 회귀 탐지 시스템 구현
✅ CI/CD 통합 완료

### Should Have (권장)
✅ 100 users 부하 테스트 통과
✅ Spike test 통과
✅ 성능 프로파일링 및 병목점 식별
✅ 최적화 권장사항 문서화

### Could Have (선택)
⭕ Soak test (1시간 부하 테스트)
⭕ Prometheus + Grafana 대시보드
⭕ 분산 부하 테스트 (multi-region)

---

## Sign-off (승인)

### Stakeholders (이해관계자)
- **Product Owner**: 성능 SLA 충족 확인
- **Tech Lead**: 병목점 분석 및 최적화 승인
- **Performance Engineer**: 부하 테스트 결과 승인
- **DevOps Engineer**: CI/CD 통합 승인

### Approval Checklist
- [ ] 모든 수락 기준 충족
- [ ] 성능 SLA 달성
- [ ] 문서화 완료
- [ ] CI/CD 통합 완료

---

**Document Version**: 1.0
**Last Updated**: 2025-10-23
**Author**: @Alfred
