---
id: TEST-003
version: 0.1.0
status: completed
created: 2025-10-23
author: @Alfred
priority: medium
category: testing
labels: [performance, load-test, benchmark, optimization]
depends_on:
  - TEST-001
  - TEST-002
related_specs:
  - TEST-004
  - REFLECTION-001
  - CONSOLIDATION-001
scope:
  packages:
    - apps/api
    - apps/orchestration
  files:
    - apps/api/routers/*.py
  tests:
    - tests/performance/test_load_reflection.py
    - tests/performance/test_load_consolidation.py
    - tests/performance/test_database_optimization.py
---

# @SPEC:TEST-003 성능 및 부하 테스트

## HISTORY

### v0.1.0 (2025-10-23)
- **FEATURE**: Completed Phase 1-3 (Infrastructure + Baseline + Load Tests)
- Added pytest-benchmark, locust dependencies
- Created 4 baseline benchmarks (reflection analyze/batch, consolidation run/dry-run)
- Created 7 load tests (reflection 3 tests, consolidation 4 tests)
- Fixed test data isolation (DELETE+INSERT pattern)
- Fixed API response contracts (failed_executions, timezone, suggestions handling)
- Verified SLA targets: P95 32.80ms << 1000ms target (30x margin)

### v0.0.1 (2025-10-23)
- **INITIAL**: 성능 및 부하 테스트 SPEC 초안 작성
- **AUTHOR**: @Alfred
- **SCOPE**: Phase 3 API 성능 벤치마킹, 부하 테스트, 데이터베이스 쿼리 최적화 검증
- **CONTEXT**: TEST-002 완료 후 프로덕션 배포 전 성능 검증
- **BASELINE**: TEST-001 (기존 API 성능 기준), TEST-002 (Phase 3 API SLA)

## Environment (환경)

본 SPEC은 다음 환경에서 적용됩니다:

- **Load Testing Framework**: locust 또는 pytest-benchmark
- **Profiling Tools**: cProfile, py-spy, line_profiler
- **Database Profiling**: EXPLAIN ANALYZE, pg_stat_statements
- **Monitoring**: Prometheus + Grafana (선택 사항)
- **Test Environment**: Docker Compose (PostgreSQL + Redis + FastAPI)
- **Performance Targets**:
  - **Reflection**:
    - `/reflection/analyze`: P50 < 500ms, P95 < 1s, P99 < 2s
    - `/reflection/batch`: P50 < 5s, P95 < 10s, P99 < 15s (100 케이스)
  - **Consolidation**:
    - `/consolidation/run`: P50 < 1.5s, P95 < 3s, P99 < 5s
    - `/consolidation/dry-run`: P50 < 1s, P95 < 2s, P99 < 3s
  - **Database**:
    - Connection pool: 50 concurrent connections 지원
    - Query latency: P95 < 100ms

## Assumptions (전제 조건)

본 SPEC은 다음을 전제로 합니다:

1. TEST-002 완료 (기본 통합 테스트 통과)
2. Phase 3 API가 프로덕션 환경과 유사한 데이터셋으로 테스트 가능
3. 부하 테스트를 위한 충분한 시스템 리소스 확보
4. 데이터베이스 인덱스 및 쿼리 최적화 가능
5. 성능 회귀 탐지를 위한 베이스라인 메트릭 존재

## Requirements (요구사항)

### Ubiquitous Requirements (범용 요구사항)

**REQ-1**: The system shall benchmark all critical API endpoints
- 대상 엔드포인트:
  - Phase 3: `/reflection/analyze`, `/reflection/batch`, `/consolidation/run`, `/consolidation/dry-run`
  - Phase 1-2: `/classify`, `/search`, `/taxonomy/{version}/tree`
- P50, P95, P99 latency 측정
- 처리량(throughput) 측정 (requests per second)

**REQ-2**: The system shall perform load testing
- 동시 사용자 수: 10, 50, 100
- 테스트 시나리오:
  - Constant load: 일정한 요청률 유지
  - Ramp-up: 점진적 부하 증가
  - Spike test: 급격한 트래픽 증가
- 시스템 안정성 및 오류율 측정

**REQ-3**: The system shall verify database query optimization
- EXPLAIN ANALYZE를 통한 쿼리 플랜 분석
- 인덱스 사용 여부 확인
- N+1 쿼리 문제 탐지
- Connection pool 효율성 검증

**REQ-4**: The system shall detect performance regressions
- 베이스라인 대비 10% 이상 성능 저하 시 경고
- CI/CD 파이프라인에 성능 회귀 테스트 통합
- 성능 메트릭 자동 리포트 생성

### Event-driven Requirements (이벤트 기반 요구사항)

**REQ-5**: WHEN load testing with 10 concurrent users
- THEN all endpoints shall maintain P95 latency within SLA
- THEN error rate shall be < 0.1%
- THEN system shall remain stable for 5 minutes

**REQ-6**: WHEN load testing with 50 concurrent users
- THEN P95 latency shall increase by no more than 50%
- THEN error rate shall be < 1%
- THEN database connection pool shall not be exhausted

**REQ-7**: WHEN load testing with 100 concurrent users
- THEN P95 latency shall increase by no more than 100%
- THEN error rate shall be < 5%
- THEN system shall gracefully degrade (not crash)

**REQ-8**: WHEN spike testing (0 → 100 users in 10 seconds)
- THEN the system shall handle the spike without crashing
- THEN P99 latency shall recover to baseline within 30 seconds
- THEN no database deadlocks shall occur

**REQ-9**: WHEN profiling reflection batch operations
- THEN bottlenecks shall be identified and documented
- THEN LLM API calls shall be rate-limited correctly
- THEN database queries shall use indexes efficiently

**REQ-10**: WHEN profiling consolidation operations
- THEN vector similarity calculations shall be optimized
- THEN database transactions shall not block for > 1 second
- THEN archived cases shall be backed up asynchronously

### State-driven Requirements (상태 기반 요구사항)

**REQ-11**: WHILE the system is under heavy load
- Database connection pool shall not be exhausted
- Memory usage shall remain under 2GB per worker
- CPU usage shall remain under 80%

**REQ-12**: WHILE performance profiling is active
- The profiling overhead shall be < 5% of total execution time
- Profiling data shall be exported to JSON/CSV format
- Flame graphs shall be generated for CPU-bound operations

**REQ-13**: WHILE database query optimization is in progress
- EXPLAIN ANALYZE results shall be captured and analyzed
- Missing indexes shall be identified and documented
- Query plans shall be compared before/after optimization

### Optional Features (선택적 기능)

**REQ-14**: WHERE real-time monitoring is enabled
- The system may export metrics to Prometheus
- Grafana dashboards may be created for visualization
- Alerting rules may be configured for SLA violations

**REQ-15**: WHERE distributed load testing is required
- The system may use multiple load generators
- Load may be distributed across regions
- Realistic network latency may be simulated

### Constraints (제약사항)

**CON-1**: IF load testing exceeds 100 concurrent users
- THEN the test shall be conducted in a separate staging environment
- THEN production data shall not be used

**CON-2**: IF performance regression is detected
- THEN the CI/CD pipeline shall fail
- THEN a detailed performance report shall be generated
- THEN the PR shall be blocked until regression is fixed

**CON-3**: Performance test execution time shall be < 15 minutes
- Exclude long-running soak tests (run separately)
- Focus on critical path testing

**CON-4**: Database query profiling shall not impact production
- Use dedicated test database
- Disable profiling in production by default

## Specifications (상세 명세)

### Test Structure

```
tests/performance/
├── conftest.py                         # 공통 fixture 및 설정
├── test_load_reflection.py             # Reflection API 부하 테스트
├── test_load_consolidation.py          # Consolidation API 부하 테스트
├── test_database_optimization.py       # 데이터베이스 쿼리 최적화 검증
├── test_benchmark_baseline.py          # 베이스라인 벤치마크
└── locustfile.py                       # Locust 부하 테스트 시나리오

reports/
├── performance_baseline.json           # 베이스라인 메트릭
├── load_test_results.html              # Locust HTML 리포트
└── profiling/
    ├── reflection_batch_profile.txt    # cProfile 결과
    ├── consolidation_run_profile.txt
    └── flame_graphs/                   # py-spy flame graphs
```

### Load Testing Scenarios (Locust)

```python
# locustfile.py - Reflection API 부하 테스트
from locust import HttpUser, task, between

class ReflectionLoadTest(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def analyze_case(self):
        """단일 케이스 분석 (가중치 3)"""
        self.client.post(
            "/reflection/analyze",
            json={"case_id": "test-001"},
            headers={"X-API-Key": "test_api_key"}
        )

    @task(1)
    def batch_analyze(self):
        """배치 분석 (가중치 1)"""
        self.client.post(
            "/reflection/batch",
            headers={"X-API-Key": "test_api_key"}
        )

# 실행: locust -f locustfile.py --users 50 --spawn-rate 5 --run-time 5m
```

### pytest-benchmark 테스트

```python
# test_benchmark_baseline.py
import pytest

@pytest.mark.benchmark(group="reflection")
def test_reflection_analyze_benchmark(benchmark, api_client):
    """Reflection analyze 벤치마크"""
    result = benchmark(
        api_client.post,
        "/reflection/analyze",
        json={"case_id": "test-001"}
    )
    assert result.status_code == 200

@pytest.mark.benchmark(group="consolidation")
def test_consolidation_dry_run_benchmark(benchmark, api_client):
    """Consolidation dry-run 벤치마크"""
    result = benchmark(
        api_client.post,
        "/consolidation/dry-run"
    )
    assert result.status_code == 200
```

### Database Query Profiling

```python
# test_database_optimization.py
import pytest
from sqlalchemy import text

@pytest.mark.asyncio
async def test_case_bank_query_optimization(test_db):
    """CaseBank 쿼리 인덱스 사용 검증"""
    query = text("""
        EXPLAIN ANALYZE
        SELECT * FROM case_bank
        WHERE status = 'active' AND success_rate < 30
        ORDER BY usage_count DESC
        LIMIT 100;
    """)

    result = await test_db.execute(query)
    explain_plan = result.fetchall()

    # Index Scan 사용 여부 확인
    assert any("Index Scan" in str(row) for row in explain_plan)
    # Seq Scan 없음 확인
    assert not any("Seq Scan" in str(row) for row in explain_plan)
```

### Performance Metrics Collection

| Metric | Tool | Target | Measurement Method |
|--------|------|--------|--------------------|
| P50 Latency | pytest-benchmark | Phase별 SLA | `benchmark.stats.median` |
| P95 Latency | locust | Phase별 SLA | Locust HTML report |
| P99 Latency | locust | Phase별 SLA | Locust HTML report |
| Throughput (RPS) | locust | ≥ 100 RPS | Locust stats |
| Error Rate | locust | < 1% | Locust failures |
| Database Query Time | pg_stat_statements | P95 < 100ms | `SELECT * FROM pg_stat_statements` |
| Connection Pool Usage | psycopg2 | < 80% | `pool.size / pool.maxsize` |
| Memory Usage | psutil | < 2GB | `psutil.Process().memory_info().rss` |
| CPU Usage | psutil | < 80% | `psutil.cpu_percent(interval=1)` |

### Performance Regression Detection

```python
# conftest.py - 성능 회귀 탐지
import pytest
import json
from pathlib import Path

BASELINE_FILE = Path("reports/performance_baseline.json")

@pytest.fixture
def performance_baseline():
    """베이스라인 메트릭 로드"""
    if BASELINE_FILE.exists():
        with open(BASELINE_FILE) as f:
            return json.load(f)
    return {}

def pytest_benchmark_compare_failed(config, benchmarkgroup, benchmarks, compared):
    """벤치마크 회귀 탐지 후크"""
    for bench in benchmarks:
        if bench.stats.median > compared.get(bench.name, {}).get("median", 0) * 1.1:
            pytest.fail(f"Performance regression detected: {bench.name}")
```

## Traceability (추적성)

- **SPEC**: @SPEC:TEST-003
- **TEST**:
  - tests/performance/test_load_reflection.py
  - tests/performance/test_load_consolidation.py
  - tests/performance/test_database_optimization.py
  - locustfile.py
- **CODE**:
  - apps/api/routers/reflection.py
  - apps/api/routers/consolidation.py
  - apps/orchestration/src/reflection_engine.py
  - apps/orchestration/src/consolidation_policy.py
- **DOC**: README.md (Performance Testing section)
- **RELATED SPECS**:
  - @SPEC:TEST-001 (기존 API 성능 기준)
  - @SPEC:TEST-002 (Phase 3 API SLA)
  - @SPEC:REFLECTION-001 (Reflection Engine)
  - @SPEC:CONSOLIDATION-001 (Consolidation Policy)

## Success Criteria (성공 기준)

1. ✅ 모든 critical endpoints가 부하 테스트 통과 (10, 50, 100 users)
2. ✅ P95 latency가 SLA 내에 유지됨
3. ✅ 데이터베이스 쿼리 최적화 검증 완료 (인덱스 사용 확인)
4. ✅ 성능 회귀 탐지 시스템 구현 완료
5. ✅ 베이스라인 메트릭 수립 및 문서화
6. ✅ CI/CD 파이프라인에 성능 테스트 통합
7. ✅ 성능 병목점 식별 및 최적화 권장사항 제시

## References (참고 문서)

- Locust Documentation: https://locust.io/
- pytest-benchmark: https://pytest-benchmark.readthedocs.io/
- cProfile: https://docs.python.org/3/library/profile.html
- py-spy: https://github.com/benfred/py-spy
- PostgreSQL EXPLAIN: https://www.postgresql.org/docs/current/sql-explain.html
