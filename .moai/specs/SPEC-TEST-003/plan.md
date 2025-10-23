# SPEC-TEST-003 Implementation Plan
# 성능 및 부하 테스트

## Overview

본 계획서는 SPEC-TEST-003 (성능 및 부하 테스트)의 구현 계획을 정의합니다. Phase 3 API의 성능 벤치마킹, 부하 테스트, 데이터베이스 쿼리 최적화 검증을 수행하여 프로덕션 배포 준비를 완료합니다.

---

## Work Breakdown Structure (작업 분해)

### Phase 1: 성능 테스트 환경 구성 (Priority: HIGH)

#### Task 1.1: pytest-benchmark 설정
- **Description**: 베이스라인 성능 벤치마킹 환경 구성
- **Deliverables**:
  - `pytest-benchmark` 설치 및 설정
  - `conftest.py`에 벤치마크 fixture 추가
  - 베이스라인 메트릭 저장 경로 설정 (`reports/performance_baseline.json`)
- **Dependencies**: 없음
- **Estimated Effort**: 낮음

#### Task 1.2: Locust 부하 테스트 환경 구축
- **Description**: 분산 부하 테스트 프레임워크 설정
- **Deliverables**:
  - `locust` 설치
  - `locustfile.py` 작성 (기본 시나리오)
  - Docker Compose에 Locust 서비스 추가 (선택 사항)
- **Dependencies**: Task 1.1
- **Estimated Effort**: 중간

#### Task 1.3: 데이터베이스 프로파일링 설정
- **Description**: PostgreSQL 쿼리 프로파일링 활성화
- **Deliverables**:
  - `pg_stat_statements` 확장 활성화
  - EXPLAIN ANALYZE 헬퍼 함수 작성
  - 쿼리 통계 수집 스크립트
- **Dependencies**: 없음
- **Estimated Effort**: 낮음

---

### Phase 2: 베이스라인 벤치마크 수립 (Priority: HIGH)

#### Task 2.1: Phase 1-2 API 베이스라인 측정
- **Description**: 기존 API의 성능 베이스라인 수립
- **Test Cases**:
  - POST /classify: P50, P95, P99 측정
  - POST /search: P50, P95, P99 측정
  - GET /taxonomy/{version}/tree: P50, P95, P99 측정
- **Dependencies**: Phase 1 완료
- **Estimated Effort**: 낮음

#### Task 2.2: Phase 3 API 베이스라인 측정
- **Description**: Phase 3 API의 성능 베이스라인 수립
- **Test Cases**:
  - POST /reflection/analyze: P50, P95, P99 측정
  - POST /reflection/batch: P50, P95, P99 측정
  - POST /consolidation/run: P50, P95, P99 측정
  - POST /consolidation/dry-run: P50, P95, P99 측정
- **Dependencies**: Task 2.1
- **Estimated Effort**: 중간

#### Task 2.3: 베이스라인 메트릭 문서화
- **Description**: 베이스라인 메트릭 JSON 파일 생성 및 문서화
- **Deliverables**:
  - `reports/performance_baseline.json` 생성
  - README.md에 베이스라인 섹션 추가
  - SLA 임계값 정의 문서화
- **Dependencies**: Task 2.2
- **Estimated Effort**: 낮음

---

### Phase 3: Reflection API 부하 테스트 (Priority: HIGH)

#### Task 3.1: POST /reflection/analyze 부하 테스트
- **Description**: 단일 케이스 분석 API 부하 테스트
- **Test Scenarios**:
  - 10 concurrent users (5분)
  - 50 concurrent users (5분)
  - 100 concurrent users (5분)
- **Dependencies**: Phase 2 완료
- **Estimated Effort**: 중간

#### Task 3.2: POST /reflection/batch 부하 테스트
- **Description**: 배치 분석 API 부하 테스트
- **Test Scenarios**:
  - 10 concurrent users (10분)
  - 50 concurrent users (10분)
  - Spike test (0 → 100 users in 10s)
- **Dependencies**: Task 3.1
- **Estimated Effort**: 중간

#### Task 3.3: Reflection API 성능 프로파일링
- **Description**: 병목점 식별 및 최적화 권장사항 제시
- **Deliverables**:
  - cProfile 실행 및 결과 저장
  - py-spy flame graph 생성
  - 병목점 분석 리포트 작성
- **Dependencies**: Task 3.2
- **Estimated Effort**: 중간

---

### Phase 4: Consolidation API 부하 테스트 (Priority: MEDIUM)

#### Task 4.1: POST /consolidation/run 부하 테스트
- **Description**: 실제 consolidation 실행 부하 테스트
- **Test Scenarios**:
  - 10 concurrent users (5분)
  - 50 concurrent users (5분)
- **Dependencies**: Phase 3 완료
- **Estimated Effort**: 중간

#### Task 4.2: POST /consolidation/dry-run 부하 테스트
- **Description**: 시뮬레이션 모드 부하 테스트
- **Test Scenarios**:
  - 10 concurrent users (5분)
  - 50 concurrent users (5분)
  - 100 concurrent users (5분)
- **Dependencies**: Task 4.1
- **Estimated Effort**: 중간

#### Task 4.3: Consolidation API 성능 프로파일링
- **Description**: Vector 유사도 계산 최적화 검증
- **Deliverables**:
  - Vector 유사도 계산 프로파일링
  - 데이터베이스 트랜잭션 분석
  - 최적화 권장사항 문서화
- **Dependencies**: Task 4.2
- **Estimated Effort**: 중간

---

### Phase 5: 데이터베이스 쿼리 최적화 검증 (Priority: MEDIUM)

#### Task 5.1: CaseBank 쿼리 프로파일링
- **Description**: CaseBank 관련 쿼리 성능 분석
- **Test Cases**:
  - `SELECT * FROM case_bank WHERE status = 'active'` (EXPLAIN ANALYZE)
  - `SELECT * FROM case_bank WHERE success_rate < 30` (EXPLAIN ANALYZE)
  - `SELECT * FROM case_bank ORDER BY usage_count DESC LIMIT 100` (EXPLAIN ANALYZE)
- **Dependencies**: Phase 4 완료
- **Estimated Effort**: 낮음

#### Task 5.2: ExecutionLog 쿼리 프로파일링
- **Description**: ExecutionLog 관련 쿼리 성능 분석
- **Test Cases**:
  - `SELECT * FROM execution_log WHERE case_id = 'test-001'` (EXPLAIN ANALYZE)
  - `SELECT case_id, COUNT(*) FROM execution_log GROUP BY case_id` (EXPLAIN ANALYZE)
- **Dependencies**: Task 5.1
- **Estimated Effort**: 낮음

#### Task 5.3: 인덱스 최적화 권장사항
- **Description**: 누락된 인덱스 식별 및 추가 권장
- **Deliverables**:
  - 인덱스 최적화 스크립트 (SQL)
  - Before/After 성능 비교 리포트
  - Migration 가이드 작성
- **Dependencies**: Task 5.2
- **Estimated Effort**: 중간

---

### Phase 6: 성능 회귀 탐지 시스템 (Priority: LOW)

#### Task 6.1: pytest-benchmark 회귀 탐지 구현
- **Description**: 베이스라인 대비 성능 회귀 자동 탐지
- **Deliverables**:
  - `pytest_benchmark_compare_failed` 후크 구현
  - 회귀 임계값 설정 (10% 저하 시 실패)
  - CI/CD 파이프라인에 통합
- **Dependencies**: Phase 5 완료
- **Estimated Effort**: 중간

#### Task 6.2: Locust 결과 자동 리포트 생성
- **Description**: Locust HTML 리포트 자동 생성 및 저장
- **Deliverables**:
  - `locust --html` 자동 실행 스크립트
  - `reports/load_test_results.html` 저장
  - CI/CD 아티팩트로 저장
- **Dependencies**: Task 6.1
- **Estimated Effort**: 낮음

#### Task 6.3: 성능 메트릭 시각화 (선택 사항)
- **Description**: Grafana 대시보드 생성 (선택 사항)
- **Deliverables**:
  - Prometheus exporter 추가
  - Grafana 대시보드 JSON 작성
  - 실시간 모니터링 설정
- **Dependencies**: Task 6.2
- **Estimated Effort**: 높음 (선택 사항)

---

## Dependencies (의존성)

### 외부 의존성
- **SPEC-TEST-001**: 기존 API 성능 기준
- **SPEC-TEST-002**: Phase 3 API SLA 정의
- **SPEC-REFLECTION-001**: Reflection Engine 구현
- **SPEC-CONSOLIDATION-001**: Consolidation Policy 구현

### 내부 의존성
- **Phase 1 → Phase 2**: 테스트 환경 없이 벤치마크 불가
- **Phase 2 → Phase 3**: 베이스라인 없이 부하 테스트 무의미
- **Phase 3 → Phase 4**: Reflection 패턴을 Consolidation에 재사용
- **Phase 5 독립**: 데이터베이스 프로파일링은 병렬 수행 가능

### 기술 의존성
- **pytest-benchmark**: ^4.0.0
- **locust**: ^2.15.0
- **cProfile**: stdlib (Python 내장)
- **py-spy**: ^0.3.14
- **psutil**: ^5.9.0
- **pg_stat_statements**: PostgreSQL 확장

---

## Risk Assessment (위험 요소)

### Risk 1: 부하 테스트 중 시스템 불안정
- **Probability**: Medium
- **Impact**: High
- **Mitigation**:
  - 전용 테스트 환경에서 수행
  - 점진적 부하 증가 (ramp-up)
  - 시스템 리소스 모니터링

### Risk 2: 성능 SLA 미달성
- **Probability**: Medium
- **Impact**: High
- **Mitigation**:
  - 사전 프로파일링으로 병목점 식별
  - 데이터베이스 쿼리 최적화
  - 캐싱 전략 적용 (Redis)

### Risk 3: 데이터베이스 쿼리 최적화 어려움
- **Probability**: Low
- **Impact**: Medium
- **Mitigation**:
  - PostgreSQL 전문가 컨설팅
  - 인덱스 최적화 도구 사용 (pg_indexadvisor)

### Risk 4: 부하 테스트 실행 시간 초과
- **Probability**: Medium
- **Impact**: Low
- **Mitigation**:
  - CI/CD에서는 간소화된 부하 테스트 실행 (1분)
  - 주간 배치로 전체 부하 테스트 수행

---

## Resource Requirements (리소스 요구사항)

### 개발 리소스
- **Performance Engineer**: 1명
- **Backend Developer**: 0.5명 (최적화 지원)
- **DevOps Engineer**: 0.5명 (인프라 설정)

### 인프라 리소스
- **Load Testing Server**: 4 vCPU, 8GB RAM
- **Database Server**: 8 vCPU, 16GB RAM, SSD
- **Monitoring**: Prometheus + Grafana (선택 사항)

### 시간 리소스
- **Phase 1**: 1일
- **Phase 2**: 1일
- **Phase 3**: 2일
- **Phase 4**: 2일
- **Phase 5**: 1-2일
- **Phase 6**: 1-2일
- **Total**: 8-10일

---

## Architecture Decisions (아키텍처 결정)

### Decision 1: Locust vs JMeter
- **Choice**: Locust
- **Rationale**:
  - Python 기반, FastAPI와 동일 언어
  - 스크립트 작성 용이성
  - 분산 부하 테스트 지원

### Decision 2: pytest-benchmark vs custom solution
- **Choice**: pytest-benchmark
- **Rationale**:
  - pytest 통합
  - 자동 통계 계산 (P50, P95, P99)
  - 회귀 탐지 기능 내장

### Decision 3: cProfile vs py-spy
- **Choice**: 둘 다 사용
- **Rationale**:
  - cProfile: 함수 단위 프로파일링
  - py-spy: 프로덕션 환경 프로파일링 (오버헤드 낮음)
  - Flame graph 생성

---

## Technical Approach (기술적 접근법)

### Locust 시나리오 설계
```python
class ReflectionLoadTest(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def analyze_case(self):
        """단일 케이스 분석 (가중치 3)"""
        self.client.post("/reflection/analyze", ...)

    @task(1)
    def batch_analyze(self):
        """배치 분석 (가중치 1)"""
        self.client.post("/reflection/batch", ...)
```

### pytest-benchmark 사용법
```python
@pytest.mark.benchmark(group="reflection")
def test_reflection_analyze_benchmark(benchmark, api_client):
    result = benchmark(
        api_client.post,
        "/reflection/analyze",
        json={"case_id": "test-001"}
    )
    assert result.status_code == 200
```

### EXPLAIN ANALYZE 사용법
```python
query = text("""
    EXPLAIN ANALYZE
    SELECT * FROM case_bank
    WHERE status = 'active' AND success_rate < 30
    ORDER BY usage_count DESC
    LIMIT 100;
""")
result = await test_db.execute(query)
```

---

## Success Metrics (성공 지표)

### 정량적 지표
- **부하 테스트**: 10, 50, 100 users 통과
- **P95 Latency**: 모든 엔드포인트 SLA 충족
- **Error Rate**: < 1% (50 users 기준)
- **Database Query**: P95 < 100ms

### 정성적 지표
- **병목점 식별**: 최소 3개 이상 식별 및 문서화
- **최적화 권장사항**: 구체적이고 실행 가능한 권장사항 제시
- **성능 회귀 탐지**: 자동화된 회귀 탐지 시스템 구축

---

## Next Steps (다음 단계)

1. **Phase 1 시작**: pytest-benchmark 및 Locust 설정
2. **SPEC-TEST-004 참조**: 보안 테스트와 연계 계획
3. **프로덕션 배포 준비**: 모든 성능 테스트 통과 후 배포 승인

---

**Document Version**: 1.0
**Last Updated**: 2025-10-23
**Author**: @Alfred
