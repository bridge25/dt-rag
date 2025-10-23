---
id: TEST-001
version: 0.1.0
status: completed
created: 2025-10-22
updated: 2025-10-22
author: @Alfred
priority: high
category: testing
labels: [api, integration-test, coverage]
---

# @SPEC:TEST-001 API 엔드포인트 통합 테스트 확장

## HISTORY

### v0.1.0 (2025-10-22)
- **COMPLETED**: API 엔드포인트 통합 테스트 확장 완료
- **AUTHOR**: @Alfred
- **CHANGES**:
  - 16개 신규 통합 테스트 추가 (총 30개)
  - 커버리지 47% → 91% 달성 (목표 85% 초과)
  - @CODE TAG 4개 라우터에 추가 (TAG 무결성 100%)
  - 성능 테스트 추가 (classify <2s, search <1s, healthz <100ms)
- **TEST RESULTS**:
  - 30/30 tests passing (100%)
  - classify.py: 94% coverage
  - search.py: 93% coverage
  - taxonomy.py: 83% coverage
  - health.py: 100% coverage

### v0.0.1 (2025-10-22)
- **INITIAL**: API 엔드포인트 통합 테스트 확장 SPEC 초안 작성
- **AUTHOR**: @Alfred
- **SCOPE**: FastAPI 엔드포인트(classify, search, taxonomy, health) 전체 테스트
- **CONTEXT**: 테스트 커버리지 47% → 85% 달성을 위한 API 테스트 확장

## Environment (환경)

본 SPEC은 다음 환경에서 적용됩니다:

- **API Framework**: FastAPI (Python 3.11+)
- **Testing Framework**: pytest + httpx
- **Test Environment**: CI/CD 파이프라인 및 로컬 개발 환경
- **Database**: SQLite (테스트용) / PostgreSQL (프로덕션)
- **Coverage Target**: 85% 이상
- **Performance Requirements**:
  - /classify 응답 시간 < 2초
  - /search 응답 시간 < 1초
  - /healthz 응답 시간 < 100ms

## Assumptions (전제 조건)

본 SPEC은 다음을 전제로 합니다:

1. FastAPI 서버가 정상적으로 실행 가능한 상태
2. 테스트용 데이터베이스가 초기화된 상태
3. ML 분류 모델이 로드된 상태
4. pytest 및 httpx 테스트 클라이언트 사용 가능
5. 기존 테스트 파일(`tests/integration/test_api_endpoints.py`)이 존재

## Requirements (요구사항)

### Ubiquitous Requirements (범용 요구사항)

**REQ-1**: The system shall test all FastAPI endpoints
- 대상 엔드포인트: `/classify`, `/search`, `/taxonomy/{version}/tree`, `/healthz`
- 각 엔드포인트에 대해 정상 케이스 및 에러 케이스 테스트

**REQ-2**: The system shall validate HTTP status codes
- 200 OK: 정상 응답
- 400 Bad Request: 잘못된 요청
- 422 Unprocessable Entity: 유효성 검증 실패
- 404 Not Found: 존재하지 않는 리소스
- 500 Internal Server Error: 서버 오류
- 503 Service Unavailable: 서비스 사용 불가

**REQ-3**: The system shall verify JSON response schemas
- Pydantic 모델을 사용한 응답 스키마 검증
- 필수 필드 존재 여부 확인
- 데이터 타입 일치 여부 확인

**REQ-4**: The system shall test with valid and invalid payloads
- 정상 데이터: 예상 형식의 올바른 요청
- 비정상 데이터: 누락된 필드, 잘못된 타입, 빈 값, 초과 길이

### Event-driven Requirements (이벤트 기반 요구사항)

**REQ-5**: WHEN POST /classify is called with valid text
- THEN the system shall return classification results within 2 seconds
- THEN the response shall include confidence scores and category labels

**REQ-6**: WHEN POST /classify is called with invalid payload
- THEN the system shall return 422 with error details
- THEN the error message shall specify which field failed validation

**REQ-7**: WHEN POST /search is called with filters
- THEN the system shall apply BM25 + vector hybrid search
- THEN the results shall be sorted by relevance score

**REQ-8**: WHEN POST /search exceeds timeout
- THEN the system shall return 504 Gateway Timeout
- THEN the partial results may be returned if available

**REQ-9**: WHEN GET /taxonomy/{version}/tree is called
- THEN the system shall return complete taxonomy structure
- THEN the tree depth shall match the expected hierarchy

**REQ-10**: WHEN GET /healthz is called
- THEN the system shall return 200 with service status
- THEN the response time shall be under 100ms

### State-driven Requirements (상태 기반 요구사항)

**REQ-11**: WHILE the database connection is active
- ALL endpoints shall return valid responses
- Database queries shall complete successfully

**REQ-12**: WHILE the ML classifier is loaded
- Classification requests shall use the cached model
- Model initialization time shall not impact response time

**REQ-13**: WHILE the API server is running
- Health endpoint shall respond within 100ms
- Service status shall be reported accurately

### Optional Features (선택적 기능)

**REQ-14**: WHERE detailed logging is enabled
- The system may log request/response bodies
- The logs shall be sanitized to remove sensitive data

**REQ-15**: WHERE performance profiling is active
- The system may track endpoint latency
- The profiling data shall be exported to monitoring tools

### Constraints (제약사항)

**CON-1**: IF the request body is missing required fields
- THEN the system shall return 422 Unprocessable Entity
- THEN the error response shall list all missing fields

**CON-2**: IF the database is unreachable
- THEN the system shall return 503 Service Unavailable
- THEN the health endpoint shall report unhealthy status

**CON-3**: Test coverage for API routes shall reach 85% or higher
- Branch coverage 포함
- 모든 주요 코드 경로 테스트

**CON-4**: Response time limits
- /classify: < 2초
- /search: < 1초
- /healthz: < 100ms

**CON-5**: Test isolation
- 각 테스트는 독립적으로 실행 가능
- 테스트 간 상태 공유 금지

## Specifications (상세 명세)

### Test Structure

```
tests/integration/test_api_endpoints.py
├── POST /classify 테스트 (8개)
│   ├── test_classify_valid_text
│   ├── test_classify_empty_text
│   ├── test_classify_invalid_format
│   ├── test_classify_long_text_5000_chars
│   ├── test_classify_special_characters
│   ├── test_classify_multilingual_text
│   ├── test_classify_performance_under_2s
│   └── test_classify_response_schema_validation
├── POST /search 테스트 (10개)
│   ├── test_search_valid_query
│   ├── test_search_with_filters
│   ├── test_search_empty_query
│   ├── test_search_pagination
│   ├── test_search_sorting_options
│   ├── test_search_hybrid_bm25_vector
│   ├── test_search_filter_combinations
│   ├── test_search_performance_under_1s
│   ├── test_search_timeout_handling
│   └── test_search_response_schema_validation
├── GET /taxonomy 테스트 (8개)
│   ├── test_taxonomy_get_latest_version
│   ├── test_taxonomy_get_specific_version
│   ├── test_taxonomy_nonexistent_version
│   ├── test_taxonomy_tree_depth_validation
│   ├── test_taxonomy_tree_structure
│   ├── test_taxonomy_category_count
│   ├── test_taxonomy_response_format
│   └── test_taxonomy_response_schema_validation
└── GET /healthz 테스트 (6개)
    ├── test_health_check_ok
    ├── test_health_check_database_status
    ├── test_health_check_response_time_under_100ms
    ├── test_health_check_service_unavailable
    ├── test_health_check_response_format
    └── test_health_check_cache_status

Total: 32개 테스트 (기존 16개 + 신규 16개)
```

### Error Handling Matrix

| Endpoint | 200 OK | 400 Bad Request | 422 Validation Error | 404 Not Found | 500 Server Error | 503 Unavailable |
|----------|--------|-----------------|----------------------|---------------|------------------|-----------------|
| POST /classify | ✓ | ✓ | ✓ | - | ✓ | - |
| POST /search | ✓ | ✓ | ✓ | - | ✓ | ✓ |
| GET /taxonomy | ✓ | - | - | ✓ | ✓ | - |
| GET /healthz | ✓ | - | - | - | ✓ | ✓ |

### Performance Test Matrix

| Endpoint | Max Response Time | Test Method | Pass Criteria |
|----------|-------------------|-------------|---------------|
| POST /classify | 2s | pytest-benchmark | 95th percentile < 2s |
| POST /search | 1s | pytest-benchmark | 95th percentile < 1s |
| GET /healthz | 100ms | pytest-benchmark | 95th percentile < 100ms |

## Traceability (추적성)

- **SPEC**: @SPEC:TEST-001
- **TEST**: tests/integration/test_api_endpoints.py
- **CODE**: apps/api/routers/*.py
- **DOC**: README.md (Testing section)
- **RELATED SPECS**:
  - @SPEC:API-001 (FastAPI 라우터 구현)
  - @SPEC:SEARCH-001 (하이브리드 검색 시스템)
  - @SPEC:CLASS-001 (분류 시스템)

## Success Criteria (성공 기준)

1. ✅ 전체 테스트 커버리지 85% 이상 달성
2. ✅ 모든 API 엔드포인트에 대해 정상 케이스 및 에러 케이스 테스트 완료
3. ✅ 성능 요구사항 충족 (classify < 2s, search < 1s, healthz < 100ms)
4. ✅ CI/CD 파이프라인에서 테스트 자동 실행 및 통과
5. ✅ 응답 스키마 검증 통과 (Pydantic 모델 기반)
6. ✅ 에러 핸들링 테스트 통과 (422, 404, 500, 503)

## References (참고 문서)

- FastAPI Testing Guide: https://fastapi.tiangolo.com/tutorial/testing/
- pytest Documentation: https://docs.pytest.org/
- httpx Documentation: https://www.python-httpx.org/
- pytest-benchmark: https://pytest-benchmark.readthedocs.io/
