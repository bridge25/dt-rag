# SPEC-TEST-002 Implementation Plan
# Phase 3 API 엔드포인트 통합 테스트

## Overview

본 계획서는 SPEC-TEST-002 (Phase 3 API 엔드포인트 통합 테스트)의 구현 계획을 정의합니다. Reflection 및 Consolidation 8개 신규 API 엔드포인트에 대한 24개 통합 테스트를 작성하여 95% 커버리지를 달성합니다.

---

## Work Breakdown Structure (작업 분해)

### Phase 1: 테스트 환경 구성 (Priority: HIGH)

#### Task 1.1: Docker PostgreSQL 테스트 환경 구축
- **Description**: 격리된 PostgreSQL 테스트 환경 구성
- **Deliverables**:
  - `docker-compose.test.yml` 작성
  - PostgreSQL test container 설정
  - 환경변수 및 설정 파일
- **Dependencies**: 없음
- **Estimated Effort**: 중간

#### Task 1.2: pytest 비동기 테스트 Fixture 작성
- **Description**: 공통 테스트 fixture 및 헬퍼 함수 구현
- **Deliverables**:
  - `conftest.py` 업데이트
  - `test_db` fixture (비동기 DB 세션)
  - `test_case_bank` fixture (테스트 데이터)
  - `api_client` fixture (비동기 HTTP 클라이언트)
- **Dependencies**: Task 1.1
- **Estimated Effort**: 중간

#### Task 1.3: 트랜잭션 격리 및 Cleanup 메커니즘
- **Description**: 테스트 독립성을 위한 트랜잭션 격리 구현
- **Deliverables**:
  - `@pytest.fixture(scope="function")` 트랜잭션 관리
  - 자동 rollback 메커니즘
  - Cleanup 헬퍼 함수
- **Dependencies**: Task 1.2
- **Estimated Effort**: 중간

---

### Phase 2: Reflection API 테스트 작성 (Priority: HIGH)

#### Task 2.1: POST /reflection/analyze 테스트 (3개)
- **Description**: 케이스 성능 분석 API 테스트
- **Test Cases**:
  - `test_analyze_valid_case`: 정상 케이스 분석
  - `test_analyze_invalid_case_id`: 존재하지 않는 case_id
  - `test_analyze_authentication_required`: 인증 누락
- **Dependencies**: Phase 1 완료
- **Estimated Effort**: 낮음

#### Task 2.2: POST /reflection/batch 테스트 (3개)
- **Description**: 배치 분석 API 테스트
- **Test Cases**:
  - `test_batch_analyze_all_cases`: 전체 케이스 분석
  - `test_batch_performance_under_10s`: 성능 SLA 검증
  - `test_batch_authentication_required`: 인증 누락
- **Dependencies**: Task 2.1
- **Estimated Effort**: 중간

#### Task 2.3: POST /reflection/suggestions 테스트 (3개)
- **Description**: 개선 제안 생성 API 테스트
- **Test Cases**:
  - `test_suggestions_low_performance_cases`: 저성능 케이스 제안
  - `test_suggestions_high_performance_cases`: 고성능 케이스 제안 없음
  - `test_suggestions_authentication_required`: 인증 누락
- **Dependencies**: Task 2.2
- **Estimated Effort**: 낮음

#### Task 2.4: GET /reflection/health 테스트 (3개)
- **Description**: Reflection 서비스 헬스체크 테스트
- **Test Cases**:
  - `test_reflection_health_ok`: 정상 상태 확인
  - `test_reflection_health_response_time`: 응답 시간 < 100ms
  - `test_reflection_health_database_status`: DB 연결 상태 확인
- **Dependencies**: Task 2.3
- **Estimated Effort**: 낮음

---

### Phase 3: Consolidation API 테스트 작성 (Priority: HIGH)

#### Task 3.1: POST /consolidation/run 테스트 (3개)
- **Description**: 실제 consolidation 실행 API 테스트
- **Test Cases**:
  - `test_consolidation_run_execute_mode`: 실제 실행 모드
  - `test_consolidation_run_database_changes`: DB 변경 검증
  - `test_consolidation_run_authentication_required`: 인증 누락
- **Dependencies**: Phase 2 완료
- **Estimated Effort**: 중간

#### Task 3.2: POST /consolidation/dry-run 테스트 (3개)
- **Description**: 시뮬레이션 모드 테스트
- **Test Cases**:
  - `test_consolidation_dry_run_no_changes`: DB 변경 없음 검증
  - `test_consolidation_dry_run_projections`: 예상 결과 반환
  - `test_consolidation_dry_run_authentication_required`: 인증 누락
- **Dependencies**: Task 3.1
- **Estimated Effort**: 낮음

#### Task 3.3: GET /consolidation/summary 테스트 (3개)
- **Description**: Consolidation 통계 API 테스트
- **Test Cases**:
  - `test_consolidation_summary_statistics`: 통계 정보 검증
  - `test_consolidation_summary_response_schema`: 응답 스키마 검증
  - `test_consolidation_summary_authentication_required`: 인증 누락
- **Dependencies**: Task 3.2
- **Estimated Effort**: 낮음

#### Task 3.4: GET /consolidation/health 테스트 (3개)
- **Description**: Consolidation 서비스 헬스체크 테스트
- **Test Cases**:
  - `test_consolidation_health_ok`: 정상 상태 확인
  - `test_consolidation_health_response_time`: 응답 시간 < 100ms
  - `test_consolidation_health_database_status`: DB 연결 상태 확인
- **Dependencies**: Task 3.3
- **Estimated Effort**: 낮음

---

### Phase 4: 성능 및 커버리지 검증 (Priority: MEDIUM)

#### Task 4.1: pytest-benchmark 성능 테스트
- **Description**: 각 엔드포인트의 성능 SLA 검증
- **Deliverables**:
  - 성능 테스트 케이스 추가
  - P95 latency 측정
  - 성능 회귀 탐지 메커니즘
- **Dependencies**: Phase 3 완료
- **Estimated Effort**: 중간

#### Task 4.2: 커버리지 측정 및 리포트
- **Description**: Phase 3 API 커버리지 95% 이상 달성 확인
- **Deliverables**:
  - `pytest-cov` 실행 및 리포트 생성
  - 커버리지 갭 분석
  - 누락된 테스트 케이스 추가
- **Dependencies**: Phase 3 완료
- **Estimated Effort**: 낮음

#### Task 4.3: CI/CD 파이프라인 통합
- **Description**: GitHub Actions에 Phase 3 테스트 통합
- **Deliverables**:
  - `.github/workflows/test.yml` 업데이트
  - Docker PostgreSQL 서비스 추가
  - 테스트 자동 실행 검증
- **Dependencies**: Phase 3 완료
- **Estimated Effort**: 중간

---

## Dependencies (의존성)

### 외부 의존성
- **SPEC-REFLECTION-001**: Reflection Engine 구현 완료
- **SPEC-CONSOLIDATION-001**: Memory Consolidation Policy 구현 완료
- **SPEC-TEST-001**: 기존 API 테스트 패턴 참조

### 내부 의존성
- **Phase 1 → Phase 2**: 테스트 환경 없이 Reflection 테스트 불가
- **Phase 2 → Phase 3**: Reflection 테스트 패턴을 Consolidation에 재사용
- **Phase 3 → Phase 4**: 모든 테스트 완료 후 성능 및 커버리지 검증

### 기술 의존성
- **pytest**: ^7.4.0
- **pytest-asyncio**: ^0.21.0
- **pytest-cov**: ^4.1.0
- **pytest-benchmark**: ^4.0.0
- **httpx**: ^0.24.0
- **docker-compose**: ^2.20.0

---

## Risk Assessment (위험 요소)

### Risk 1: Docker 환경 불안정
- **Probability**: Medium
- **Impact**: High
- **Mitigation**:
  - 로컬 및 CI 환경에서 Docker 테스트 사전 검증
  - Fallback: SQLite in-memory database 사용

### Risk 2: 비동기 테스트 복잡도
- **Probability**: Medium
- **Impact**: Medium
- **Mitigation**:
  - pytest-asyncio 공식 문서 참조
  - 기존 TEST-001 비동기 패턴 재사용

### Risk 3: 성능 SLA 미달성
- **Probability**: Low
- **Impact**: High
- **Mitigation**:
  - 성능 프로파일링 도구 사용 (cProfile, py-spy)
  - 데이터베이스 쿼리 최적화
  - 캐싱 전략 적용

### Risk 4: LLM API 호출 비용
- **Probability**: Low
- **Impact**: Medium
- **Mitigation**:
  - Mock LLM 응답 사용 (테스트 환경)
  - API 호출 횟수 최소화

---

## Resource Requirements (리소스 요구사항)

### 개발 리소스
- **Backend Developer**: 1명
- **Test Engineer**: 1명 (선택 사항)
- **DevOps Engineer**: 0.5명 (CI/CD 설정)

### 인프라 리소스
- **Docker**: PostgreSQL test container
- **CI/CD**: GitHub Actions runners
- **Test Database**: PostgreSQL 14+

### 시간 리소스
- **Phase 1**: 1-2일
- **Phase 2**: 1-2일
- **Phase 3**: 1-2일
- **Phase 4**: 1일
- **Total**: 4-7일

---

## Architecture Decisions (아키텍처 결정)

### Decision 1: Docker PostgreSQL vs SQLite
- **Choice**: Docker PostgreSQL
- **Rationale**:
  - 프로덕션 환경과 동일한 DB 엔진 사용
  - Vector 유사도 계산 (pgvector) 필요
  - 트랜잭션 격리 및 동시성 테스트 가능

### Decision 2: pytest-asyncio vs sync tests
- **Choice**: pytest-asyncio
- **Rationale**:
  - FastAPI 비동기 엔드포인트 직접 테스트
  - 실제 비동기 동작 검증
  - 성능 테스트의 정확성 향상

### Decision 3: 테스트 데이터 생성 전략
- **Choice**: pytest fixture + factory pattern
- **Rationale**:
  - 테스트 재사용성 향상
  - 데이터 일관성 보장
  - 유지보수 용이성

---

## Technical Approach (기술적 접근법)

### 테스트 구조
```python
tests/integration/
├── conftest.py                      # 공통 fixture
├── test_phase3_reflection.py        # Reflection API 테스트 (12개)
└── test_phase3_consolidation.py     # Consolidation API 테스트 (12개)
```

### Fixture 설계
```python
@pytest.fixture(scope="function")
async def test_db():
    """트랜잭션 격리된 테스트 DB"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        async with session.begin():
            yield session
            await session.rollback()

@pytest.fixture
async def api_client(test_db):
    """비동기 HTTP 클라이언트"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

### 테스트 패턴
```python
@pytest.mark.asyncio
async def test_analyze_valid_case(api_client, test_case_bank):
    response = await api_client.post(
        "/reflection/analyze",
        json={"case_id": "test-001"},
        headers={"X-API-Key": "test_api_key"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "success_rate" in data
    assert "total_executions" in data
    assert data["success_rate"] >= 0.0
```

---

## Success Metrics (성공 지표)

### 정량적 지표
- **테스트 케이스**: 24개 작성 완료
- **커버리지**: Phase 3 API 95% 이상
- **테스트 통과율**: 100%
- **성능 SLA**: 모든 엔드포인트 통과

### 정성적 지표
- **코드 품질**: pytest best practices 준수
- **유지보수성**: 명확한 테스트 구조 및 fixture 설계
- **문서화**: 테스트 의도 및 검증 항목 명확화

---

## Next Steps (다음 단계)

1. **Phase 1 시작**: Docker PostgreSQL 환경 구성
2. **SPEC-TEST-003 참조**: 성능 테스트 계획 수립
3. **SPEC-TEST-004 참조**: 보안 테스트 계획 수립
4. **CI/CD 검증**: 모든 테스트가 자동화 파이프라인에서 통과하는지 확인

---

**Document Version**: 1.0
**Last Updated**: 2025-10-23
**Author**: @Alfred
